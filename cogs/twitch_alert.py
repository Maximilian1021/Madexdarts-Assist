import discord
from discord.ext import commands, tasks
import aiohttp
import os

# ──────────────────────────────────────────────
#  CONFIG – wird aus bot.env geladen
# ──────────────────────────────────────────────
TWITCH_CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_USERNAME      = os.getenv("TWITCH_USERNAME", "madexdarts")
ALERT_CHANNEL_ID     = int(os.getenv("ALERT_CHANNEL_ID", "0"))
CHECK_INTERVAL       = int(os.getenv("TWITCH_CHECK_INTERVAL", "60"))
# ──────────────────────────────────────────────


class TwitchAlert(commands.Cog):
    """Sendet einen @everyone Alert, sobald ein Twitch-Kanal live geht."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.was_live = False          # Zustand aus dem letzten Check
        self.access_token: str | None = None
        self.check_stream.start()

    def cog_unload(self):
        self.check_stream.cancel()

    # ------------------------------------------------------------------
    # Twitch-OAuth: App Access Token holen
    # ------------------------------------------------------------------
    async def get_access_token(self) -> str:
        url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id":     TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type":    "client_credentials",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as resp:
                data = await resp.json()
                return data["access_token"]

    # ------------------------------------------------------------------
    # Twitch-API: Stream-Status abfragen
    # ------------------------------------------------------------------
    async def is_live(self) -> tuple[bool, dict | None]:
        if not self.access_token:
            self.access_token = await self.get_access_token()

        headers = {
            "Client-ID":     TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {self.access_token}",
        }
        url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                # Token abgelaufen → neu holen und nochmal
                if resp.status == 401:
                    self.access_token = await self.get_access_token()
                    return await self.is_live()

                data = await resp.json()
                streams = data.get("data", [])
                if streams:
                    return True, streams[0]
                return False, None

    # ------------------------------------------------------------------
    # Loop: alle CHECK_INTERVAL Sekunden prüfen
    # ------------------------------------------------------------------
    @tasks.loop(seconds=CHECK_INTERVAL)
    async def check_stream(self):
        try:
            live, stream_info = await self.is_live()

            # Nur feuern wenn Kanal gerade LIVE GEGANGEN ist (war vorher offline)
            if live and not self.was_live:
                channel = self.bot.get_channel(ALERT_CHANNEL_ID)
                if channel:
                    await self.send_alert(channel, stream_info)

            self.was_live = live

        except Exception as e:
            print(f"[TwitchAlert] Fehler beim Check: {e}")

    @check_stream.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------
    # Alert-Nachricht bauen und senden
    # ------------------------------------------------------------------
    async def send_alert(self, channel: discord.TextChannel, info: dict):
        title    = info.get("title", "–")
        game     = info.get("game_name", "–")
        viewers  = info.get("viewer_count", 0)
        thumb    = info.get("thumbnail_url", "").replace("{width}", "1280").replace("{height}", "720")
        url      = f"https://www.twitch.tv/{TWITCH_USERNAME}"

        embed = discord.Embed(
            title       = f"🔴 {TWITCH_USERNAME} ist jetzt LIVE!",
            description = f"**{title}**\n\nSpielt: **{game}**\n👥 {viewers} Zuschauer",
            color       = discord.Color.purple(),
            url         = url,
        )
        embed.set_image(url=thumb)
        embed.set_footer(text="Twitch Live Alert")

        await channel.send(content=f"@everyone **{TWITCH_USERNAME}** ist live! 🎯\n{url}", embed=embed)


# ──────────────────────────────────────────────
#  Setup-Funktion (wird von bot.load_extension aufgerufen)
# ──────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(TwitchAlert(bot))
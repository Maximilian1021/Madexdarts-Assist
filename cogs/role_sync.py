import discord
from discord.ext import commands, tasks
import os

# ──────────────────────────────────────────────
#  CONFIG – wird aus bot.env geladen
# ──────────────────────────────────────────────
SUBS_ROLE_ID       = int(os.getenv("SUBS_ROLE_ID", "0"))
SYNC_INTERVAL_MIN  = int(os.getenv("ROLE_SYNC_INTERVAL_MIN", "10"))

_raw = os.getenv("TWITCH_SUB_ROLE_IDS", "")
TWITCH_SUB_ROLE_IDS: set[int] = {int(r.strip()) for r in _raw.split(",") if r.strip()}
# ──────────────────────────────────────────────


class RoleSync(commands.Cog):
    """Synchronisiert Twitch-Subscriber-Rollen mit der Discord ⭐ Subs Rolle.

    Läuft auf zwei Arten:
      • Echtzeit  – on_member_update (sofort bei jeder Rollenänderung)
      • Periodisch – sync_all_members Loop (alle ROLE_SYNC_INTERVAL_MIN Minuten)
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sync_all_members.start()

    def cog_unload(self):
        self.sync_all_members.cancel()

    # ------------------------------------------------------------------
    # Hilfsmethode: einen einzelnen Member prüfen & ggf. Rolle anpassen
    # ------------------------------------------------------------------
    async def _sync_member(self, member: discord.Member) -> None:
        subs_role = member.guild.get_role(SUBS_ROLE_ID)
        if not subs_role:
            return

        has_twitch_sub = any(r.id in TWITCH_SUB_ROLE_IDS for r in member.roles)
        has_subs_role  = subs_role in member.roles

        try:
            if has_twitch_sub and not has_subs_role:
                await member.add_roles(subs_role, reason="RoleSync: Twitch Subscriber erkannt")
                print(f"[RoleSync] ✅ {member} → ⭐ Subs vergeben")
            elif not has_twitch_sub and has_subs_role:
                await member.remove_roles(subs_role, reason="RoleSync: Kein Twitch Subscriber mehr")
                print(f"[RoleSync] ❌ {member} → ⭐ Subs entzogen")
        except discord.Forbidden:
            print(f"[RoleSync] ⛔ Keine Berechtigung bei {member}!")
        except discord.HTTPException as e:
            print(f"[RoleSync] HTTP-Fehler bei {member}: {e}")

    # ------------------------------------------------------------------
    # Echtzeit: feuert sofort bei jeder Rollenänderung
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return
        await self._sync_member(after)

    # ------------------------------------------------------------------
    # Periodisch: alle X Minuten alle Member prüfen
    # ------------------------------------------------------------------
    @tasks.loop(minutes=SYNC_INTERVAL_MIN)
    async def sync_all_members(self):
        synced = 0
        for guild in self.bot.guilds:
            subs_role = guild.get_role(SUBS_ROLE_ID)
            if not subs_role:
                print("[RoleSync] ⚠️ Subs-Rolle nicht gefunden – SUBS_ROLE_ID prüfen!")
                continue
            for member in guild.members:
                await self._sync_member(member)
                synced += 1
        print(f"[RoleSync] 🔄 Periodischer Sync abgeschlossen ({synced} Member geprüft)")

    @sync_all_members.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()


# ──────────────────────────────────────────────
#  Setup-Funktion
# ──────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(RoleSync(bot))

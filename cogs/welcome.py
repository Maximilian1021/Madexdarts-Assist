import discord
from discord.ext import commands

VIEWER_ROLE_ID     = 1475119142616039444
WELCOME_CHANNEL_ID = 1475113895852113990  # ersetzen!

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # ── Rolle vergeben ──
        role = member.guild.get_role(VIEWER_ROLE_ID)
        if role:
            await member.add_roles(role, reason="Auto-Role: Neues Mitglied")
        else:
            print(f"[WARN] Zuschauerrolle nicht gefunden!")

        # ── Willkommensnachricht ──
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="👋 Willkommen auf dem Server!",
                description=(
                    f"Hey {member.mention}, schön dass du da bist! 🎯\n\n"
                    f"Du bist jetzt Mitglied **{member.guild.member_count}** – herzlich willkommen!\n\n"
                    f"➡️ Schau kurz in die **Regeln** rein\n"
                    f"➡️ Hol dir passende Rollen\n"
                    f"➡️ Und dann ab in den Chat! 💜"
                ),
                color=discord.Color.purple()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text="MadexDarts Community")
            await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
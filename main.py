import os
from datetime import datetime
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv("bot.env")

# Intents: all() geht, members ist fürs on_member_join wichtig
intents = discord.Intents.all()

now = datetime.now()
dt_string = now.strftime("%d.%m.%Y %H:%M:%S")


def extensions():
    files = Path("cogs").rglob("*.py")
    for file in files:
        # cogs/foo.py -> cogs.foo
        yield file.as_posix()[:-3].replace("/", ".")


class MadexBot(commands.Bot):
    async def setup_hook(self):
        # Extensions beim Start laden (async!)
        for ext_file in extensions():
            try:
                await self.load_extension(ext_file)
                print(f"Loaded {ext_file}")
            except Exception as ex:
                print(f"Failed to load {ext_file}: {ex}")

        # Slash Commands registrieren / aktualisieren
        # (wenn du global syncst, kann das bis zu 1h dauern; guild sync ist schneller)
        try:
            await self.tree.sync()
            print("Slash commands synced")
        except Exception as ex:
            print(f"Failed to sync slash commands: {ex}")


bot = MadexBot(
    command_prefix=commands.when_mentioned_or("$"),
    intents=intents,
    case_insensitive=True,
    description="MadexDartsbot - Assist overall",
    help_command=None
)


@bot.event
async def on_ready():
    print('---------------------------')
    print(dt_string)
    print('Logged in as:')
    print(bot.user.name)
    print(bot.user.id)
    print('---------------------------')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="madexdarts"
        ),
        status=discord.Status.idle
    )


# --------- Reload (async) ---------
async def unload_all():
    for ext_file in extensions():
        try:
            await bot.unload_extension(ext_file)
            print(f"Unloaded {ext_file}")
        except Exception as ex:
            print(f"Failed to unload {ext_file}: {ex}")


async def load_all():
    for ext_file in extensions():
        try:
            await bot.load_extension(ext_file)
            print(f"Loaded {ext_file}")
        except Exception as ex:
            print(f"Failed to load {ext_file}: {ex}")


async def client_reload():
    await unload_all()
    await load_all()
    print(f"\nReloaded at {dt_string}")


@bot.command()
async def reload(ctx):
    await client_reload()
    embed = discord.Embed(
        title="Reload abgeschlossen!",
        colour=discord.Colour.red(),
        description="Alle Module des Discord Bots wurden erfolgreich neu geladen"
    )
    embed.set_footer(
        text=f"Reload wurde von {ctx.author} ausgelöst",
        icon_url="https://cdn.max1021.de/G-E/GameEnergy_Green.png"
    )
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if ctx.invoked_with in ["rename", "close"]:
        return
    embed = discord.Embed(
        title="Es ist ein Fehler aufgetreten",
        colour=discord.Colour.red(),
        description=(
            "Bei der Ausführung des Commands ist ein Fehler aufgetreten.\n"
            f"**Error:** {error}"
        )
    )
    await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(os.getenv("TOKEN"))
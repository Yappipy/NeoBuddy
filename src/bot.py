# bot.py
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

from fieldboss import field_boss_command, todays_bosses_command, boss_alert_loop
from party_manager import force_calculator_command

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)

    async def setup_hook(self):
        try:
            guild = discord.Object(id=int(os.getenv('GUILD_ID')))  # replace with your guild ID

            # Clear all guild commands (force)
            self.tree.clear_commands(guild=guild)  # <-- Remove 'await'

            # Re-sync our local commands to the guild
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands to guild {guild.id}")
            print("Commands currently in bot.tree:")
            for cmd in self.tree.walk_commands():
                print(" -", cmd.name)
        except Exception as e:
            print("Error syncing commands:")
            traceback.print_exc()

bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    app_info = await bot.application_info()
    print(f"Logged in as: {bot.user} ({bot.user.id})")
    print(f"Application id: {app_info.id}")
    if not hasattr(bot, 'boss_alert_task'):
        bot.boss_alert_task = bot.loop.create_task(boss_alert_loop(bot))

@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello! I am your Discord bot.")

@bot.tree.command(name="ping_latency", description="Check the bot's latency.")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000  # Convert to milliseconds
    await interaction.response.send_message(f"Pong! Latency: {round(latency)} ms")



""" 
Register commands from other modules 
"""
# Field boss commands
bot.tree.add_command(field_boss_command)
bot.tree.add_command(todays_bosses_command)

# Party manager command
bot.tree.add_command(force_calculator_command)

if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Error: BOT_TOKEN not found in environment variables.")
    else:
        bot.run(token)

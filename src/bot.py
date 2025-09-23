# bot.py
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

from fieldboss import next_boss_command, boss_alert_loop, get_todays_bosses
from party_manager import force_calculator

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

# NOTE: changed name to field_boss (underscore) to avoid hyphen problems
@bot.tree.command(name="field_boss", description="Show the next field boss spawn time.")
async def field_boss(interaction: discord.Interaction):
    # import inside handler so any import-time errors show only on use
    await next_boss_command(interaction)

@bot.tree.command(name="todays_bosses", description="Show today's field bosses and their spawn times.")
async def todays_bosses(interaction: discord.Interaction):
    bosses = get_todays_bosses()
    if not bosses:
        msg = "No field bosses scheduled for the rest of today."
    else:
        msg = "**Today's Field Bosses:**\n"
        for boss in bosses:
            msg += f"- **{boss['location']}** at {boss['time'].strftime('%H:%M')} (In-Game Time)\n"
    await interaction.response.send_message(msg)

@bot.tree.command(name="force_calculator", description="Calculate max force for extra party members.")
@app_commands.describe(current_force="Current average force of the party",
                       party_size="Current size of the party (max 6)",
                       max_average_value="Maximum allowed average force")
async def force_calculator_command(interaction: discord.Interaction,
                                   current_force: int,
                                   party_size: int,
                                   max_average_value: int):
    if party_size < 1 or party_size > 6:
        await interaction.response.send_message("Error: Party size must be between 1 and 6.")
        return
    max_force = force_calculator(current_force, party_size, max_average_value)
    if max_force < 0:
        msg = "No extra members can be added without exceeding the max average force. Max force to lose per member: {-max_force}"
    else:
        msg = f"Current party size: {party_size}. Current average force: {current_force}.\n"
        msg = msg + f"Max force for each extra member to stay below {max_average_value} average: {max_force}"
    await interaction.response.send_message(msg)


if __name__ == '__main__':
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Error: BOT_TOKEN not found in environment variables.")
    else:
        bot.run(token)

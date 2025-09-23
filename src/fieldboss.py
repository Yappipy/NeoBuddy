import csv
from datetime import datetime, timedelta
import discord
import asyncio
import os
from discord import app_commands

BOSS_CSV_PATH = "./data/boss_timers.csv"  # Update path as needed

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def load_boss_timers():
    bosses = []
    with open(BOSS_CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Days of week
        for row_idx, row in enumerate(reader):
            for col_idx, cell in enumerate(row):
                cell = cell.strip()
                if cell.lower() in ("unknown", "missing") or not cell:
                    continue
                time_str = cell[:5]
                location = cell[5:].strip()
                try:
                    hour, minute = map(int, time_str.split(":"))
                except ValueError:
                    continue  # Skip malformed time
                bosses.append({
                    "weekday": col_idx,  # 0=Monday, 6=Sunday
                    "hour": hour,
                    "minute": minute,
                    "location": location
                })
    return bosses

def get_next_boss():
    bosses = load_boss_timers()
    now = datetime.utcnow() + timedelta(hours=1)  # UTC+1
    next_spawn = None
    for boss in bosses:
        today = now.replace(hour=boss["hour"], minute=boss["minute"], second=0, microsecond=0)
        days_ahead = (boss["weekday"] - now.weekday()) % 7
        spawn_time = today + timedelta(days=days_ahead)
        if spawn_time < now:
            spawn_time += timedelta(days=7)
        if not next_spawn or spawn_time < next_spawn["time"]:
            next_spawn = {
                "location": boss["location"],
                "time": spawn_time
            }
    return next_spawn

def get_todays_bosses():
    """Returns a list of bosses scheduled for today (UTC+1)."""
    bosses = load_boss_timers()
    now = datetime.utcnow() + timedelta(hours=1)  # UTC+1
    today_weekday = now.weekday()
    todays_bosses = []
    for boss in bosses:
        if boss["weekday"] == today_weekday:
            spawn_time = now.replace(hour=boss["hour"], minute=boss["minute"], second=0, microsecond=0)
            # If the boss time has already passed today, skip it
            if spawn_time >= now:
                todays_bosses.append({
                    "location": boss["location"],
                    "time": spawn_time
                })
    # Sort by time
    todays_bosses.sort(key=lambda b: b["time"])
    return todays_bosses

async def next_boss_command(interaction: discord.Interaction):
    boss = get_next_boss()
    if boss:
        msg = f"Next boss: **{boss['location']}** at {boss['time'].strftime('%A %H:%M (In-Game Time)')}"
    else:
        msg = "No boss timers found."
    await interaction.response.send_message(msg)

@discord.app_commands.command(name="field_boss", description="Show the next field boss spawn time.")
async def field_boss_command(interaction: discord.Interaction):
    await next_boss_command(interaction)

@discord.app_commands.command(name="todays_bosses", description="Show today's field bosses and their spawn times.")
async def todays_bosses_command(interaction: discord.Interaction):
    bosses = get_todays_bosses()
    if not bosses:
        msg = "No field bosses scheduled for the rest of today."
    else:
        msg = "**Today's Field Bosses:**\n"
        for boss in bosses:
            msg += f"- **{boss['location']}** at {boss['time'].strftime('%H:%M')} (In-Game Time)\n"
    await interaction.response.send_message(msg)

async def boss_alert_loop(bot):
    await bot.wait_until_ready()
    channel_id = int(os.getenv('ALERT_CHANNEL_ID'))
    role_id = int(os.getenv('ALERT_ROLE_ID'))
    alerted_times = set()
    while not bot.is_closed():
        boss = get_next_boss()
        if boss:
            alert_time = boss['time'] - timedelta(minutes=5)
            now = datetime.utcnow() + timedelta(hours=1)  # UTC+1
            # Only alert if within 1 minute window and not already alerted
            if alert_time <= now < alert_time + timedelta(minutes=1):
                if alert_time not in alerted_times:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"<@&{role_id}> Next boss **{boss['location']}** at {boss['time'].strftime('%A %H:%M')} (In-Game Time)!")
                    alerted_times.add(alert_time)
        await asyncio.sleep(60)  # Check every minute
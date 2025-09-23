import discord
from discord import app_commands
import math

MAX_PARTY_SIZE = 6

def force_calculator(current_force, party_size, max_average_value):
    """
    Calculate the max force the extra members can have to stay below the max_value.
    :param current_force: The current average force of the party.
    :param party_size: The current size of the party.
    :param max_average_value: The maximum allowed force.
    
    Reminder : max party size is 6.
    """
    if party_size == MAX_PARTY_SIZE:
        force_to_lose = (current_force - max_average_value * MAX_PARTY_SIZE)/MAX_PARTY_SIZE
        return -force_to_lose  # No extra members can be added -- Force to lose per member

    total_current_force = current_force * party_size
    max_total_force = max_average_value * MAX_PARTY_SIZE
    remaining_force = max_total_force - total_current_force
    max_extra_members = MAX_PARTY_SIZE - party_size
    max_force_per_extra_member = math.ceil(remaining_force / max_extra_members)
    return int(max_force_per_extra_member)

@discord.app_commands.command(name="force_calculator", description="Calculate max force for extra party members.")
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


import discord
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


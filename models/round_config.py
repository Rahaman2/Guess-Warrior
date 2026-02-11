"""Round configuration for multiplayer matches.

Change these values to adjust the round system.
Both backend and frontend receive these from the server,
so only this file needs updating.
"""

# Number of rounds per match
TOTAL_ROUNDS = 3

# Score multiplier for each round (index 0 = round 1, etc.)
ROUND_MULTIPLIERS = [1, 2, 3]

# Seconds between rounds (auto-advance delay)
BETWEEN_ROUND_DELAY = 5

# Seconds per round
ROUND_TIMER_SECONDS = 60

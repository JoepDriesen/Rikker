from django.dispatch import Signal

# Define signals used throughout the program to notify bots of actions to be taken
bidding_needed = Signal()
playing_needed = Signal()
collection_needed = Signal()
from portal import bidding_needed, playing_needed, collection_needed
from game.models import Bid, Round, Card, Trick

def do_bidding(sender, **kwargs):
    next_player_to_bid = sender.next_player_to_bid()
    if next_player_to_bid is not None and next_player_to_bid.is_bot:
        try:
            sender.place_bid(next_player_to_bid, Bid.PASS)
        except Round.BadBidException:
            # This can only be if this bot is the last player and everybody else has passed.
            sender.place_bid(next_player_to_bid, Bid.RIK)
            
    if sender.highest_bid is not None and sender.highest_bid.player.is_bot and not sender.highest_bid.is_complete():
        for suit in Card.SUITS:
            try:
                sender.finalize_bid(sender.highest_bid.player, trump_suit=Card.CLUBS, mate_suit=suit[0])
                break
            except Bid.IllegalChoiceException:
                pass
bidding_needed.connect(do_bidding)

def do_play_card(sender, **kwargs):
    next_player_to_play = sender.next_player_to_play()
    if next_player_to_play.is_bot:
        owned_cards = list(sender.round.game.isplaying_set.get(player=next_player_to_play).cards.all())
        card_to_play = 0
        while True:
            try:
                sender.play_card(next_player_to_play, owned_cards[card_to_play])
                break
            except Trick.BadPlayException:
                card_to_play += 1
            
playing_needed.connect(do_play_card)

def do_collect_trick(sender, **kwargs):
    if sender.winner().is_bot:
        sender.collect(sender.winner())
collection_needed.connect(do_collect_trick)
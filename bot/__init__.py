from portal import bidding_needed, playing_needed, collection_needed
from portal.models import Bid, Round, Card

def do_bidding(sender, **kwargs):
    next_player_to_bid = sender.next_player_to_bid
    if next_player_to_bid.is_bot:
        try:
            sender.place_bid(next_player_to_bid, Bid.PASS)
        except Round.CannotPassException:
            sender.place_bid(next_player_to_bid, Bid.RIK)
            # TODO: put some error checking here:
            sender.finalize_bid(trump_suit=Card.CLUBS, mate_suit=Card.HEARTS, mate_cardnumber=1)
bidding_needed.connect(do_bidding)

def do_play_card(sender, **kwargs):
    next_player_to_play = sender.next_player_to_play
    if next_player_to_play.is_bot:
        owned_cards = sender.game.isplaying_set.get(player=next_player_to_play).cards.all()
        if not sender.current_trick or not sender.current_trick.cards.exists():
            card_to_play = owned_cards[0]
        else:
            try:
                card_to_play = owned_cards.filter(suit=sender.current_trick.requested_suit)[0]
            except IndexError:
                card_to_play = owned_cards.all().order_by('number')[0] 
        
        sender.play_card(next_player_to_play, card_to_play)
playing_needed.connect(do_play_card)

def do_collect_trick(sender, **kwargs):
    current_trick = sender.current_trick
    playedintrick = sender.current_trick.playedintrick_set.all()
    cards = sender.current_trick.cards.all()
    winner = sender.current_trick.winner()
    if sender.current_trick.winner().is_bot:
        sender.collect_current_trick(sender.current_trick.winner())
collection_needed.connect(do_collect_trick)
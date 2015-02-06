from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
import portal
from portal import bidding_needed, playing_needed, collection_needed

class CardManager(models.Manager):
    
    def get_by_identifier(self, card_identifier):
        suit_letter = card_identifier[0]
        suit = None
        for possible_suit in Card.SUITS:
            if Card.SUIT_MAP[possible_suit[1]] == suit_letter:
                suit = possible_suit[0]
        if suit is None:
            raise Exception('Card identifier does not have a valid suit: {}'.format(card_identifier))
        number = int(card_identifier[1:])
        return self.get(suit=suit, number=number)
        
class Card(models.Model):
    """
    This class represents a card
    
    """
    CLUBS, DIAMONDS, HEARTS, SPADES = 0, 1, 2, 3
    SUITS = ((CLUBS, 'w'), (DIAMONDS, 'e'), (HEARTS, 'r'), (SPADES, 'q'))
    SUIT_MAP = {'w': 'C', 'e': 'D', 'r': 'H', 'q': 'S'}
    
    objects = CardManager()
    
    class Meta:
        unique_together = (("number", "suit"), )
        
    @classmethod
    def get_card_number_display(cls, card_number):
        d = {10: '0', 11: 'a', 12: 's', 13: 'd'}
        return d.get(card_number, card_number)
    
    number = models.PositiveSmallIntegerField()
    suit = models.PositiveSmallIntegerField(choices=SUITS)
    
    def worth(self):
        if self.number == 1:
            return 13
        return self.number - 1
    
    def __unicode__(self):
        return '%s of %s' % (self.number, self.get_suit_display())
    
    def identifier(self):
        return '%s%s' % (self.SUIT_MAP[self.get_suit_display()], self.number)
    
    def image_file(self):
        return 'img/cards/%s.png' % self.identifier()

class Bid(models.Model):
    """
    This class represents a bid made by a player at the start of a round
    
    """
    PASS, RIK, RIKp1, MISERIE, RIKp2, RIKp3, OPENMISERIEKAART, OPENALLESKAART, RIKp4, RIKp5, OPENMISERIE, OPENALLES = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
    BIDS = ((RIK, 'Rik'), (RIKp1, 'Rik voor 9'), (MISERIE, 'Miserie'), (RIKp2, 'Rik voor 10'), (RIKp3, 'Rik voor 11'),
            (OPENMISERIEKAART, 'Open miserie met kaart'), (OPENALLESKAART, 'Open voor alles met kaart'), (RIKp4, 'Rik voor 12'),
            (RIKp5, 'Rik voor 12'), (OPENMISERIE, 'Open miserie'), (OPENALLES, 'Open voor alles'), (PASS, 'Pas'))
    
    class Meta:
        ordering = ['-bid', ]
    
    round = models.ForeignKey('Round', related_name='bids')
    player = models.ForeignKey(get_user_model())
    
    bid = models.PositiveSmallIntegerField(choices=BIDS, default=PASS)
    
    trump_suit = models.PositiveSmallIntegerField(choices=Card.SUITS, null=True, blank=True)
    mate_suit = models.PositiveSmallIntegerField(choices=Card.SUITS, null=True, blank=True)
    mate_card = models.PositiveSmallIntegerField(null=True, blank=True)
    
    def __unicode__(self):
        if self.bid == self.PASS:
            return '%s passes' % self.player.username
        return 'Bid %s by %s' % (self.get_bid_display(), self.player.username)
    
    def mate_card_display(self):
        return Card.get_card_number_display(self.mate_card)
    
    def is_rik(self):
        if self.bid in [self.RIK, self.RIKp1, self.RIKp2, self.RIKp3, self.RIKp4, self.RIKp5]:
            return True
    
    def trump_suit_needed(self):
        if self.bid in [self.MISERIE, self.OPENMISERIEKAART, self.OPENMISERIE]:
            return False
        return True
    
    def mate_card_needed(self):
        return self.is_rik()
        
    def get_trump_pick_form(self):
        if self.trump_suit_needed():
            if self.mate_card_needed():
                return ('trump_and_mate_form', portal.forms.PickTrumpSuitAndMateForm)
            return ('trump_form', portal.forms.PickTrumpSuitForm)
        return None

class Round(models.Model):
    """
    This class represents a round of cards that is currently being played
    
    """
    class BidTooLowException(Exception):
        pass
    
    class CannotPassException(Exception):
        pass
    
    class MissingCardException(Exception):
        pass
    
    class CantPlayThatCardException(Exception):
        pass
    
    class Meta():
        ordering = ('-id', )
    
    game = models.ForeignKey('Game', related_name='rounds')
    
    dealer = models.ForeignKey(get_user_model(), related_name='games_dealing')
    
    highest_bid = models.ForeignKey(Bid, null=True, blank=True, related_name='highest_for_round')
    
    next_player_to_bid = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='games_to_bid')
    
    playing = models.BooleanField(blank=True, default=False)
    
    next_player_to_play = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='games_to_play')
    
    mate = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='mate_in_games')
    
    def __unicode__(self):
        try:
            return 'Round #%s of %s' % (self.game.round_number, self.game)
        except Game.DoesNotExist:
            return None
    
    def temp_highest_bid(self):
        try:
            last_bid = self.bids.all()[0]
            if last_bid.bid != Bid.PASS:
                return last_bid
        except IndexError:
            pass
        return None
    
    def get_next_player_to_bid(self, current_player):
        next_player_in_line = current_player
        while True:
            next_player_in_line = self.game.get_next_player(next_player_in_line)
            if next_player_in_line == current_player:
                return None
            if self.temp_highest_bid() is not None and next_player_in_line == self.temp_highest_bid().player:
                return None
            try:
                self.bids.get(player=next_player_in_line, bid=Bid.PASS)
            except Bid.DoesNotExist:
                return next_player_in_line
    
    def tricks_played(self):
        return self.tricks.filter(collected=True).count()
    
    def place_bid(self, player, bid):
        if self.highest_bid is not None or player != self.next_player_to_bid or self.playing:
            raise PermissionDenied()        
        
        current_highest_bid = self.temp_highest_bid()
        if current_highest_bid is None or bid > current_highest_bid or bid == Bid.PASS:
            if bid == Bid.PASS:
                # Make sure this is not the last player passing when everyone else has passed
                amount_of_players = len(self.game.players.all())
                notpass_present = False
                passes = 0
                for tmp_bid in self.bids.all():
                    if tmp_bid.bid == Bid.PASS:
                        passes += 1
                    else:
                        notpass_present = True
                if not notpass_present and passes >= (amount_of_players - 1):
                    raise self.CannotPassException()
                 
            bid = Bid(round=self, player=player, bid=bid)
            bid.save()
            
            self.next_player_to_bid = self.get_next_player_to_bid(player)
            if self.next_player_to_bid is None:
                # Bidding is done, set the highest bid
                self.highest_bid = self.temp_highest_bid()                
                
            if self.highest_bid is None:
                bidding_needed.send(sender=self)
                self.save()
            else:
                if not self.highest_bid.trump_suit_needed():
                    # no trump/mate cards need to be picked
                    self.finalize_bid()
                else:
                    self.save()
            return bid
            
        raise self.BidTooLowException()
    
    def finalize_bid(self, trump_suit=None, mate_suit=None, mate_cardnumber=None):
        if self.highest_bid is None:
            raise PermissionDenied()
        
        if self.highest_bid.trump_suit_needed():
            if trump_suit is None:
                raise self.MissingCardException('Trump suit is needed')
            if self.highest_bid.mate_card_needed():
                if mate_suit is None or mate_cardnumber is None:
                    raise self.MissingCardException('Mate card is needed')
                self.highest_bid.mate_suit = mate_suit
                self.highest_bid.mate_card = mate_cardnumber
                mate_card = Card.objects.get(suit=mate_suit, number=mate_cardnumber)
                self.mate = self.game.players.get(isplaying__cards=mate_card)
            self.highest_bid.trump_suit = trump_suit
        self.highest_bid.save()
        self.playing = True
        self.next_player_to_play = self.game.get_next_player(self.dealer)
        self.save()
        playing_needed.send(sender=self)
        
    _current_trick_cache = None
    @property
    def current_trick(self):
        try:
            current_trick_updated = self.tricks.get(collected=False)
        except ObjectDoesNotExist:
            self._current_trick_cache = None
            return self._current_trick_cache
        
        if self._current_trick_cache is None or self._current_trick_cache != current_trick_updated:
            self._current_trick_cache = current_trick_updated
        
        return self._current_trick_cache
    
    _previous_trick_cache = None
    @property
    def previous_trick(self):
        try:
            previous_trick_updated = self.tricks.all().order_by('-number')[1]
        except IndexError:
            self._previous_trick_cache = None
            return self._previous_trick_cache
        
        if self._previous_trick_cache is None or self._previous_trick_cache != previous_trick_updated:
            self._previous_trick_cache = previous_trick_updated
        
        return self._previous_trick_cache   
    
    def play_card(self, player, card):
        if not self.playing or self.next_player_to_play != player or (self.current_trick is not None and self.current_trick.is_done()):
            raise PermissionDenied()
        if card not in self.game.isplaying_set.get(player=player).cards.all():
            raise PermissionDenied()
        
        if self.current_trick is None:
            # First card of a new trick
            self.tricks.add(Trick(number=self.tricks.count(), requested_suit=card.suit))
        else:
            if card.suit != self.current_trick.requested_suit:
                # Check if the player does not have any cards of the requested suit left
                if IsPlaying.objects.get(game=self.game, player=player).cards.filter(suit=self.current_trick.requested_suit).exists():
                    raise self.CantPlayThatCardException("You must follow suit if possible.")
        
        self.current_trick.play_card(player, card)
        
        isplaying = IsPlaying.objects.get(game=self.game, player=player)
        isplaying.cards.remove(card)
        
        self.next_player_to_play = self.game.get_next_player(player)
        
        if self.current_trick.is_done():
            self.next_player_to_play = None
        
        self.save()
        
        if not self.current_trick.is_done():
            playing_needed.send(sender=self)
        else:
            collection_needed.send(sender=self)
    
    def collect_current_trick(self, player):
        if self.current_trick is None or not self.current_trick.is_done() or self.current_trick.winner() != player:
            raise PermissionDenied()
        
        current_trick = self.current_trick
        current_trick.collected = True
        current_trick.save()
        
        if self.tricks_played() < 13:
            self.next_player_to_play = current_trick.winner()
            self.save()
        
            playing_needed.send(sender=self)
        else:
            self.next_player_to_play = None
            self.save()
        
            self.game.finish_round()
    
    def asking_team_tricks(self):
        """
        Returns the amount of tricks currently won by the asking team
        
        """
        tricks_won = 0
        for trick in self.tricks.all():
            if trick.winner() == self.highest_bid.player or trick.winner() == self.mate:
                tricks_won += 1
        return tricks_won
    
    def asking_team_won(self):
        """
        Returns wether the asking team won this round
        
        """
        return self.asking_team_points() >= 0
    
    def asking_team_points(self):
        """
        Returns the points for the asking team at the end of the
        round (can be negative
        
        """
        if self.tricks_played() < 13:
            return Exception('Round is not yet finished')
        
        tricks_won = self.asking_team_tricks()
        bid = self.highest_bid.bid
        if bid == Bid.RIK:
            if tricks_won >= 8:
                return 1 + (tricks_won - 8)
            return (tricks_won - 8) - 1
        if bid == Bid.RIKp1:
            if tricks_won >= 9:
                return 1 + (tricks_won - 9)
            return (tricks_won - 9) - 1
        if bid == Bid.RIKp2:
            if tricks_won >= 10:
                return 1 + (tricks_won - 10)
            return (tricks_won - 10) - 1
        if bid == Bid.RIKp3:
            if tricks_won >= 11:
                return 1 + (tricks_won - 11)
            return (tricks_won - 11) - 1
        if bid == Bid.RIKp4:
            if tricks_won >= 12:
                return 1 + (tricks_won - 12)
            return (tricks_won - 12) - 1
        if bid == Bid.RIKp5:
            if tricks_won >= 13:
                return 1 + (tricks_won - 13)
            return (tricks_won - 13) - 1
        # TODO: implement other games
        return 0
    
    def other_player_points(self):
        return -self.asking_team_points()
    
    def get_points_earned(self, player):
        if player == self.highest_bid.player or player == self.mate:
            return self.asking_team_points()
        return self.other_player_points()
    
    def mate_card_played(self):
        if self.highest_bid is not None:
            try:
                PlayedInTrick.objects.get(card__number=self.highest_bid.mate_card, card__suit=self.highest_bid.mate_suit, trick__round=self)
                return True
            except:
                pass
        return False
    
    def save(self, *args, **kwargs):
        self.game.changed()
        super(Round, self).save(*args, **kwargs)
        
class Score(models.Model):
    """
    Holds the score for a player at the start of a round
    
    """
    round = models.ForeignKey(Round, related_name='scores')
    player = models.ForeignKey(get_user_model(), related_name='scores')
    
    score = models.IntegerField()
        

class Trick(models.Model):
    
    round = models.ForeignKey(Round, related_name='tricks')
    number = models.PositiveSmallIntegerField(default=0)
    
    cards = models.ManyToManyField(Card, through='PlayedInTrick')
    
    requested_suit = models.PositiveSmallIntegerField(choices=Card.SUITS)
    
    collected = models.BooleanField(default=False)
    
    def cards_in_trick(self):
        return len(PlayedInTrick.objects.filter(trick=self))
    
    def play_card(self, player, card):
        ordinal = self.cards_in_trick()
        PlayedInTrick(card=card, trick=self, ordinal=ordinal, played_by=player).save()
    
    def is_done(self):
        return self.cards.count() >= 4
    
    def winner(self):
        if not self.is_done():
            return None
        trump_cards = sorted(self.playedintrick_set.filter(card__suit=self.round.highest_bid.trump_suit), key=lambda x: x.card.worth(), reverse=True)
        if len(trump_cards) > 0:
            return trump_cards[0].played_by
        tmp = sorted(self.playedintrick_set.filter(card__suit=self.requested_suit), key=lambda x: x.card.worth(), reverse=True)
        return tmp[0].played_by
        
    
class PlayedInTrick(models.Model):
    
    card = models.ForeignKey(Card)
    trick = models.ForeignKey(Trick)
    
    ordinal = models.PositiveSmallIntegerField()
    played_by = models.ForeignKey(get_user_model())
    
    def __unicode__(self):
        return '%s playing in trick %s by %s' % (self.card, self.trick.id, self.played_by)
        
    
class GameManager(models.Manager):
    
    def start_game(self, players):
        game = Game()
        game.save()
        
        seat = 0
        try:
            for i in range(4):
                seat = i
                player = players[i]
                isplaying = IsPlaying(player=player, game=game, seat=seat)
                if i == 0:
                    # If its the player creating the game, autoaccept
                    isplaying.accepted = True
                isplaying.save()
        except IndexError:
            for i in range(4 - len(players)):
                player = get_user_model().objects.get(username='Bot #%s' % (i + 1))
                isplaying = IsPlaying(player=player, game=game, seat=seat, accepted=True)
                isplaying.save()
                seat += 1
        return game
    
class Game(models.Model):
    """
    This class represents a game in progress
    
    """
    DEAL_ORDER = [4, 4, 5]
    
    objects = GameManager()
    
    players = models.ManyToManyField(get_user_model(), through='IsPlaying')
    
    deck = models.ManyToManyField(Card, through='IsInDeck')
    deck_initialized = models.BooleanField(default=False)
    
    current_round = models.OneToOneField(Round, null=True, blank=True, default=None, related_name='game_current')
    round_number = models.PositiveIntegerField(default=0, editable=False)
    
    def __unicode__(self):
        return 'Game #%s' % self.pk
    
    def status(self):
        if self.current_round is None:
            return 'Waiting for game to start'
        # TODO: add more statusses
        return 'Unknown status'
    
    def changed(self):
        for isplaying in self.isplaying_set.all():
            isplaying.needs_update = True;
            isplaying.save()
    
    def everybody_accepted(self):
        for isplaying in self.isplaying_set.all():
            if not isplaying.accepted:
                return False
        return True
    
    def current_dealer(self):
        if self.round_number <= 0:
            return None
        ao_players = len(self.players.all())
        dealer_seat = (self.round_number - 1) % ao_players
        
        return self.players.get(seat=dealer_seat)
    
    def next_dealer(self):
        """
        The player that will be dealing next round
        
        """
        ao_players = len(self.players.all())
        dealer_seat = self.round_number % ao_players
        
        return self.players.get(isplaying__seat=dealer_seat)
    
    def initialize_deck(self):
        self.deck.clear()
        
        card_no = 0
        cards_in_deck = []
        for card in Card.objects.all().order_by('?'):
            isindeck = IsInDeck(card=card, game=self, ordinal=card_no)
            cards_in_deck.append(isindeck)
            card_no += 1
        IsInDeck.objects.bulk_create(cards_in_deck)
        self.deck_initialized = True
        self.deal_allowed = True
        self.save()
    
    def start_round(self):
        if not self.deck_initialized or (self.current_round is not None and not self.current_round.tricks_played() >= 13):
            raise PermissionDenied()
        
        new_round = Round(game=self, dealer=self.next_dealer(), next_player_to_bid=self.get_next_player(self.next_dealer()))
        new_round.save()
        
        # Save score for each player at the start of this round
        for isplaying in self.isplaying_set.all():
            Score(round=new_round, player=isplaying.player, score=isplaying.score).save()
        
        self.current_round = new_round
        self.deal()
        self.save()
        bidding_needed.send(sender=self.current_round)
    
    def deal(self):
        cards = self.deck.all().order_by('-isindeck__ordinal')
        
        # Reset all cards in the players' hands
        for isplaying in self.isplaying_set.all():
            isplaying.cards.clear()
            
        # Deal cards
        next_card_to_deal = 0
        for deal_amount in self.DEAL_ORDER:
            for isplaying in self.isplaying_set.all():
                for card in cards[next_card_to_deal:next_card_to_deal+deal_amount]:
                    isplaying.cards.add(card)
                    next_card_to_deal += 1
        self.deck.clear()
        self.changed()
    
    def get_next_player(self, current_player):
        current_isplaying = self.isplaying_set.get(player=current_player)
        try:
            next_isplaying = self.isplaying_set.get(seat=(current_isplaying.seat+1))
        except ObjectDoesNotExist:
            next_isplaying = self.isplaying_set.get(seat=0)
        return next_isplaying.player
    
    def finish_round(self):
        # Give points to each player
        for isplaying in self.isplaying_set.all():
            isplaying.score = isplaying.score + self.current_round.get_points_earned(isplaying.player)
            isplaying.save()
            
        # Put all cards in deck in order
        ordinal = 0
        for trick in self.current_round.tricks.all().order_by('-number'):
            for card in trick.cards.all().order_by('-playedintrick__ordinal'):
                IsInDeck(card=card, game=self, ordinal=ordinal).save()
        self.changed()
    
    def save(self, *args, **kwargs):
        self.round_number = self.rounds.count()
        self.changed()
        super(Game, self).save(*args, **kwargs)
        

class IsPlaying(models.Model):
    
    class Meta:
        ordering = ['seat']
        
    player = models.ForeignKey(get_user_model())
    game = models.ForeignKey(Game)
    
    seat = models.PositiveSmallIntegerField()
    
    accepted = models.BooleanField(default=False)
    abandoned = models.BooleanField(default=False)
    
    score = models.IntegerField(default=100)
    
    cards = models.ManyToManyField(Card)
    
    needs_update = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s is playing in Game #%s' % (self.player.username, self.game.id)
    
    def last_bid(self):
        for bid in self.game.current_round.bids.all():
            if bid.player == self.player:
                return bid
        return None
    
    def current_tricks(self):
        if self.game.current_round is not None:
            tricks = self.game.current_round.tricks.all()
            count = 0
            for trick in tricks:
                if trick.winner() == self.player:
                    count += 1
            return count
        return None
            
class IsInDeck(models.Model):
    
    card = models.ForeignKey(Card)
    game = models.ForeignKey(Game)
    
    # The place that this card has in the deck (0 is the bottom card)
    ordinal = models.PositiveSmallIntegerField()
    
    
    


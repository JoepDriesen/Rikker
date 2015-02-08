from django.db import models
from django.contrib.auth import get_user_model
from portal import bidding_needed, playing_needed, collection_needed
import threading

global_lock = threading.RLock()

class GameException(Exception):
    pass

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
    
    class IllegalChoiceException(Exception):
        pass
    
    PASS, RIK, RIKp1, MISERIE, RIKp2, RIKp3, OPENMISERIEKAART, OPENALLESKAART, RIKp4, RIKp5, OPENMISERIE, OPENALLES = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
    BIDS = ((RIK, 'Rik'), (RIKp1, 'Rik voor 9'), (MISERIE, 'Miserie'), (RIKp2, 'Rik voor 10'), (RIKp3, 'Rik voor 11'),
            (OPENMISERIEKAART, 'Open miserie met kaart'), (OPENALLESKAART, 'Open voor alles met kaart'), (RIKp4, 'Rik voor 12'),
            (RIKp5, 'Rik voor 12'), (OPENMISERIE, 'Open miserie'), (OPENALLES, 'Open voor alles'), (PASS, 'Pas'))
    TRICKS_REQUIRED = {RIK: 8, RIKp1: 9, RIKp2: 10, RIKp3: 11, RIKp4: 12, RIKp5: 13}
    POINTS = {MISERIE: 9, OPENMISERIEKAART: 12, OPENALLESKAART: 15, OPENMISERIE: 18, OPENALLES: 21}
    
    class Meta:
        ordering = ['-bid', ]
        
    bid_lock = global_lock
    
    round = models.ForeignKey('Round', related_name='bids')
    player = models.ForeignKey(get_user_model())
    
    bid = models.PositiveSmallIntegerField(choices=BIDS, default=PASS)
    
    trump_suit = models.PositiveSmallIntegerField(choices=Card.SUITS, null=True, blank=True)
    mate_suit = models.PositiveSmallIntegerField(choices=Card.SUITS, null=True, blank=True)
    mate_card = models.PositiveSmallIntegerField(null=True, blank=True)
    
    def __unicode__(self):
        if self.bid == self.PASS:
            return '%s passes' % self.player.username
        return '%s by %s' % (self.get_bid_display(), self.player.username)
    
    @classmethod
    def bid_is_rik(cls, bid):
        return bid in [cls.RIK, cls.RIKp1, cls.RIKp2, cls.RIKp3, cls.RIKp4, cls.RIKp5]
    
    @classmethod
    def bid_is_miserie(cls, bid):
        return bid in [cls.MISERIE, cls.OPENMISERIEKAART, cls.OPENMISERIE]
    
    @classmethod
    def bid_is_vooralls(cls, bid):
        return bid in [cls.OPENALLESKAART, cls.OPENALLES]
    
    def is_rik(self):
        with self.bid_lock:
            return self.bid_is_rik(self.bid)
        
    def is_miserie(self):
        with self.bid_lock:
            return self.bid_is_miserie(self.bid)
        
    def is_vooralles(self):
        with self.bid_lock:
            return self.bid_is_vooralls(self.bid)
        
    def tricks_needed_to_win(self):
        with self.bid_lock:
            if self.is_rik():
                return self.TRICKS_REQUIRED[self.bid]
            elif self.bid in [self.OPENALLESKAART, self.OPENALLES]:
                return 13
            else:
                # This is not applicable for Miserie
                return None
    
    def points_to_earn(self):
        with self.bid_lock:
            if self.is_rik():
                # This depends on the game
                return None
            return self.POINTS[self.bid]
    
    def trump_suit_needed(self):
        with self.bid_lock:
            if self.bid in [self.MISERIE, self.OPENMISERIEKAART, self.OPENMISERIE]:
                return False
            return True
    
    def mate_card_needed(self):
        with self.bid_lock:
            return self.is_rik()
    
    def is_complete(self):
        with self.bid_lock:
            if self.trump_suit_needed() and self.trump_suit is None:
                return False
            if self.mate_card_needed() and (self.mate_suit is None or self.mate_card is None):
                return False
            return True
    
    def mate_card_display(self):
        with self.bid_lock:
            return Card.get_card_number_display(self.mate_card)
    
        
    def get_bidding_finalize_form(self):
        with self.bid_lock:
            if self.trump_suit_needed():
                if self.mate_card_needed():
                    from forms import PickTrumpSuitAndMateForm
                    return PickTrumpSuitAndMateForm
                from forms import PickTrumpSuitForm
                return PickTrumpSuitForm
            return None
        
    def finalize(self, player, trump_suit=None, mate_suit=None):
        with self.bid_lock:
            if player != self.player:
                raise GameException('Player {} trying to finalize bid while {} has the highest bid'.format(player, self.player))
                
            if self.trump_suit_needed():
                if trump_suit is None:
                    raise self.IllegalChoiceException('You must choose a trump suit')
                    
                if self.mate_card_needed():
                    if mate_suit is None:
                        raise self.IllegalChoiceException('You must choose a mate card')
                    elif trump_suit == mate_suit:
                        raise self.IllegalChoiceException('You cannot pick the trump suit as mate.')
                    else:
                        # Check if the given mate suit can be picked
                        asking_hand = [cih.card for cih in CardInHand.objects.filter(isplaying__game=self.round.game, isplaying__player=player)]
                        # We first assume the mate card number is the Ace, which is always the case unless the asking
                        # player has all 4 aces.
                        mate_cardnumber = 1
                        
                        while True:
                            if len(filter(lambda card: (card.number == mate_cardnumber and card.suit == mate_suit), asking_hand)) > 0:
                                # The player has the highest card of the asked mate suit. This is only allowed if he has all of
                                # the highest cards except that of the trump suit 
                                if len(filter(lambda card: (card.number == mate_cardnumber and card.suit != trump_suit), asking_hand)) < 3:
                                    # The player has the option of picking another mate suit, it follows that this mate suit is an illegal
                                    # choice
                                    raise self.BadBidException('You must pick another mate suit. You have the highest card of the chosen mate suit and there are other options.')
                                # The player has all other cards of this number, so it would still appear this is an ok suit to pick, we must
                                # go deeper
                                mate_cardnumber -= 1
                                if mate_cardnumber <= 0:
                                    mate_cardnumber = 13
                                elif mate_cardnumber <= 1:
                                    raise Exception('Looping infinitely for some reason')
                                continue
                            # The player does not have the highest card of the chosen mate suit, this is an ok choice
                            break
                            
                    self.mate_suit = mate_suit
                    self.mate_card = mate_cardnumber
                        
                self.trump_suit = trump_suit
                    
                self.save()

class Round(models.Model):
    """
    This class represents a round of cards that is currently being played
    
    """
    class BadBidException(Exception):
        pass
    
    class Meta():
        ordering = ('-id', )
    
    round_lock = global_lock
        
    # Round phases
    BIDDING_PHASE, FINALIZE_BIDDING_PHASE, TRICK_TAKING_PHASE, END_OF_ROUND_PHASE = 0, 1, 2, 3
    
    game = models.ForeignKey('Game', related_name='rounds')
    
    dealer = models.ForeignKey(get_user_model(), related_name='games_dealing')
    
    highest_bid = models.ForeignKey(Bid, null=True, blank=True, related_name='highest_for_round')
    
    playing = models.BooleanField(blank=True, default=False)
    
    mate = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='mate_in_games')
    
    
    def __unicode__(self):
        try:
            return 'Round #%s of %s' % (list(self.game.rounds.all().reverse()).index(self) + 1, self.game)
        except Game.DoesNotExist:
            return None
        
    
    _bids_cache = None
    def all_bids(self):
        if self._bids_cache is None:
            self._bids_cache = self.bids.select_related('player').all()
        return self._bids_cache
    
    _tricks_cache = None
    def all_tricks(self):
        if self._tricks_cache is None:
            self._tricks_cache = self.tricks.prefetch_related('cards').all()
        return self._tricks_cache
    
    def tricks_played(self):
        with self.round_lock:
            return len(filter(lambda trick: trick.collected, self.all_tricks()))
        
    def all_tricks_played(self):
        with self.round_lock:
            return self.tricks_played() >= 13
        
    def asking_team_tricks(self):
        """
        Returns the amount of tricks currently won by the asking team
        
        """
        with self.round_lock:
            tricks_won = 0
            for trick in self.all_tricks():
                if trick.collected:
                    if (trick.winner() == self.highest_bid.player) or (self.mate is not None and trick.winner() == self.mate):
                        tricks_won += 1
            return tricks_won
    
    def asking_team_won(self):
        """
        Returns wether the asking team won this round
        
        """
        with self.round_lock:
            if self.highest_bid is None:
                return None
            
            if self.highest_bid.is_rik():
                if not self.all_tricks_played():
                    return None
                return self.asking_team_tricks() >= self.highest_bid.tricks_needed_to_win()
            
            elif self.highest_bid.is_miserie():
                if self.asking_team_tricks() > 0:
                    return False
                elif self.all_tricks_played():
                    return True
                return None
            
            elif self.highest_bid.is_vooralles():
                if self.asking_team_tricks() < len(self.all_tricks()):
                    return False
                elif self.all_tricks_played():
                    return True
                return None
            
            raise Exception('Unknown Bid')
    
    def is_finished(self):
        return self.asking_team_won() is not None
    
    def current_phase(self):
        with self.round_lock:
            if self.highest_bid is None:
                return self.BIDDING_PHASE
            elif not self.highest_bid.is_complete():
                return self.FINALIZE_BIDDING_PHASE
            elif not self.is_finished():
                return self.TRICK_TAKING_PHASE
            else:
                return self.END_OF_ROUND_PHASE
            
    def underway(self):
        return self.current_phase() is not self.END_OF_ROUND_PHASE
        
        
        
    
    def round_players_ordered(self):
        """
        Return a list of the players in this round in the order that they should play/bid. This
        means: [player_after_dealer, next_player, next_player, dealer]
        
        """
        with self.round_lock:
            next_player = self.game.get_next_player(self.dealer)
            while True:
                yield next_player
                if next_player == self.dealer:
                    return
                next_player = self.game.get_next_player(next_player)
    
    def next_player_to_bid(self):
        with self.round_lock:
            bids = self.all_bids()
            
            players = list(self.round_players_ordered())
            if len(filter(lambda bid: bid.bid == Bid.PASS, bids)) >= 3 and len(bids) > 3:
                # Everybody but 1 player has passed and bids have been placed, no more bidding is needed
                return None
            
            bidding_round = 1
            while True:
                for player in players:
                    if len(filter(lambda bid: bid.player == player, bids)) < bidding_round:
                        # This player has not yet bid this round
                        if len(filter(lambda bid: (bid.player == player and bid.bid == Bid.PASS), bids)) > 0:
                            # This player has passed before, so he may not bid again
                            continue
                        return player
                # Every player has bid this round, check the next round
                bidding_round += 1
                
                
                
    
    def temp_highest_bid(self):
        with self.round_lock:
            try:
                last_bid = self.all_bids()[0]
                if last_bid.bid != Bid.PASS:
                    return last_bid
            except IndexError:
                pass
            return None
    
    def place_bid(self, player, bid):
        with self.round_lock:
            if self.current_phase() is not self.BIDDING_PHASE:
                raise GameException('Player {} trying to place bid in phase {}'.format(player.username, self.current_phase()))
            if player != self.next_player_to_bid():
                raise GameException('Player {} trying to bid while it is {}\'s turn to bid'.format(player, self.next_player_to_bid()))
            
            if len(filter(lambda bid: (bid.player == player and bid.bid == Bid.PASS), self.all_bids())) > 0:
                raise GameException('This player ({}) has already passed and should not be allowed to place another bid.'.format(player.username))
            
            
            current_highest_bid = self.temp_highest_bid()
            if current_highest_bid is None or bid > current_highest_bid.bid or bid == Bid.PASS:
                if bid == Bid.PASS:
                    # Make sure this is not the last player passing when everyone else has passed
                    amount_of_players = len(self.game.players.all())
                    notpass_present = False
                    passes = 0
                    for tmp_bid in self.all_bids():
                        if tmp_bid.bid == Bid.PASS:
                            passes += 1
                        else:
                            notpass_present = True
                    if not notpass_present and passes >= (amount_of_players - 1):
                        raise self.BadBidException('You are the last player to bid and every other player has passed. You must place a bid.')
                     
                bid = Bid(round=self, player=player, bid=bid)
                bid.save()
                self._bids_cache = None
                
                if self.next_player_to_bid() is None:
                    # Bidding is done, set the highest bid
                    self.highest_bid = self.temp_highest_bid()                
                    self.save()
                
                self.advance()
                self.changed()
                
            else:
                raise self.BadBidException('Please bid higher than the currently placed bid.')
        
    def finalize_bid(self, player, trump_suit=None, mate_suit=None):
        with self.round_lock:
            if self.current_phase() is not self.FINALIZE_BIDDING_PHASE:
                raise GameException('Player {} trying to finalize bid during phase {}'.format(player, self.current_phase()))
            
            self.highest_bid.finalize(player, trump_suit, mate_suit)
            
            if self.highest_bid.mate_card_needed():
                mate_card = Card.objects.get(suit=self.highest_bid.mate_suit, number=self.highest_bid.mate_card)
                self.mate = self.game.players.get(isplaying__cards=mate_card)
                self.save()
    
    def current_trick(self):
        with self.round_lock:
            if self.current_phase() is not self.TRICK_TAKING_PHASE:
                raise GameException('Trying to get current trick while in phase {}'.format(self.current_phase()))
            
            try:
                uncollected_tricks = filter(lambda trick: not trick.collected, self.all_tricks())
                if len(uncollected_tricks) > 1:
                    raise Exception('Multiple uncollected tricks')
                current_trick = uncollected_tricks[0]
            except IndexError:
                prev_tricks = sorted(self.all_tricks(), key=lambda trick: trick.number, reverse=True)
                if len(prev_tricks) <= 0:
                    leader = self.game.get_next_player(self.dealer)
                else:
                    leader = prev_tricks[0].winner()
                current_trick = Trick(number=self.tricks.count(), leading_player=leader)
                self.tricks.add(current_trick)
                self._tricks_cache = None
            
            return current_trick
    
    def previous_trick(self):
        with self.round_lock:
            try:
                previous_trick = sorted(self.all_tricks(), key=lambda trick: trick.number, reverse=True)[1]
            except IndexError:
                previous_trick = None
            
            return previous_trick
        
        
        
    
    
        
    def asking_team_points(self):
        """
        Returns the points for the asking team at the end of the
        round (can be negative)
        
        """
        with self.round_lock:
            if not self.is_finished():
                return GameException('Round is not yet finished')
            
            if self.highest_bid.is_rik():
                tricks_won = self.asking_team_tricks()
                tricks_needed = self.highest_bid.tricks_needed_to_win()
                
                if tricks_won >= tricks_needed:
                    return tricks_won - tricks_needed + 1
                return tricks_won - tricks_needed - 1
            
            if self.asking_team_won():
                return self.highest_bid.points_to_earn()
            return -self.highest_bid.points_to_earn()
    
    def other_player_points(self):
        with self.round_lock:
            if self.highest_bid.is_rik():
                return -self.asking_team_points()
            else:
                return -self.asking_team_points()/3
    
    def get_points_earned(self, player):
        with self.round_lock:
            if player == self.highest_bid.player or player == self.mate:
                return self.asking_team_points()
            return self.other_player_points()
    
    def mate_card_played(self):
        with self.round_lock:
            if self.highest_bid is not None:
                try:
                    PlayedInTrick.objects.get(card__number=self.highest_bid.mate_card, card__suit=self.highest_bid.mate_suit, trick__round=self)
                    return True
                except:
                    pass
            return False
    
    
    
    
    
    
    def changed(self):
        """
        If any actions are taken in this game, notify the participants so
        they can update their game screen
    
        """
        with self.round_lock:
            self.game.changed()
    
    def advance(self):
        """
        Take bot actions if required
        
        """
        with self.round_lock:
            if self.current_phase() in [self.BIDDING_PHASE, self.FINALIZE_BIDDING_PHASE]:
                bidding_needed.send(sender=self)
            elif self.current_phase() is self.TRICK_TAKING_PHASE:
                self.current_trick().advance()
            
    def save(self, *args, **kwargs):
        with self.round_lock:
            result = super(Round, self).save(*args, **kwargs)
            self.changed()
            return result
        
class Score(models.Model):
    """
    Holds the score for a player at the start of a round
    
    """
    round = models.ForeignKey(Round, related_name='scores')
    player = models.ForeignKey(get_user_model(), related_name='scores')
    
    score = models.IntegerField()
        

class Trick(models.Model):
    
    class BadPlayException(Exception):
        pass
    
    # Trick phases
    PLAY_PHASE, DONE_PHASE = 0, 1
    
    trick_lock = global_lock
    
    round = models.ForeignKey(Round, related_name='tricks')
    number = models.PositiveSmallIntegerField(default=0)
    
    cards = models.ManyToManyField(Card, through='PlayedInTrick')
    
    leading_player = models.ForeignKey(get_user_model())
    requested_suit = models.PositiveSmallIntegerField(choices=Card.SUITS, default=None, blank=True, null=True)
    
    collected = models.BooleanField(default=False)
    
    def __unicode__(self):
        return str(self.id)
    
    _cards_cache = None
    def all_playedintrick(self):
        if self._cards_cache is None:
            self._cards_cache = self.playedintrick_set.select_related('card', 'played_by').all()
        return self._cards_cache
    
    def next_player_to_play(self):
        with self.trick_lock:
            cards = self.all_playedintrick()
            if len(cards) >= 4:
                # Everybody has played a card, this trick is done
                return None
            elif len(cards) <= 0:
                return self.leading_player
            
            players = list(self.round.round_players_ordered())
            while players[0].id != self.leading_player_id:
                players.append(players[0])
                del players[0]
            
            for player in players:
                if len(filter(lambda played: played.played_by == player, cards)) <= 0:
                    return player
            raise Exception('Some player has played two cards: {}'.format(list(cards)))
    
    def is_done(self):
        with self.trick_lock:
            return self.next_player_to_play() is None
    
    def current_phase(self):
        with self.trick_lock:
            if self.is_done():
                return self.DONE_PHASE
            return self.PLAY_PHASE
    
    def winner(self):
        with self.trick_lock:
            if self.current_phase() is not self.DONE_PHASE:
                return None
            
            trump_cards = sorted(filter(lambda played: played.card.suit == self.round.highest_bid.trump_suit, self.all_playedintrick()), key=lambda x: x.card.worth(), reverse=True)
            if len(trump_cards) > 0:
                return trump_cards[0].played_by
            tmp = sorted(filter(lambda played: played.card.suit == self.requested_suit, self.all_playedintrick()), key=lambda x: x.card.worth(), reverse=True)
            return tmp[0].played_by
    
    
    
    
    def play_card(self, player, card):
        with self.trick_lock:
            if self.current_phase() is not self.PLAY_PHASE:
                raise GameException('Player {} trying to play card in phase {}'.format(player, self.current_phase()))
            if self.next_player_to_play() != player:
                raise GameException('Player {} trying to play card while {} is next in line'.format(player, self.next_player_to_play()))
            
            try:
                CardInHand.objects.get(isplaying__game=self.round.game, isplaying__player=player, card=card)
            except CardInHand.DoesNotExist:
                raise GameException('Player {} trying to play card {}, but he does not have it in his hand'.format(player, card))
            
            ordinal = len(self.all_playedintrick())
            if ordinal == 0:
                self.requested_suit = card.suit
                self.save()
           
            if card.suit != self.requested_suit:
                # Check if the player does not have any cards of the requested suit left
                if IsPlaying.objects.get(game=self.round.game, player=player).cards.filter(suit=self.requested_suit).exists():
                    raise self.BadPlayException("You must follow suit if possible.")
            
            PlayedInTrick(card=card, trick=self, ordinal=ordinal, played_by=player).save()
            CardInHand.objects.get(isplaying__game=self.round.game, isplaying__player=player, card=card).delete()
            
            self._cards_cache = None
            
            self.advance()
            self.changed()
    
    def collect(self, player):
        with self.trick_lock:
            if self.current_phase() is not self.DONE_PHASE:
                raise GameException('Player {} trying to collect a trick during phase {}'.format(player, self.current_phase()))
            if self.winner() != player:
                raise GameException('Player {} trying to collect a trick he did not win'.format(player))
            
            self.collected = True
            self.save()
            
            self.advance()
            self.changed()
            
        
    
    
    def changed(self):
        """
        If any actions are taken in this game, notify the participants so
        they can update their game screen
    
        """
        with self.trick_lock:
            self.round.changed()
    
    def advance(self):
        """
        Take bot action if required
        
        """
        with self.trick_lock:
            if self.current_phase() is self.PLAY_PHASE:
                playing_needed.send(sender=self)
            elif self.current_phase() is self.DONE_PHASE:
                if not self.collected:
                    collection_needed.send(sender=self)
            
            
        
    
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
    
    def infofetch(self, game_id):
        game = self.select_related(
            'current_round__dealer', 
            'current_round__highest_bid__player').prefetch_related(
                'players',
                'isplaying_set__player', 
                'isplaying_set__cards', 
                'current_round__bids__player').get(id=game_id)
        if game.current_round is not None:
            game.current_round.game = game
        
        return game
    
class Game(models.Model):
    """
    This class represents a game in progress
    
    """
    DECK_SIZE = 52
    DEAL_ORDER = [4, 4, 5]
    
    # Game States
    BEFORE_ROUND, DURING_ROUND, AFTER_ROUND = 0, 1, 2
    
    game_lock = global_lock
    
    objects = GameManager()
    
    players = models.ManyToManyField(get_user_model(), through='IsPlaying')
    
    deck = models.ManyToManyField(Card, through='IsInDeck')
    deck_initialized = models.BooleanField(default=False)
    
    current_round = models.OneToOneField(Round, null=True, blank=True, default=None, related_name='game_current')
    round_number = models.PositiveIntegerField(default=0, editable=False)
    
    def __unicode__(self):
        return 'Game #%s' % self.pk
    
    def current_state(self):
        """
        Returns the current state of the game
        
        """
        with self.game_lock:
            if not self.deck_initialized:
                return None
            elif self.current_round is None:
                return self.BEFORE_ROUND
            elif self.current_round.underway():
                return self.DURING_ROUND
            else:
                return self.AFTER_ROUND
    
    def everybody_accepted(self):
        """
        Check if every participant has accepted to play in this game
        
        """
        with self.game_lock:
            for isplaying in self.isplaying_set.all():
                if not isplaying.accepted:
                    return False
            return True
    
    def current_dealer(self):
        """
        The current dealer of this game
        
        """
        with self.game_lock:
            if self.round_number <= 0:
                return None
            ao_players = len(self.players.all())
            dealer_seat = (self.round_number - 1) % ao_players
            
            return self.players.get(seat=dealer_seat)
    
    def next_dealer(self):
        """
        The player that will be dealing next round
        
        """
        with self.game_lock:
            ao_players = len(self.players.all())
            dealer_seat = self.round_number % ao_players
            
            for isplaying in self.isplaying_set.all():
                if isplaying.seat == dealer_seat:
                    return isplaying.player
            raise Exception('Bad dealer seat: {}'.format(dealer_seat))
        
    def get_next_player(self, current_player):
        """
        Returns the player that should play after the given player
        
        """
        with self.game_lock:
            current_isplaying = None
            for isplaying in self.isplaying_set.all():
                if isplaying.player == current_player:
                    current_isplaying = isplaying
                    break
            if current_isplaying is None:
                raise Exception('Player (id: {}) is nog playing in this game (id: {})'.format(current_player.id, self.id))
            
            seats = len(self.isplaying_set.all())
            next_seat = (current_isplaying.seat + 1) % seats
            for isplaying in self.isplaying_set.all():
                if isplaying.seat == next_seat:
                    return isplaying.player
            raise Exception('Bad next seat number: {}'.format(next_seat))
        
        
    
    
    def initialize_deck(self):
        """
        Add all playable cards to this game and give them an initial order
        
        """
        with self.game_lock:
            if self.current_state() is not None:
                raise GameException('Trying to initialize the deck during game state: {}'.format(self.current_state()))
            
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
            
        
        
    
    
    def deal(self):
        """
        Distribute the cards in the deck between players
        
        """
        with self.game_lock:
            if self.current_state() is not self.BEFORE_ROUND:
                raise GameException('Trying to deal during game state: {}'.format(self.current_state()))
            
            # TODO: check if the dealing starts at the correct person
            cards = self.deck.all().order_by('-isindeck__ordinal')
            if len(cards) != self.DECK_SIZE:
                raise GameException('Trying to deal with less than {} cards in the deck'.format(self.DECK_SIZE))
            
            # Reset all cards in the players' hands
            CardInHand.objects.filter(isplaying__game=self).delete()
                
            # Deal cards
            next_card_to_deal = 0
            cards_to_deal = []
            for deal_amount in self.DEAL_ORDER:
                for isplaying in self.isplaying_set.all():
                    for card in cards[next_card_to_deal:next_card_to_deal+deal_amount]:
                        cards_to_deal.append(CardInHand(isplaying=isplaying, card=card))
                        next_card_to_deal += 1
                        
            CardInHand.objects.bulk_create(cards_to_deal)
                
            self.deck.clear()
            
            self.changed()
    
    def start_round(self):
        """
        Start the next round
        
        """
        with self.game_lock:
            if self.current_state() is self.AFTER_ROUND:
                self.finish_round()
                
            if self.current_state() is not self.BEFORE_ROUND:
                raise GameException('Trying to start round during game state: {}'.format(self.current_state()))
            
            new_round = Round(game=self, dealer=self.next_dealer())
            new_round.save()
            
            # Save score for each player at the start of this round
            start_of_round_scores = []
            for isplaying in self.isplaying_set.all():
                start_of_round_scores.append(Score(round=new_round, player=isplaying.player, score=isplaying.score))
            Score.objects.bulk_create(start_of_round_scores)
            
            self.deal()
            self.current_round = new_round
            self.save()
            
            self.advance()
        
    
        
        
    
    
    def finish_round(self):
        """
        Finish the current round
        
        """
        with self.game_lock:
            if self.current_state() is not self.AFTER_ROUND:
                raise GameException('Trying to finish round during game state: {}'.format(self.current_state()))
            
            # Give points to each player
            for isplaying in self.isplaying_set.all():
                isplaying.score = isplaying.score + self.current_round.get_points_earned(isplaying.player)
                isplaying.save()
                
            # Put all cards in deck in order
            # TODO: fix if not all tricks were played out
            ordinal = 0
            for trick in self.current_round.tricks.all().order_by('-number'):
                for card in trick.cards.all().order_by('-playedintrick__ordinal'):
                    IsInDeck(card=card, game=self, ordinal=ordinal).save()
                    ordinal += 1
            if not self.current_round.all_tricks_played():
                for isplaying in self.isplaying_set.all():
                    for card in isplaying.cards.all():
                        IsInDeck(card=card, game=self, ordinal=ordinal).save()
                        ordinal += 1
                    isplaying.cards.clear()
                        
            
            self.current_round = None
            self.save()
        
    
    def changed(self):
        """
        If any actions are taken in this game, notify the participants so
        they can update their game screen
    
        """
        IsPlaying.objects.filter(game=self).update(needs_update=True)
    
    def advance(self):
        """
        Take bot actions if required
        
        """
        with self.game_lock:
            if self.current_state() is self.DURING_ROUND:
                self.current_round.advance()
    
    def save(self, *args, **kwargs):
        with self.game_lock:
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
    
    cards = models.ManyToManyField(Card, through='CardInHand')
    
    needs_update = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s is playing in Game #%s' % (self.player.username, self.game.id)
    
    def abandon(self):
        self.abandoned = True
        self.save()
    
    def last_bid(self):
        for bid in self.game.current_round.all_bids():
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
    
class CardInHand(models.Model):
    
    isplaying = models.ForeignKey(IsPlaying)
    card = models.ForeignKey(Card)
            
class IsInDeck(models.Model):
    
    card = models.ForeignKey(Card)
    game = models.ForeignKey(Game)
    
    # The place that this card has in the deck (0 is the bottom card)
    ordinal = models.PositiveSmallIntegerField()
    
    
    


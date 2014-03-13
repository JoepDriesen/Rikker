from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from portal.models import Game, Round, IsPlaying, Card
from portal.forms import MakeBidForm, PickTrumpSuitAndMateForm,\
    PickTrumpSuitForm, StartGameForm
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.http.response import HttpResponse, Http404
import json
from django.template.loader import render_to_string

@login_required
def portal(request):
    start_game_form = StartGameForm()
    isplayings = IsPlaying.objects.select_related('game', 'player').prefetch_related('game__isplaying_set__player').filter(player=request.user)
    
    pending_games = []
    invitations = []
    games = []
    
    for isplaying in isplayings:
        if isplaying.abandoned:
            continue
        elif not isplaying.accepted:
            invitations.append(isplaying.game)
        elif not isplaying.game.deck_initialized:
            pending_games.append(isplaying.game)
        else:
            games.append(isplaying.game)
    
    return render(request, 'portal/portal.html', {'start_game_form': start_game_form,
                                                  'pending_games': pending_games,
                                                  'invitations': invitations,
                                                  'games': games})

@login_required
def new_game(request):
    if request.method != 'POST':
        raise PermissionDenied()
    start_game_form = StartGameForm(request.POST)
    if start_game_form.is_valid():
        players = start_game_form.get_players_to_invite()
        players.insert(0, request.user)
        Game.objects.start_game(players)
    else:
        messages.add_message(request, messages.ERROR, 'Could not start a new game, please try again.')
    return redirect('portal')

@login_required
def accept_invitation(request, game_id):
    try:
        isplaying = IsPlaying.objects.get(game__id=game_id, player=request.user, accepted=False, abandoned=False)
    except IsPlaying.DoesNotExist:
        raise PermissionDenied("You cannot accept this invitation because you were not invited to this game")
    isplaying.accepted = True
    isplaying.save()
    return redirect('portal')

@login_required
def decline_invitation(request, game_id):
    try:
        isplaying = IsPlaying.objects.get(game__id=game_id, player=request.user, accepted=False, abandoned=False)
    except IsPlaying.DoesNotExist:
        raise PermissionDenied("You cannot decline this invitation because you were not invited to this game")
    isplaying.abaondoned = True
    isplaying.save()
    return redirect('portal')

@login_required
def cancel_game(request, game_id):
    try:
        game = Game.objects.get(id=game_id, deck_initialized=False)
        if game.isplaying_set.get(seat=0).player != request.user:
            raise PermissionDenied("You cannot cancel a game you didn't start.")
        game.delete()
    except Game.DoesNotExist:
        raise PermissionDenied("That game does not exist")
    return redirect('portal')

@login_required
def start_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if not game.deck_initialized:
        game.initialize_deck()
    return redirect('game', game_id)

@login_required
def game(request, game_id):
    try:
        game = Game.objects.select_related('current_round__dealer', 'current_round__next_player_to_bid', 'current_round__highest_bid__player', 'current_round__next_player_to_play').prefetch_related('isplaying_set__player', 'isplaying_set__cards', 'current_round__bids__player').get(id=game_id)
    except Game.DoesNotExist:
        raise Http404()
    args = {'game': game}
    if game.current_round is not None and game.current_round.next_player_to_bid == request.user:
        bid_form = MakeBidForm()
        args['bid_form'] = bid_form
    elif game.current_round is not None and game.current_round.highest_bid is not None and not game.current_round.playing and game.current_round.highest_bid.player == request.user:
        form_info = game.current_round.highest_bid.get_trump_pick_form()
        args[form_info[0]] = form_info[1]()
    return render(request, 'portal/game.html', args)

@login_required
def abandon_game(request, game_id):
    try:
        isplaying = IsPlaying.objects.get(game__id=game_id, player=request.user, abandoned=False)
    except IsPlaying.DoesNotExist:
        raise PermissionDenied("You cannot abandon this game because you are not part of it")
    isplaying.abandoned = True
    isplaying.save()
    return redirect('portal')

@login_required
def start_round(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    game.start_round()
    return redirect('game', game_id)

@login_required
@csrf_exempt
def place_bid(request, game_id):
    if request.method == "POST":
        bid_form = MakeBidForm(request.POST)
        if bid_form.is_valid():
            game = get_object_or_404(Game, id=game_id)
            try:
                game.current_round.place_bid(request.user, bid_form.cleaned_data['bid'])
            except Round.BidTooLowException:
                messages.add_message( request, messages.SUCCESS, 'Please bid higher than the currently placed bid.')
            except Round.CannotPassException:
                messages.add_message( request, messages.SUCCESS, 'You are the last player to bid and every other player has passed. You must place a bid.')
            return redirect('game', game_id)
    raise PermissionDenied()

@login_required
@csrf_exempt
def pick_trump_and_mate(request, game_id):
    if request.method == "POST":
        trump_and_mate_form = PickTrumpSuitAndMateForm(request.POST)
        if trump_and_mate_form.is_valid():
            all_good = False
            game = get_object_or_404(Game, id=game_id)
            
            trump = trump_and_mate_form.cleaned_data['trump_suit']
            mate = trump_and_mate_form.cleaned_data['mate_suit']
            mate_cardnumber = None
            
            # Check if the wanted mate is possible
            if trump == mate:
                messages.add_message( request, messages.SUCCESS, 'You cannot pick the trump suit as mate.')
            else:
                isplaying = IsPlaying.objects.get(game=game, player=request.user)
                try:
                    mate_cardnumber = 1
                    isplaying.cards.get(suit=mate, number=1)
                    # Player has the ace of the chosen mate, check if he has 4 aces
                    if len(isplaying.cards.filter(number=1)) >= 4:
                        mate_cardnumber = 13
                        isplaying.cards.get(suit=mate, number=13)
                        # Player has the king of the chosen mate, check if he has 4 kings
                        if len(isplaying.cards.filter(number=13)) >= 4:
                            mate_cardnumber = 12
                            isplaying.cards.get(suit=mate, number=12)
                            # Player has the queen of the chosen mate, check if he has 4 queens
                            if len(isplaying.cards.filter(number=12)) >= 4:
                                mate_cardnumber = 11
                                isplaying.cards.get(suit=mate, number=11)
                                # Player has the jack of the chosen mate
                                messages.add_message( request, messages.SUCCESS, 'You must pick a mate suit of which you do not have the jack.')
                            else:
                                messages.add_message( request, messages.SUCCESS, 'You must pick a mate suit of which you do not have the queen.')
                        else:
                            messages.add_message( request, messages.SUCCESS, 'You must pick a mate suit of which you do not have the king.')
                    else:
                        messages.add_message( request, messages.SUCCESS, 'You must pick a mate suit of which you do not have the ace.')
                except Card.DoesNotExist:
                    if isplaying.cards.filter(suit=mate).exists():
                        # You can pick this mate suit
                        all_good = True
                    else:
                        try:
                            for card in isplaying.cards.distinct('suit'):
                                isplaying.cards.get(suit=card.suit, number=1)
                            # You can blind pick this mate suit
                            mate_cardnumber = 1
                            all_good = True
                        except Card.DoesNotExist:
                            messages.add_message( request, messages.SUCCESS, 'You must pick a mate suit of which you have at least one card.')
                            
            if all_good:
                game.current_round.finalize_bid(trump, mate, mate_cardnumber)
                
            return redirect('game', game_id)
    raise PermissionDenied()

@login_required
@csrf_exempt
def pick_trump(request, game_id):
    if request.method == "POST":
        trump_form = PickTrumpSuitForm(request.POST)
        if trump_form.is_valid():
            game = get_object_or_404(Game, id=game_id)
            game.current_round.highest_bid.trump_suit = trump_form.cleaned_data['trump_suit']
            return redirect('game', game_id)
    raise PermissionDenied()
    
@login_required
def play_card(request, game_id, card_identifier):
    game = get_object_or_404(Game, id=game_id)
    card = Card.objects.get_by_identifier(card_identifier)
    try:
        game.current_round.play_card(request.user, card)
    except Round.CantPlayThatCardException:
        messages.add_message( request, messages.SUCCESS, 'You must follow suit.')
    return redirect('game', game_id)

@login_required
def collect_trick(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    game.current_round.collect_current_trick(request.user)
    return redirect('game', game_id)



@csrf_exempt
def get_update(request):
    if request.method != 'POST' or not request.is_ajax():
        raise PermissionDenied()
    
    isplaying = get_object_or_404(IsPlaying, game__id=request.POST['game'], player__id=request.POST['player'])
        
    if isplaying.needs_update:
        isplaying.needs_update = False
        isplaying.save()
        
        game = isplaying.game
        players = render_to_string('includes/players.html', {'user': request.user,
                                                             'game': game})
        
        args = {'user': request.user,
                'game': game}
        if game.current_round is not None and game.current_round.next_player_to_bid == request.user:
            bid_form = MakeBidForm()
            args['bid_form'] = bid_form
        elif game.current_round is not None and game.current_round.highest_bid is not None and not game.current_round.playing and game.current_round.highest_bid.player == request.user:
            form_info = game.current_round.highest_bid.get_trump_pick_form()
            args[form_info[0]] = form_info[1]()
        playfield = render_to_string('includes/playfield.html', args)
        
        extra_info = render_to_string('includes/extra_info.html', {'game': game})
        
        messages = render_to_string('includes/messages.html')
        
        json_data = json.dumps({'update': True,
                                'players': players,
                                'playfield': playfield,
                                'extra_info': extra_info,
                                'messages': messages})
        return HttpResponse(json_data, mimetype='application/json')
    return HttpResponse(json.dumps({'update': False}), mimetype='application/json')
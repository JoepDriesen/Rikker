from django.contrib.auth.decorators import login_required
from django.http.response import Http404, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from game.models import IsPlaying, Game, Round, Card, Trick, GameException
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from game.forms import MakeBidForm, PickTrumpSuitAndMateForm, PickTrumpSuitForm

@login_required
def game(request, game_id):
    try:
        game = Game.objects.infofetch(game_id)
    except Game.DoesNotExist:
        raise Http404()
    
    game.advance()
    
    isplaying = get_object_or_404(IsPlaying, game=game, player=request.user)
    
    if isplaying.needs_update:
        isplaying.needs_update = False
        isplaying.save()
        
    
    context = {'game': game}
    
    if game.current_state() is Game.DURING_ROUND and game.current_round.current_phase() is Round.BIDDING_PHASE:
        if game.current_round.next_player_to_bid() == request.user:
            bid_form = MakeBidForm(current_round=game.current_round)
            context['bid_form'] = bid_form
        
    elif game.current_state() is game.DURING_ROUND and game.current_round.current_phase() is Round.FINALIZE_BIDDING_PHASE \
     and game.current_round.highest_bid.player == request.user:
        FinalizeBidForm = game.current_round.highest_bid.get_bidding_finalize_form()
        context['finalize_bid_form'] = FinalizeBidForm()
        
    context['g'] = Game
    context['r'] = Round
    context['t'] = Trick
    
    return render(request, 'game/game.html', context)

@login_required
def abandon_game(request, game_id):
    try:
        isplaying = IsPlaying.objects.get(game__id=game_id, player=request.user, abandoned=False)
    except IsPlaying.DoesNotExist:
        raise PermissionDenied("You cannot abandon this game because you are not part of it")
    
    isplaying.abandon()
    return redirect('portal')

@login_required
def start_round(request, game_id):
    try:
        game = Game.objects.infofetch(game_id)
    except Game.DoesNotExist:
        raise Http404
    
    try:
        game.start_round()
    except GameException as e:
        print(e.message)
    
    return redirect('game', game_id)

@login_required
def place_bid(request, game_id):
    try:
        game = Game.objects.infofetch(game_id)
    except Game.DoesNotExist:
        raise Http404
    
    if request.method == "POST":
        try:
            bid_form = MakeBidForm(request.POST)
            if bid_form.is_valid():
                try:
                    game.current_round.place_bid(request.user, bid_form.cleaned_data['bid'])
                except Round.BadBidException as e:
                    messages.add_message(request, messages.SUCCESS, e.message)
            else:
                messages.add_message(request, messages.WARNING, bid_form.errors)
        
        except GameException as e:
            print(e.message)
            
        return redirect('game', game_id)
    raise PermissionDenied()

@login_required
def pick_trump_and_mate(request, game_id):
    if request.method == "POST":
        try:
            trump_and_mate_form = PickTrumpSuitAndMateForm(request.POST)
            if trump_and_mate_form.is_valid():
                try:
                    game = Game.objects.infofetch(game_id)
                except Game.DoesNotExist:
                    raise Http404
                
                trump = trump_and_mate_form.cleaned_data['trump_suit']
                mate = trump_and_mate_form.cleaned_data['mate_suit']
                
                try:
                    game.current_round.finalize_bid(request.user, trump, mate)
                except Round.BadBidException as e:
                    messages.add_message(request, messages.WARNING, e.message)
            else:
                messages.add_message(request, messages.WARNING, trump_and_mate_form.errors)
        
        except GameException as e:
            print(e.message)
            
        return redirect('game', game_id)
                
    raise PermissionDenied()

@login_required
def pick_trump(request, game_id):
    if request.method == "POST":
        try:
            trump_form = PickTrumpSuitForm(request.POST)
            if trump_form.is_valid():
                try:
                    game = Game.objects.infofetch(game_id)
                except Game.DoesNotExist:
                    raise Http404
                
                trump = trump_form.cleaned_data['trump_suit']
                
                try:
                    game.current_round.finalize_bid(request.user, trump)
                except Round.BadBidException as e:
                    messages.add_message(request, messages.WARNING, e.msg)
            else:
                messages.add_message(request, messages.WARNING, trump_form.errors)
        
        except GameException as e:
            print(e.message)
            
        return redirect('game', game_id)
        
    raise PermissionDenied()
    
@login_required
def play_card(request, game_id, card_identifier):
    try:
        game = Game.objects.infofetch(game_id)
    except Game.DoesNotExist:
        raise Http404
    
    card = Card.objects.get_by_identifier(card_identifier)
    
    try:
        game.current_round.current_trick().play_card(request.user, card)
    except Trick.BadPlayException as e:
        messages.add_message( request, messages.SUCCESS, e.message)
    except GameException as e:
        print(e.message)
        
    return redirect('game', game_id)

@login_required
def collect_trick(request, game_id):
    try:
        game = get_object_or_404(Game, id=game_id)
        game.current_round.current_trick().collect(request.user)
    
    except GameException as e:
        print(e.message)
        
    return redirect('game', game_id)



@csrf_exempt
def get_update(request):
    if request.method != 'POST' or not request.is_ajax():
        raise PermissionDenied()
    
    isplaying = get_object_or_404(IsPlaying, game__id=request.POST['game'], player__id=request.POST['player'])
        
    if isplaying.needs_update:
        isplaying.needs_update = False
        isplaying.save()
        
        json_data = json.dumps({'update': True})
        return HttpResponse(json_data, mimetype='application/json')
    
    return HttpResponse(json.dumps({'update': False}), mimetype='application/json')

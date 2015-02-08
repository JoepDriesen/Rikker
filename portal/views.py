from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from game.models import Game, IsPlaying
from portal.forms import NewGameForm
from django.core.exceptions import PermissionDenied
from django.contrib import messages

@login_required
def portal(request):
    start_game_form = NewGameForm(creating_user=request.user)
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
    
    start_game_form = NewGameForm(request.user, request.POST)
    if start_game_form.is_valid():
        players = start_game_form.get_players_to_invite()
        players.insert(0, request.user)
        Game.objects.start_game(players)
    else:
        messages.add_message(request, messages.ERROR, 'Could not start a new game, please try again. Error: {}'.format(start_game_form.errors))
    return redirect('portal')

@login_required
def accept_invitation(request, game_id):
    try:
        isplaying = IsPlaying.objects.get(game__id=game_id, player=request.user, accepted=False, abandoned=False)
    except IsPlaying.DoesNotExist:
        raise PermissionDenied("You cannot accept this invitation because you were not invited to this game.")
    
    isplaying.accepted = True
    isplaying.save()
    return redirect('portal')

@login_required
def decline_invitation(request, game_id):
    try:
        isplaying = IsPlaying.objects.get(game__id=game_id, player=request.user, accepted=False, abandoned=False)
    except IsPlaying.DoesNotExist:
        raise PermissionDenied("You cannot decline this invitation because you were not invited to this game.")
    
    isplaying.abandoned = True
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
    game.initialize_deck()
    
    return redirect('game', game_id)

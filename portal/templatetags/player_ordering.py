from django import template

register = template.Library()

@register.simple_tag
def seat_number(game, isplaying, player_looking_at_screen):
    if isplaying.player == player_looking_at_screen:
        return 0
    
    for loop_isplaying in game.isplaying_set.all():
        if loop_isplaying.player == player_looking_at_screen:
            player_seat = loop_isplaying.seat
    
    if isplaying.seat > player_seat:
        return isplaying.seat - player_seat
    return 4 - (player_seat - isplaying.seat)

@register.simple_tag
def current_trick_display(game, player_looking_at_screen):
    result = '<div id="current-trick-display">'
    
    for loop_isplaying in game.isplaying_set.all():
        if loop_isplaying.player == player_looking_at_screen:
            player_seat = loop_isplaying.seat
            
    for card in game.current_round.current_trick.playedintrick_set.all():
        this_guys_seat = game.isplaying_set.get(player=card.played_by).seat
        if this_guys_seat >= player_seat:
            relative_seat_number = (this_guys_seat - player_seat) + 1
        else:
            relative_seat_number = (4 - (player_seat - this_guys_seat)) + 1
        result += '<img src="/static/%s" id="trick-card-%s" />' % (card.card.image_file(), relative_seat_number)
    result += '</div>'
    return result
from django.contrib import admin
from django.contrib.auth import get_user_model
from game.models import Game, Card, IsPlaying, IsInDeck, Round, Bid, Trick,\
    PlayedInTrick

class IsPlayingInline(admin.TabularInline):
    model = IsPlaying
    max_num = 4

class IsInDeckInline(admin.TabularInline):
    model = IsInDeck

class GameAdmin(admin.ModelAdmin):
    model = Game
    inlines = (IsPlayingInline, IsInDeckInline)

class BidInline(admin.TabularInline):
    model = Bid
    
class TrickInline(admin.TabularInline):
    readonly_fields = ('winner', )
    fields = ('round', 'number', 'requested_suit', 'collected', 'winner')
    model = Trick
    
class RoundAdmin(admin.ModelAdmin):
    model = Round
    inlines = (BidInline, TrickInline, )

class PlayedInTrickInline(admin.TabularInline):
    model = PlayedInTrick

class TrickAdmin(admin.ModelAdmin):
    readonly_fields = ('winner', )
    fields = ('round', 'number', 'requested_suit', 'collected', 'winner')
    inlines = (PlayedInTrickInline, )
    
admin.site.register(get_user_model())
admin.site.register(Game, GameAdmin)
admin.site.register(Card)
admin.site.register(Round, RoundAdmin)
admin.site.register(Trick, TrickAdmin)
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^(\d+)/$', 'game.views.game', name='game'),
    url(r'^abandon/(\d+)/$', 'game.views.abandon_game', name='abandon_game'),
    url(r'^startround/(\d+)/$', 'game.views.start_round', name='start_round'),
    url(r'^placebid/(\d+)/$', 'game.views.place_bid', name='place_bid'),
    url(r'^picktrumpandmate/(\d+)/$', 'game.views.pick_trump_and_mate', name='pick_trump_and_mate'),
    url(r'^picktrump/(\d+)/$', 'game.views.pick_trump', name='pick_trump'),
    url(r'^playcard/(\d+)/(\D\d+)/$', 'game.views.play_card', name='play_card'),
    url(r'^collecttrick/(\d+)/$', 'game.views.collect_trick', name='collect_trick'),
    
    url(r'^getupdate/$', 'game.views.get_update', name='get_update'),
)

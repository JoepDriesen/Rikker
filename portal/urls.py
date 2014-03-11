from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'portal.views.portal', name='portal'),
    url(r'^newgame/$', 'portal.views.new_game', name='new_game'),
    url(r'^acceptinv/(\d*)/$', 'portal.views.accept_invitation', name='accept_invitation'),
    url(r'^declineinv/(\d*)/$', 'portal.views.decline_invitation', name='decline_invitation'),
    url(r'^cancelgame/(\d*)/$', 'portal.views.cancel_game', name='cancel_game'),
    url(r'^startgame/(\d*)/$', 'portal.views.start_game', name='start_game'),
    url(r'^game/(\d*)/$', 'portal.views.game', name='game'),
    url(r'^abandongame/(\d*)/$', 'portal.views.abandon_game', name='abandon_game'),
    url(r'^startround/(\d*)/$', 'portal.views.start_round', name='start_round'),
    url(r'^placebid/(\d*)/$', 'portal.views.place_bid', name='place_bid'),
    url(r'^picktrumpandmate/(\d*)/$', 'portal.views.pick_trump_and_mate', name='pick_trump_and_mate'),
    url(r'^picktrump/(\d*)/$', 'portal.views.pick_trump', name='pick_trump'),
    url(r'^playcard/(\d*)/(\D\d*)/$', 'portal.views.play_card', name='play_card'),
    url(r'^collecttrick/(\d*)/$', 'portal.views.collect_trick', name='collect_trick'),
    
    url(r'^getupdate/$', 'portal.views.get_update', name='get_update'),
)

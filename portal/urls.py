from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'portal.views.portal', name='portal'),
    url(r'^newgame/$', 'portal.views.new_game', name='new_game'),
    url(r'^acceptinv/(\d*)/$', 'portal.views.accept_invitation', name='accept_invitation'),
    url(r'^declineinv/(\d*)/$', 'portal.views.decline_invitation', name='decline_invitation'),
    url(r'^cancelgame/(\d*)/$', 'portal.views.cancel_game', name='cancel_game'),
    url(r'^startgame/(\d*)/$', 'portal.views.start_game', name='start_game'),
)

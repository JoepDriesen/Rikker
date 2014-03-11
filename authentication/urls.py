from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^login/$', 'authentication.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/login/'}, name='logout'),
    url(r'^register/$', 'authentication.views.register', name='register'),
)

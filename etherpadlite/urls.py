
from django.conf.urls import patterns, url

import etherpadlite
import django



urlpatterns = patterns(
    '',
    url(r'^pad/(?P<pk>\d+)/$', etherpadlite.views.pad, name="pad"),
    url(r'^create/(?P<pk>\d+)/$', etherpadlite.views.padCreate, name="create"),
    url(r'^delete/(?P<pk>\d+)/$', etherpadlite.views.padDelete, name="delete"),
    url(r'^group/create/$', etherpadlite.views.groupCreate, name="groupcreate"),
    url(r'^profile/$', etherpadlite.views.profile, name="etherpad-profile"),

    url(r'^$', django.contrib.auth.views.login,
    url(r'^pad/(?P<pk>\d+)/$', etherpadlite.views.pad, name="pad"),
    url(r'^create/(?P<pk>\d+)/$', etherpadlite.views.padCreate, name="create"),
    url(r'^delete/(?P<pk>\d+)/$', etherpadlite.views.padDelete, name="delete"),
    url(r'^group/create/$', etherpadlite.views.groupCreate, name="groupcreate"),
    url(r'^profile/$', etherpadlite.views.profile, name="etherpad-profile"),
)

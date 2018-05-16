
from django.conf.urls import url, include

from etherpadlite import views
from django.contrib.auth.views import login, logout
import django


app_name = 'etherpadlite'
urlpatterns = [
    #url(r'^$', views.padIndex ,name="index"),

    url(r'^pad/(?P<pk>\d+)/$', views.pad, name="pad"),
    url(r'^pad/(?P<pk>\d+)/edit/$', views.padSettings, name="padsettings"),
    url(r'^pad/(?P<pk>\d+)/delete/$', views.padDelete, name="delete"),
    url(r'^pad/(?P<pk>\d+)/duplicate/$', views.padDuplicate, name="duplicate"),
    
    url(r'^create/(?P<pk>\d+)/$', views.padCreate, name="create"),
    url(r'^search/$', views.padSearch, name="search"),

    url(r'^~create/$', views.groupCreate, name="groupcreate"),
    
    url(r'^profile/$', views.profile, name="profile"),
    
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),

    url(r'^(?P<group>[a-z0-9_-]+)/', include([
        url(r'^$', views.groupMapper, name='groupmapper'),
        url(r'^~search$', views.groupSearch, name='groupsearch'),
        url(r'^~edit$', views.groupSettings, name='groupsettings'),
        url(r'^(?P<show>[\w ]+)/$', views.padMapper, name='padmapper'),
    ])),
    
]


from django.conf.urls import url

from etherpadlite import views
from django.contrib.auth.views import login, logout
import django


app_name = 'etherpadlite'
urlpatterns = [
    url(r'^pad/(?P<pk>\d+)/$', views.pad, name="pad"),
    url(r'^padsettings/(?P<pk>\d+)/$', views.padSettings, name="padsettings"),
    url(r'^create/(?P<pk>\d+)/$', views.padCreate, name="create"),
    url(r'^delete/(?P<pk>\d+)/$', views.padDelete, name="delete"),
    url(r'^group/create/$', views.groupCreate, name="groupcreate"),
    url(r'^profile/$', views.profile, name="profile"),
    
    url(r'^login/$', views.login_view, name='login'),
    url(r'^logout/$', views.logout_view, name='logout'),
]

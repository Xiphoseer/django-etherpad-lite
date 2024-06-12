from django.conf.urls import url, include
from . import views


app_name = 'padman'
urlpatterns = [
    url(r'^$', views.IndexView.as_view() ,name="index"),
    url(r'^pad/(?P<pk>\d+)/', include([
        url(r'^$', views.PadView.as_view(), name="pad"),
        url(r'^edit/$', views.PadSettingsView.as_view(), name="padsettings"),
        url(r'^delete/$', views.padDelete, name="delete"),
        url(r'^duplicate/$', views.padDuplicate, name="duplicate"),
        url(r'^raw/$', views.RawPadView.as_view(), name="rawpad"),
    ])),

    url(r'^search/$', views.padSearch, name="search"),
    url(r'^~create/$', views.groupCreate, name="groupcreate"),

    url(r'^(?P<category>[A-Za-z0-9_-]+)/', include([
        url(r'^$', views.CategoryView.as_view(), name='category-slug'),
        url(r'^~newpad/$', views.PadCreateView.as_view(), name="create"),
        url(r'^~search/$', views.groupSearch, name='groupsearch'),
        url(r'^~edit/$', views.CategorySettingsView.as_view(), name='category-settings'),
        url(r'^~import/$', views.GroupPadImportView.as_view(), name='grouppadimport'),
        url(r'^(?P<show>[\w ]+)/$', views.PadMapperView.as_view(), name='padmapper'),
    ])),
]

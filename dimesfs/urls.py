from django.conf.urls import patterns, url

from dimesfs import views

urlpatterns = patterns('',
        url(r'fslist$', views.fslist, name='fslist'),
        url(r'^$', views.index, name='index'),
        )

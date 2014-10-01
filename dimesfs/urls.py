from django.conf.urls import patterns, url

from dimesfs import views

urlpatterns = patterns('',
        url(r'fslist$', views.fslist, name='fslist'),
        url(r'dirflist$', views.dirflist, name='dirflist'),
        url(r'upload$', views.upload, name='upload'),
        url(r'^$', views.index, name='index'),
        )

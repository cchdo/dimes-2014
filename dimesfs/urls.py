from django.conf.urls import patterns, include, url
from django.conf import settings

from dimesfs import views

urlpatterns = patterns('',
        url(r'fslist$', views.fslist, name='fslist'),
        url(r'dirflist$', views.dirflist, name='dirflist'),
        url(r'upload$', views.upload, name='upload'),
        url(r'delete$', views.delete, name='delete'),
        url(r'download/(?P<uri_frag>.+)$', views.download, name='download'),
        url(r'^$', views.index, name='index'),
        )

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'', include('django.contrib.staticfiles.urls')),
    )

from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from dimes import settings

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'dimes.views.index', name='index'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'', include('django.contrib.staticfiles.urls')),
    )

from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from dimes import settings

urlpatterns = patterns('',
    # Examples:
    url(r'about$', 'dimes.views.about', name='about'),
    url(r'components$', 'dimes.views.components', name='components'),
    url(r'contact$', 'dimes.views.contact', name='contact'),
    url(r'cruises$', 'dimes.views.cruises', name='cruises'),
    url(r'^$', 'dimes.views.index', name='index'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'', include('django.contrib.staticfiles.urls')),
    )

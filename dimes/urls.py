from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from dimes import settings

urlpatterns = patterns('',
    # Examples:
    url(r'components$', 'dimes.views.components', name='components'),
    url(r'people$', 'dimes.views.people', name='people'),
    url(r'publications$', 'dimes.views.publications', name='publications'),
    url(r'cruises$', 'dimes.views.fieldwork', name='fieldwork'),
    url(r'data$', 'dimes.views.data', name='data'),
    url(r'fieldwork$', 'dimes.views.fieldwork', name='fieldwork'),
    url(r'cruise_data/(\w+)$', 'dimes.views.cruise_page', name='cruise_data'),
    url(r'cruise_reports$', 'dimes.views.cruise_reports', name='cruise_reports'),
    url(r'media$', 'dimes.views.media', name='media'),
    url(r'outreach$', 'dimes.views.outreach', name='outreach'),
    url(r'^$', 'dimes.views.index', name='index'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'', include('django.contrib.staticfiles.urls')),
    )

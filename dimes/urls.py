from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    # Examples:
    url(r'components$', 'dimes.views.components', name='components'),
    url(r'people$', 'dimes.views.people', name='people'),
    url(r'publications$', 'dimes.views.publications', name='publications'),
    url(r'cruises$', 'dimes.views.fieldwork', name='fieldwork'),
    url(r'data$', 'dimes.views.data', name='data'),
    url(r'fieldwork$', 'dimes.views.fieldwork', name='fieldwork'),
    url(r'cruise_data/([A-Za-z0-9\.]+)$', 'dimes.views.cruise_page', name='cruise_data'),
    url(r'cruise_reports$', 'dimes.views.cruise_reports', name='cruise_reports'),
    url(r'data_policy$', 'dimes.views.data_policy', name='data_policy'),
    url(r'outreach$', 'dimes.views.outreach', name='outreach'),
    url(r'calendar$', 'dimes.views.calendar', name='calendar'),
    url(r'^dimesfs/', include('dimesfs.urls')),
    url(r'^$', 'dimes.views.index', name='index'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^login/$', 'django.contrib.auth.views.login', {
        'template_name': 'login.html'}),
    url(r'^logout/$', 'dimes.views.logout'),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'', include('django.contrib.staticfiles.urls')),
    )

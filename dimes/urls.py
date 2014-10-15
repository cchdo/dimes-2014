from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
admin.autodiscover()

from django.conf import settings

urlpatterns = patterns('',
    url(r'^dimesfs/', include('dimesfs.urls')),

    url(r'^login/$', 'django.contrib.auth.views.login', {
        'template_name': 'login.html'}),
    url(r'^logout/$', 'dimes.views.logout'),

)

urlpatterns += i18n_patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('cms.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'', include('django.contrib.staticfiles.urls')),
    )

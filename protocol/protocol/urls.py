"""protocol URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

import django.contrib.auth.views as auth_views

import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', RedirectView.as_view(url=reverse_lazy('protocol_login'), permanent=True),  name='protocol_root'),
    url(r'^protocol/login/$', auth_views.login, {'template_name':'protocol/protocol_login.html'}, name='protocol_login'),
    url(r'^protocol/logout/$', auth_views.logout_then_login, {'login_url':reverse_lazy('where')}, name='protocol_logout'),
]

urlpatterns += [
    url(r'^api/protocol/protocols/$', views.ProtocolListAPIView.as_view(), name='api_protocol_list'),
    url(r'^api/protocol/(.+)/$', views.ProtocolDetailAPIView.as_view(), name='api_protocol_detail'),
]

urlpatterns += [
    url(r'^protocol/$', views.MainView.as_view(), name='main'),
    url(r'^protocol/addEditProtocol/$', views.AddEditProtocolView.as_view(), name='add_edit_protocol'),
    url(r'^protocol/saveProtocol/$', views.SaveProtocolAPIView.as_view(), name='save_protocol'),
    url(r'^protocol/protocols/$', views.ProtocolListView.as_view(), name='protocol_list'),
    url(r'^protocol/(?P<protocol>.+)/$', views.ProtocolDetailView.as_view(), name='protocol_detail'),
]


urlpatterns = format_suffix_patterns(urlpatterns)


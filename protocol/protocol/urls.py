"""protocol URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class_based views
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
from forms import UserAuthenticationForm
import django.contrib.auth.views as auth_views

import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^whereToGo/$', views.where_to_go, name='where'),
    url(r'^$', RedirectView.as_view(url=reverse_lazy('login'), permanent=True),  name='protocol_root'),
    url(r'^protocol/registration/$', views.register, name='registration'),
    url(r'^protocol/login/$', views.protocol_login, {'template_name':'protocol/login.html', 'authentication_form':UserAuthenticationForm}, name='login'),
    url(r'^protocol/logout/$', auth_views.logout_then_login, {'login_url':reverse_lazy('where')}, name='logout'),
    url(r'^protocol/userprofile/$', views.user_profile_view, name='user_profile'),
]

urlpatterns += [
    url(r'^password_reset/$', auth_views.password_reset, {
        'template_name': 'protocol/reset_password/password_reset.html',
        'email_template_name': 'protocol/reset_password/password_reset.txt',
        'post_reset_redirect': reverse_lazy('protocol_password_reset_sent'),
        }, name="protocol_password_reset"),
    url(r'^password_reset_confirm/(?P<uidb64>\w*)\|(?P<token>[\-a-zA-Z0-9]*)$', auth_views.password_reset_confirm, {
        'template_name': 'protocol/reset_password/password_reset_confirm.html',
        'post_reset_redirect': reverse_lazy('protocol_password_reset_complete'),
        }, name="protocol_password_reset_confirm"),
    url(r'^password_reset_sent/$', auth_views.password_reset_done, {
        'template_name': 'protocol/reset_password/password_reset_sent.html',
        }, name="protocol_password_reset_sent"),
    url(r'^password_reset_complete/$', auth_views.password_reset_complete, {
        'template_name': 'protocol/reset_password/password_reset_complete.html',
        }, name="protocol_password_reset_complete"),
    url(r'^account_confirm_retry/$', auth_views.password_reset, {
        'template_name': 'protocol/reset_password/password_reset.html',
        'email_template_name': 'protocol/account_password.html',
        'post_reset_redirect': reverse_lazy('protocol_password_reset_sent'),
        }, name="account_confirm_retry"),
]


urlpatterns += [
    url(r'^api/protocol/protocols/$', views.api_protocol_list, name='api_protocol_list'),
    url(r'^api/protocol/(.+)/$', views.api_protocol_detail, name='api_protocol_detail'),
]

urlpatterns += [
    url(r'^protocol/sendSharedProtocol/$', views.send_shared_protocol, name='send_shared_protocol'),
    url(r'^protocol/processSharedProtocol/$', views.process_shared_protocol, name='process_shared_protocol'),
]

urlpatterns += [
    url(r'^protocol/$', views.main, name='main'),
    url(r'^protocol/searchProtocol/$', views.search_protocol, name='search_protocol'),
    url(r'^protocol/addEditProtocol/$', views.add_edit_protocol, name='add_edit_protocol'),
    url(r'^protocol/saveProtocol/$', views.save_protocol, name='save_protocol'),
    url(r'^protocol/protocols/$', views.protocol_list, name='protocol_list'),
    url(r'^protocol/(?P<protocol>.+)/$', views.protocol_detail, name='protocol_detail'),
]



urlpatterns = format_suffix_patterns(urlpatterns)


from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from django.core.urlresolvers import reverse_lazy

import protocol_api.views as views

urlpatterns = [
    url(r'^api/protocol/protocols/$', views.api_protocol_list, name='api_protocol_list'),
    url(r'^api/protocol/(?P<protocol_id>[1-9]+)/$', views.api_protocol_detail, name='api_protocol_detail'),
    url(r'^api/protocol/experiments/$', views.api_experiment_list, name='api_experiment_list'),
    url(r'^api/protocol/experiment/(?P<experiment_id>[1-9]+)/$', views.api_experiment_detail, name='api_experiment_detail'),
]
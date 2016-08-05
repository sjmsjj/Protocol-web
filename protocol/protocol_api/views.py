from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView, DetailView, ListView, UpdateView
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404, render
from django.core.urlresolvers import reverse_lazy
from django.db.models import Count, Max
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import generics
from rest_framework.response import Response

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login as login_view, logout_then_login
from django.views.decorators.cache import never_cache
from django.template.loader import render_to_string

from django.core.urlresolvers import reverse
from django.db.models import Q, F, Func, Sum
from django.db.models.functions import Substr
from collections import defaultdict
import django_filters
import json
import copy
import re
import itertools
import datetime
from django.utils import timezone
from protocol.models import Protocol, Experiment, Step, ProtocolUser, SharedProtocol
from protocol_api.serializers import StepSerializer, ProtocolSerializer, ExperimentSerializer
from django.contrib.auth.forms import UserCreationForm


class SaveProtocolAPIView(APIView):
	def post(self, request, *args, **kwargs):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		request.data['user'] = user
		edited_protocol_name = request.data.pop('edited_protocol_name')
		new_protocol_name = request.data.get('name')
		edited_protocol = []
		experiments = []
		if edited_protocol_name:
			edited_protocol = user.get_protocol(edited_protocol_name)
			for experiment in edited_protocol.get_experiments():
				experiments.append(experiment)
			edited_protocol = [edited_protocol]
			user.get_protocol(edited_protocol_name).delete()

		serializer = ProtocolSerializer(data=request.data)
		if serializer.is_valid():
			new_protocol = None
			if edited_protocol:
				serializer.save()
				new_protocol = user.get_protocol(new_protocol_name)
				for experiment in experiments:
					experiment.protocol = new_protocol
					experiment.save()
				new_protocol.ninstance = len(experiments)
				new_protocol.save()
			else:
				new_protocol = serializer.save()
			new_protocol.last_updated = datetime.datetime.today()
			new_protocol.save() 
			return HttpResponse('success')
		else:
			edited_protocol[0].save()
	        for experiment in experiments:
	        	experiment.protocol = edited_protocol
	        	experiment.save()
	        return HttpResponse('Cannot save the protocol')

save_protocol = login_required(SaveProtocolAPIView.as_view())

class ProtocolListAPIView(APIView):
	def get(self, request, format=None):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		protocols = user.get_protocols()
		serializer = ProtocolSerializer(protocols, many=True)
		return Response(serializer.data)

api_protocol_list = login_required(ProtocolListAPIView.as_view())

class ProtocolDetailAPIView(APIView):
	def get(self, request, protocol_id, format=None):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		protocol = user.get_protocol(protocol_id)
		serializer = ProtocolSerializer([protocol], many=True)
		return Response(serializer.data)

api_protocol_detail = login_required(ProtocolDetailAPIView.as_view())


class ExperimentListAPIView(APIView):
	def get(self, request, format=None):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		experiments = user.get_experiments()
		serializer = ExperimentSerializer(experiments, many=True)
		return Response(serializer.data)

api_experiment_list = login_required(ExperimentListAPIView.as_view())

class ExperimentDetailAPIView(APIView):
	def get(self, request, experiment_id, format=None):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		experiment = user.get_experiment(experiment_id)
		serializer = ExperimentSerializer([experiment], many=True)
		return Response(serializer.data)

api_experiment_detail = login_required(ExperimentDetailAPIView.as_view())
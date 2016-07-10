from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView, DetailView, ListView
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response, get_object_or_404, render
from django.db.models import Count, Max
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework import generics
from rest_framework.response import Response

from django.core.urlresolvers import reverse
from django.db.models import Q, F, Func, Sum
from django.db.models.functions import Substr
from collections import defaultdict
import json
import copy
import re
import itertools
import datetime
from models import Protocol, Experiment, Step
from serializers import StepSerializer, ProtocolSerializer


class MainView(View):
	def get(self, request, *args, **kwargs):
		experiments = Experiment.objects.all()
		params = {'experiments' : experiments,}
		return render(request, 'protocol/main.html', params)

	def post(self, request, *args, **kwargs):
		pass


class AddProtocolView(View):
	def get(self, request, *args, **kwargs):
		params = {}
		return render(request, 'protocol/add_protocol.html', params)

	def post(self, request, *args, **kwargs):
		return HttpResponse("thanks")

class ProtocolListView(ListView):
	model = Protocol
	template_name = 'protocol/protocol_list.html'
	context_object_name = 'protocols'

	def post(self, request, *args, **kwargs):
		message = 'Sorry, cannot finish this task right now'
		try:
			protocol_name = request.POST.get('protocol')
			action = request.POST.get('action')
			if action == 'start new experiment':
				message = self.add_new_experiment(protocol_name)
			elif action == 'delete protocol':
				message = self.delete_protocol(protocol_name)
		except Exception:
			pass
		return HttpResponse(message)

	def add_new_experiment(self, protocol_name):
		message = 'success'
		try:
			protocol = Protocol.objects.get(name=protocol_name)
			today = datetime.date.today()
			experiment = Experiment.objects.create(start_date=today, protocol=protocol)
			experiment.save()
			protocol.ninstance += 1
			protocol.save()
		except Exception:
			message = 'start new experiment %s failed' % protocol_name
		return message

	def delete_protocol(self, protocol_name):
		message = 'success'
		try:
			Protocol.objects.get(name=protocol_name).delete()
		except Exception:
			message = 'delete protocol %s failed' % protocol_name
		return message


class ProtocolDetailView(DetailView):
	def get(self, request, *args, **kwargs):
		protocol_name = self.kwargs.get('protocol')
		protocol = Protocol.objects.get(name=protocol_name)
		steps = protocol.steps.all()
		params = {'protocol' : protocol,
		          'steps' : steps 
		         }
		return render(request, 'protocol/protocol_detail.html', params)


class SaveProtocolAPIView(APIView):
	def post(self, request, *args, **kwargs):
		serializer = ProtocolSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return HttpResponse('Saved')
		return HttpResponse('Cannot save the protocol')

class ProtocolListAPIView(APIView):
	def get(self, request, format=None):
		protocols = Protocol.objects.all()
		serializer = ProtocolSerializer(protocols, many=True)
		return Response(serializer.data)

class ProtocolDetailAPIView(APIView):
	def get(self, request, format=None):
		protocol_name = self.args[0]
		protocol = Protocol.objects.get(name=protocol_name)
		serializer = ProtocolSerializer([protocol], many=True)
		return Response(serializer.data)


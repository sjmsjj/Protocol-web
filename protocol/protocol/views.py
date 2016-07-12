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
		order_by = request.GET.get('order_by', 'protocol')
		if order_by == 'protocol':
			ongoing_experiments = Experiment.objects.all()
		elif order_by == 'start_date':
			ongoing_experiments = Experiment.objects.all().order_by('start_date', 'protocol')
		experiments = self.get_experiments_state(ongoing_experiments)
		params = {'experiments' : experiments,}
		return render(request, 'protocol/main.html', params)

	def post(self, request, *args, **kwargs):
		pass

	"""
    experiments = [{protocolname:{finished_steps  :[{date:date, step:stepname}],
                                   unfinished_steps:[{date:date, step:stepname}]}]
    """
	def get_experiments_state(self, ongoing_experiments):
		today = datetime.date.today()
		experiments = []
		for experiment in ongoing_experiments:
			start_date = experiment.start_date
			steps = Protocol.objects.get(name=experiment.protocol.name).steps.all()
			finished_steps, unfinished_steps = [], []
			for step in steps:
				date = start_date + datetime.timedelta(days=step.day)
				if date <= today:
					finished_steps.append({'date':self.format_date(date), 'step':step.name})
				else:
					unfinished_steps.append({'date':self.format_date(date), 'step':step.name})
			experiments.append({experiment.protocol.name:{'finished_steps':finished_steps,
				                                     'unfinished_steps':unfinished_steps}})
		return experiments

	def format_date(self, date):
		return date.strftime("%d %b, %Y (%a)")

            	
class AddEditProtocolView(View):
	def get(self, request, *args, **kwargs):
		protocol_name = request.GET.get('protocol_name', '')
		protocol = None
		steps = []
		if protocol_name:
			protocol = Protocol.objects.get(name=protocol_name)
			steps = protocol.steps.all()
		params = {'protocol_name' : protocol_name,
		          'steps' : steps,
		          }
		return render(request, 'protocol/add_edit_protocol.html', params)

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

# the following save/edit code needs to be optimized
class SaveProtocolAPIView(APIView):
	def post(self, request, *args, **kwargs):
		edited_protocol_name = request.data.pop('edited_protocol_name')
		new_protocol_name = request.data.get('name')
		edited_protocol = []
		experiments = []
		if edited_protocol_name:
			edited_protocol = Protocol.objects.get(name=edited_protocol_name)
			for experiment in edited_protocol.experiments.all():
				experiments.append(experiment)
			edited_protocol = [edited_protocol]
			Protocol.objects.get(name=edited_protocol_name).delete()

		serializer = ProtocolSerializer(data=request.data)
		if serializer.is_valid():
			if edited_protocol:
				serializer.save()
				new_protocol = Protocol.objects.get(name=new_protocol_name)
				for experiment in experiments:
					experiment.protocol = new_protocol
					experiment.save()
				new_protocol.ninstance = len(experiments)
				new_protocol.save()
			else:
				serializer.save()
			return HttpResponse('Saved')
		else:
			edited_protocol[0].save()

	        for experiment in experiments:
	        	experiment.protocol = edited_protocol
	        	experiment.save()
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


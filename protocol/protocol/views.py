from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView, DetailView, ListView
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

from django.core.urlresolvers import reverse
from django.db.models import Q, F, Func, Sum
from django.db.models.functions import Substr
from collections import defaultdict
import json
import copy
import re
import itertools
import datetime
from django.utils import timezone
from models import Protocol, Experiment, Step, ProtocolUser
from serializers import StepSerializer, ProtocolSerializer
from django.contrib.auth.forms import UserCreationForm
from forms import RegistrationForm

class Registration(View):
	def get(self, request, *args, **kwargs):
		form = RegistrationForm
		params = {'form' : form,}
		return render(request, 'protocol/registration.html', params)

	def post(self, request, *args, **kwargs):
		form = RegistrationForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect(reverse('login'))
		else:
			return render(request, 'protocol/registration.html', {'form':form})

register = Registration.as_view()


def protocol_login(request, *args, **kwargs):
	if request.user.is_authenticated():
		return redirect(reverse('where'), permant=True)
	else:
		return login_view(request, *args, **kwargs)

class MainView(View):
	def get(self, request, *args, **kwargs):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		order_by = request.GET.get('order_by', 'protocol')
		if order_by == 'protocol':
			ongoing_experiments = user.get_experiments().order_by('protocol', 'start_date')
		elif order_by == 'start_date':
			ongoing_experiments = user.get_experiments().order_by('start_date', 'protocol')
		experiments = self.get_experiments_state(ongoing_experiments)
		params = {'experiments' : experiments,}
		return render(request, 'protocol/main.html', params)

	"""
    experiments = [{protocolname:{finished_steps  :[{date:date, step:stepname}],
                                   unfinished_steps:[{date:date, step:stepname}]}]
    """
	def get_experiments_state(self, ongoing_experiments):
		experiments = []
		for experiment in ongoing_experiments:
			finished_steps = experiment.get_finished_steps()
			unfinished_steps = experiment.get_unfinished_steps()
			experiments.append({experiment.protocol.name:{'finished_steps':finished_steps,
				                                          'unfinished_steps':unfinished_steps,
				                                          'experiment_note': experiment.note}})
		return experiments
    
main = login_required(MainView.as_view())

class AddEditProtocolView(View):
	def get(self, request, *args, **kwargs):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		protocol_name = request.GET.get('protocol_name', '')
		protocol = None
		steps = []
		if protocol_name:
			protocol = user.get_protocol(protocol_name)
			steps = protocol.get_steps()
		current_protocol_names = user.get_protocols().values_list('name', flat=True)
		params = {'protocol_name' : protocol_name,
		          'steps' : steps,
		          'current_protocol_names' : current_protocol_names,
		          }
		return render(request, 'protocol/add_edit_protocol.html', params)

	def post(self, request, *args, **kwargs):
		return HttpResponse("thanks")

add_edit_protocol = login_required(AddEditProtocolView.as_view())

class ProtocolListView(ListView):
	template_name = 'protocol/protocol_list.html'
	context_object_name = 'protocols'

	def get_queryset(self):
		user = ProtocolUser.objects.get(user_ptr_id=self.request.user.id)
		return user.get_protocols()

	def post(self, request, *args, **kwargs):
		self.user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		message = 'Sorry, cannot finish this task right now, please try again later'
		try:
			protocol_name = request.POST.get('protocol')
			action = request.POST.get('action')
			start_date = request.POST.get('start_date')
			note = request.POST.get('note')
			protocol = self.user.get_protocol(protocol_name)
			if action == 'start new experiment':
				message = self.add_new_experiment(protocol, start_date, note)
			elif action == 'delete protocol':
				message = self.delete_protocol(protocol)
		except Exception:
			pass
		return HttpResponse(message)

	def add_new_experiment(self, protocol, start_date=None, note=None):
		message = 'success'
		start_time = timezone.now()
		if start_date:
			month, day, year = map(int, start_date.split('/'))
			hour, minute = start_time.hour, start_time.minute
			start_time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
		try:
			experiment = Experiment.objects.create(user=self.user, start_date=start_time, protocol=protocol, note=note)
			experiment.save()
			protocol.ninstance += 1
			protocol.save()
		except Exception:
			message = 'start new experiment %s failed' % protocol_name
		return message

	def delete_protocol(self, protocol):
		message = 'success'
		try:
			protocol.delete()
		except Exception:
			message = 'delete protocol %s failed' % protocol_name
		return message

protocol_list = login_required(ProtocolListView.as_view())

class ProtocolDetailView(DetailView):
	def get(self, request, *args, **kwargs):		
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		protocol_name = self.kwargs.get('protocol')
		protocol = user.get_protocol(protocol_name)
		steps = protocol.get_steps()
		params = {'protocol' : protocol,
		          'steps' : steps 
		         }
		return render(request, 'protocol/protocol_detail.html', params)

protocol_detail = login_required(ProtocolDetailView.as_view())

# the following save/edit code needs to be optimized
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
	def get(self, request, format=None):
		user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		protocol_name = self.args[0]
		protocol = user.get_protocol(protocol_name)
		serializer = ProtocolSerializer([protocol], many=True)
		return Response(serializer.data)

api_protocol_detail = login_required(ProtocolDetailAPIView.as_view())

class ProtocolRouterView(View):
    login_url = 'login'
    redirect_url = 'main'

    def get(self, request, *args, **kwargs):
        return redirect(self.get_redirect_url())

    def get_access_url(self):
        ACCESS_CHECKS = (
                         (self.request.user,'setup_completed', reverse_lazy('main')),
                         )
        for obj, lock, url in ACCESS_CHECKS:
            if not getattr(obj, lock):
                return redirect(url)

    def get_redirect_url(self):
        if not self.request.user.is_authenticated():
            return reverse_lazy(self.login_url)
        return reverse_lazy(self.redirect_url)

where_to_go = never_cache(ProtocolRouterView.as_view())





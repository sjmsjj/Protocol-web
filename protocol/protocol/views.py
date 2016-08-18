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
from models import Protocol, Experiment, Step, ProtocolUser, SharedProtocol
from django.contrib.auth.forms import UserCreationForm
from forms import RegistrationForm, UserProfileForm
from django.contrib.auth import get_user_model

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

class ProtocolFilter(django_filters.FilterSet):
	SEARCH_FILTERS = ['name__istartswith', 'name__icontains']
	name = django_filters.MethodFilter(action='filter_search')
	filterset = []

	class Meta:
		model = Protocol
		fields = ['name']

	def filter_search(self, queryset, value):
		filterset = [] 
		for filter in self.SEARCH_FILTERS:
		    filterset, queryset = self.refine_search(filterset, queryset, {filter:value})
		self.filterset = filterset
		return filterset

	def refine_search(self, filterset, queryset, filter_params):
	    return filterset+list(queryset.filter(**filter_params)), queryset.exclude(**filter_params)

	def __len__(self):
		return self.queryset.count()

	def count(self):
		return len(self.filterset)

class SearchProtocolView(TemplateView):
	template_name = "protocol/search_protocol.html"

	def get_context_data(self, **kwargs):
		context = super(SearchProtocolView, self).get_context_data(**kwargs)
		context['shared_protocol_count'] = self.request.user.get_shared_protocol_count
		return context
	
	def post(self, request, *args, **kwargs):
		# user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		user = self.request.user
		name = request.POST.get("name")
		searched_protocols = None
		if name:
			searched_protocols = ProtocolFilter(data=request.POST, queryset=Protocol.objects.filter(is_public=True).exclude(user=user))
		params = {"searched_protocols": searched_protocols,
		          "keywords": name,
		          }
		return HttpResponse(render_to_string("protocol/search_results.html", params))

search_protocol = login_required(SearchProtocolView.as_view())

class MainView(View):
	def get(self, request, *args, **kwargs):
		# user = ProtocolUser.objects.get(user_ptr_id=request.user.id)
		user = self.request.user
		order_by = request.GET.get('order_by', 'protocol')
		if order_by == 'protocol':
			ongoing_experiments = user.get_experiments().order_by('protocol', 'start_date')
		elif order_by == 'start_date':
			ongoing_experiments = user.get_experiments().order_by('start_date', 'protocol')
		experiments = self.get_experiments_state(ongoing_experiments)
		params = {'experiments' : experiments,
		          'shared_protocol_count' : user.get_shared_protocol_count,
		}
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
		user = request.user
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
		          'shared_protocol_count' : user.get_shared_protocol_count,
		          }
		return render(request, 'protocol/add_edit_protocol.html', params)

	def post(self, request, *args, **kwargs):
		return HttpResponse("thanks")

add_edit_protocol = login_required(AddEditProtocolView.as_view())

class ProtocolListView(ListView):
	template_name = 'protocol/protocol_list.html'
	context_object_name = 'protocols'
	return_msg = "error"

	def get_queryset(self):
		return self.request.user.get_protocols()

	def get_context_data(self, *args, **kwargs):
		context = super(ProtocolListView, self).get_context_data(*args, **kwargs)
		context['shared_protocol_count'] = self.request.user.get_shared_protocol_count
		return context

	def post(self, request, *args, **kwargs):
		try:
			protocol_name = request.POST.get('protocol')
			action = request.POST.get('action')
			start_date = request.POST.get('start_date')
			note = request.POST.get('note')
			protocol = request.user.get_protocol(protocol_name)
			if action == 'start new experiment':
				self.add_new_experiment(protocol, start_date, note)
			elif action == 'change protocol access level':
				self.change_protocol_access_level(protocol)
			elif action == 'delete protocol':
				self.delete_protocol(protocol)
		except Exception:
			pass
		return HttpResponse(self.return_msg)

	def add_new_experiment(self, protocol, start_date=None, note=None):
		start_time = timezone.now()
		if start_date:
			month, day, year = map(int, start_date.split('/'))
			hour, minute = start_time.hour, start_time.minute
			start_time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
		try:
			experiment = Experiment.objects.create(user=self.request.user, start_date=start_time, protocol=protocol, note=note)
			experiment.save()
			protocol.ninstance += 1
			protocol.save()
			self.return_msg = "success"
		except Exception:
			pass

	def change_protocol_access_level(self, protocol):
		try:
			if protocol.is_public:
				protocol.is_public = False
			else:
				protocol.is_public = True
			protocol.save()
			self.return_msg = "success"
		except Exception:
			pass

	def delete_protocol(self, protocol):
		try:
			protocol.delete()
			self.return_msg = render_to_string("protocol/start_new_experiment.html", {"protocols": self.user.get_protocols()})
		except Exception:
			pass

protocol_list = login_required(ProtocolListView.as_view())

class ProtocolDetailView(DetailView):
	def get(self, request, *args, **kwargs):		
		user = self.request.user
		protocol_id = self.request.GET.get('protocol_id')
		if protocol_id:
			protocol = user.get_shared_protocol(protocol_id)
			editable=False
		else:
			protocol_name = self.kwargs.get('protocol')
			editable=True
			protocol = user.get_protocol(protocol_name)
		steps = protocol.get_steps()
		params = {'protocol' : protocol,
		          'steps' : steps,
		          'shared_protocol_count' : user.get_shared_protocol_count,
		          'editable': editable,
		         }
		return render(request, 'protocol/protocol_detail.html', params)

protocol_detail = login_required(ProtocolDetailView.as_view())

class UserProfileView(UpdateView):
	form_class = UserProfileForm
	template_name = 'protocol/user_profile.html'
	success_url = reverse_lazy('main')

	def get_object(self):
		return self.request.user

user_profile_view = UserProfileView.as_view()

class SendSharedProtocolView(View):
	message = 'cannot share the protocol right now, please try again later'

	def post(self, request, *args, **kwargs):
		protocol_name = request.POST.get('protocol')
		emails = request.POST.get('emails')
		if protocol_name and emails:
			self.create_shared_protocol(protocol_name, emails)
		return HttpResponse(self.message)

	def create_shared_protocol(self, protocol_name, emails):
		from_user = self.request.user
		try:
			protocol = from_user.get_protocol(protocol_name)
			email_list = emails.split(',')
			for email in email_list:
				email = email.strip()
				to_user = ProtocolUser.objects.filter(email=email).first()				
				if to_user:
					try:
						shared_protocol = SharedProtocol.objects.create(shared_from=from_user, shared_to=to_user, protocol=protocol)
						shared_protocol.save()
					except Exception:
						pass
			self.message = 'success'
		except Exception:
			pass

send_shared_protocol = login_required(SendSharedProtocolView.as_view())

class ProcessSharedProtocolView(ListView):
	return_msg = "error"
	def get(self, request, *args, **kwargs):
		user = request.user
		params = {"shared_protocols": user.get_shared_protocols(),
		          "shared_protocol_count": user.get_shared_protocol_count,
		          }
		return render(request, "protocol/shared_protocol_list.html", params)

	def post(self, request, *args, **kwargs):
		protocol_id = request.POST.get("protocol_id")
		action = request.POST.get("action")
		if protocol_id and action:
			try:
				protocol = Protocol.objects.get(id=protocol_id)
				self.return_msg = "search3"
				if action == "accept protocol":
					self.accept_shared_protocol(protocol)
				elif action == "decline protocol":
					self.decline_shared_protocol(protocol)
				elif action == "add from search":
					self.accept_shared_protocol(protocol, from_search=True)
			except Exception:
				pass
		return HttpResponse(self.return_msg)

	def accept_shared_protocol(self, protocol, from_search=False):
		shared_protocol = None
		if from_search:
			name_postfix = 'Search'
		else:
			shared_protocol = self.request.user.get_shared_protocols().get(protocol=protocol)
			name_postfix = shared_protocol.shared_from.get_first_name()
		new_protocol_name = protocol.name + "_from_" + name_postfix
		count = self.user.get_protocols().filter(name__istartswith=new_protocol_name).count()
		if count > 0:
			new_protocol_name += "_" + str(count)
		new_protocol = Protocol.objects.create(user=self.request.user, name=new_protocol_name, last_updated=timezone.now())
		new_protocol.save()
		self.copy_protocol_steps(protocol, new_protocol)
		if not from_search:
			shared_protocol.delete()
		self.return_msg = "success"

	def copy_protocol_steps(self, old_protocol, new_protocol):
		for step in old_protocol.get_steps():
			new_step = Step.objects.create(protocol=new_protocol, name=step.name, day=step.day, detail=step.detail, note=step.note)
			new_step.save()

	def decline_shared_protocol(self, protocol):
		self.request.get_shared_protocols().get(protocol=protocol).delete()
		self.return_msg = "success"

process_shared_protocol = login_required(ProcessSharedProtocolView.as_view())

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





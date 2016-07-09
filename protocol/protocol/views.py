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

class MainView(View):
	def get(self, request, *args, **kwargs):
		params = {}
		return render(request, 'protocol/main.html', params)

	def post(self, request, *args, **kwargs):
		pass


class AddProtocolView(View):
	def get(self, request, *args, **kwargs):
		params = {}
		return render(request, 'protocol/add_protocol.html', params)

	def post(self, request, *args, **kwargs):
		return HttpResponse("thanks")


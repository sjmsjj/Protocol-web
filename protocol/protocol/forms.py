from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from models import ProtocolUser
from django import forms
from django.utils.translation import ugettext_lazy as _
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
class RegistrationForm(UserCreationForm, forms.ModelForm):
	first_name = forms.CharField(required = True)
	last_name = forms.CharField(required = True)

	def __init__(self, *args, **kwargs):
		super(RegistrationForm, self).__init__(*args, **kwargs)
		for fieldname in ['username', 'password1', 'password2']:
		    self.fields[fieldname].help_text = None

	class Meta:
		model = ProtocolUser
		fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

	def clean(self):
		username = self.cleaned_data.get('username')
		email = self.cleaned_data.get('email')

		if ProtocolUser.objects.filter(username=username):
			self.add_error('username', 'username has been used, please try another one')
		if ProtocolUser.objects.filter(email=email):
			self.add_error('email', 'this email address has been registered')

		return self.cleaned_data

	def save(self):
		first_name = self.cleaned_data.get('first_name')
		last_name = self.cleaned_data.get('last_name')
		username = self.cleaned_data.get('username')
		email = self.cleaned_data.get('email')
		password = self.cleaned_data.get('password1')
		user = ProtocolUser.objects.create_user(first_name, last_name, username, email, password)                              
		return user


class UserAuthenticationForm(AuthenticationForm):
	email = forms.EmailField(label=_("Email"),
							 max_length=254,
		                     widget=forms.EmailInput(attrs={'autofocus': ''}))

	def __init__(self, request=None, *args, **kwargs):
		self.request = request
		self.user_cache = None
		super(UserAuthenticationForm, self).__init__(request, *args, **kwargs)
		self.clean_fields()
		UserModel = ProtocolUser
		self.email_field = UserModel._meta.get_field(UserModel.REQUIRED_FIELDS[0])
		if self.fields['email'].label is None:
		    self.fields['email'].label = capfirst(self.email_field.verbose_name)

	def clean_fields(self):
		self.fields.pop('username')
		field_order = ['email', 'password']
		self.order_fields(field_order)

	def clean(self):
	    email = self.cleaned_data.get('email')
	    password = self.cleaned_data.get('password')

	    if email and password:
		    if not get_user_model().objects.filter(email=email):
	        	self.add_error('email','This email has not been registered')
		
		    else:
		    	username = get_user_model().objects.get(email=email).username
		        self.user_cache = authenticate(username=username, password=password)
		        if self.user_cache is None:
		        	self.add_error('password','invalid password')
		        else:
		            self.confirm_login_allowed(self.user_cache)

	    return self.cleaned_data
		

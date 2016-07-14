from django.contrib.auth.forms import UserCreationForm
from models import ProtocolUser
from django import forms
from django.utils.translation import ugettext_lazy as _
import datetime

class RegistrationForm(UserCreationForm, forms.ModelForm):

	class Meta:
		model = ProtocolUser
		fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']
		fields_required = ['first_name', 'last_name']


 

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



		
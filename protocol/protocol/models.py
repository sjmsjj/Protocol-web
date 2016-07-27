import logging
import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, User
from django.contrib.auth import get_user_model

class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email=None, password=None, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError('Email must be set')
        email = UserManager.normalize_email(email)
        user = self.model(username=username, email=email, first_name=first_name, last_name=last_name,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, **extra_fields)
 
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password, **extra_fields):
        user = self.create_user(username, email, password, **extra_fields)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class ProtocolUser(User):
	objects = UserManager()
	@property
	def label(self):
	    return (self.email if self.email 
	            else self.username)

	def __unicode__(self):
	    return self.label

	def __str__(self):
	    return self.label
	 
	def get_full_name(self): 
	    return '%s %s'.strip() % (self.first_name, self.last_name)

	def get_first_name(self):
	    return self.first_name

	def deactivate(self):
	    self.is_active=False
	    self.save()

	def activate(self):
	    self.is_active=True
	    self.save()

	@property
	def authorized_user(self):
	    return self.is_staff or self.is_superuser

	def get_protocols(self):
		return Protocol.objects.filter(user=self)

	def get_protocol(self, protocol_name):
		return self.get_protocols().filter(name=protocol_name).first()

	def get_experiments(self):
		return Experiment.objects.filter(user=self)

	@property
	def get_shared_protocol_count(self):
		return self.get_shared_protocols().count()

	def get_shared_protocols(self):
		return SharedProtocol.objects.filter(shared_to=self).order_by('shared_from')

	def get_shared_protocol(self, protocol_id):
		return Protocol.objects.get(id=protocol_id)

class Protocol(models.Model):
	user = models.ForeignKey(ProtocolUser, on_delete=models.PROTECT, null=True, blank=True)
	name = models.CharField(max_length=100)
	ninstance = models.IntegerField(default=0)
	last_updated = models.DateTimeField(blank=True, null=True)
	is_public = models.BooleanField(default=False)

	def __unicode__(self):
		return 'Protocol: %s' % self.name

	def __str__(self):
		return 'Protocol: %s' % self.name

	def get_steps(self):
		return Step.objects.filter(protocol=self).order_by('day')

	@property
	def first_step(self):
		return Step.objects.first()

	@property
	def last_step(self):
		return Step.objects.last()

	def get_experiments(self):
		return Experiment.objects.filter(protocol=self)

	def get_ninstances(self):
		return self.ninstance

	class Meta:
		unique_together = ('user', 'name')

class SharedProtocol(models.Model):
	shared_from = models.ForeignKey(ProtocolUser, on_delete=models.CASCADE, related_name='shared_from')
	shared_to = models.ForeignKey(ProtocolUser, on_delete=models.CASCADE, related_name='shared_to')
	protocol = models.ForeignKey(Protocol, on_delete=models.CASCADE)

	@property
	def protocol_name(self):
		return self.protocol.name

	# @property 
	def protocol_id(self):
		return self.protocol.id

	class Meta:
		unique_together = ('shared_from', 'shared_to', 'protocol')

class Step(models.Model):
	protocol = models.ForeignKey(Protocol, related_name='steps', on_delete=models.CASCADE)
	name = models.CharField(max_length=100)
	day = models.IntegerField()
	detail = models.TextField()
	note = models.TextField(null=True, blank=True)

	def __unicode__(self):
		return 'On day %s, do: %s' % (str(day), name)

	def __unicode__(self):
		return 'On day %s, do: %s' % (str(day), name)

	class Meta:
		ordering = ['protocol', 'day']

class Experiment(models.Model):
	user = models.ForeignKey(ProtocolUser, on_delete=models.CASCADE)
	protocol = models.ForeignKey(Protocol, related_name='experiments', on_delete=models.CASCADE)
	start_date = models.DateTimeField(blank=True, null=True)
	note = models.TextField(null=True, blank=True)

	today = timezone.now()

	def __unicode__(self):
		return 'Experiment started on %s following protocol %s' % (str(start_date), protocol.name)

	def __unicode__(self):
		return 'Experiment started on %s following protocol %s' % (str(start_date), protocol.name)

	def get_finished_steps(self):
		finished_steps = []
		for step in self.protocol.get_steps():
			date = self.start_date + datetime.timedelta(days=step.day)
			if date <= self.today:
				finished_steps.append({'date':self.format_date(date), 'step':step.name})
			else:
				break
		return finished_steps

	def get_unfinished_steps(self):
		unfinished_steps = []
		for step in self.protocol.get_steps():
			date = self.start_date + datetime.timedelta(days=step.day)
			if date > self.today:
				unfinished_steps.append({'date':self.format_date(date), 'step':step.name})
		return unfinished_steps

	def is_acitve(self):
		return len(self.get_unfinished_steps()) > 0

	def format_date(self, date):
		return date.strftime("%d %b, %Y (%a)")

	class Meta:
		ordering = ['protocol', 'start_date']
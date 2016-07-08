from django.db import models

class Protocol(models.Model):
	name = models.CharField(primary_key = True, max_length=100)

	def __str__(self):
		return 'Protocol: %s' % self.name

class Step(models.Model):
	protocol = models.ForeignKey(Protocol, related_name='steps')
	name = models.CharField(max_length=100)
	day = models.IntegerField()
	detail = models.TextField()

	class Meta:
		ordering = ['protocol', 'day']

class Experiment(models.Model):
	protocol = models.ForeignKey(Protocol, related_name='experiments')
	start_date = models.DateField()

	class Meta:
		ordering = ['start_date']


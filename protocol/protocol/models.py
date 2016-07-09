from django.db import models

class Protocol(models.Model):
	name = models.CharField(primary_key = True, max_length=100)
	ninstance = models.IntegerField(default=0)

	def __str__(self):
		return 'Protocol: %s' % self.name

class Step(models.Model):
	protocol = models.ForeignKey(Protocol, primary_key=True, related_name='steps', on_delete=models.CASCADE)
	name = models.CharField(max_length=100, primary_key=True)
	day = models.IntegerField()
	detail = models.TextField()
	note = models.TextField(null=True, blank=True)

	class Meta:
		ordering = ['protocol', 'day']

class Experiment(models.Model):
	protocol = models.ForeignKey(Protocol, related_name='experiments')
	start_date = models.DateField()

	class Meta:
		ordering = ['start_date']


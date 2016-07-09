from django import template
from protocol.models import Protocol

register = template.Library()

@register.simple_tag
def has_on_going_experiments(protocol_name):
	return Protocol.objects.get(name=protocol_name).ninstance

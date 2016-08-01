from django import template
from protocol.models import Protocol

register = template.Library()

STEP_PER_ROW = 4

@register.simple_tag
def has_on_going_experiments(protocol_name):
	return Protocol.objects.get(name=protocol_name).ninstance

@register.simple_tag
def identify_new_row(counter, previous_counter = '0'):
	counter = int(counter) + int(previous_counter)
	if counter % STEP_PER_ROW == 0:
		return 'end_row'
	if counter % STEP_PER_ROW == 1:
		return 'start_row'

@register.simple_tag
def identify_experiment_end(unfinished_steps):
	counter = int(unfinished_steps)
	if counter == 0:
		return 'end'

@register.simple_tag
def highlight_search(protocol_name=None, keywords=None):
	string = []
	keywords.lower()
	for word in protocol_name.split():
		if word.lower() in keywords:
			string.append('<span style="color:red">' + word + "</span>")
		else:
			string.append(word)
	return ' '.join(string)

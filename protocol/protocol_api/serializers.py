from rest_framework import serializers
from protocol.models import Protocol, Step, Experiment

class StepSerializer(serializers.ModelSerializer):
	class Meta:
		model = Step
		fields = ['day', 'name', 'detail', 'note']

class ProtocolSerializer(serializers.ModelSerializer):
	steps = StepSerializer(many=True, read_only=False)

	class Meta:
		model = Protocol
		fields = ['id', 'user', 'name', 'ninstance', 'steps']

	def create(self, validated_data):
		new_steps = validated_data.pop('steps')
		protocol = Protocol.objects.create(**validated_data)
		for step in new_steps:
			Step.objects.create(protocol=protocol, **step)
		return protocol

class ExperimentSerializer(serializers.ModelSerializer):
	steps = StepSerializer(many=True, read_only=True)

	class Meta:
		model = Experiment
		fields = ['id', 'user', 'protocol', 'start_date', 'note', 'steps']

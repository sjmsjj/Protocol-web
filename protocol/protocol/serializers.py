from rest_framework import serializers
from .models import Protocol, Step

class StepSerializer(serializers.ModelSerializer):
	class Meta:
		model = Step
		fields = ['day', 'name', 'detail', 'note']

class ProtocolSerializer(serializers.ModelSerializer):
	steps = StepSerializer(many=True, read_only=False)

	class Meta:
		model = Protocol
		fields = ['user', 'name', 'ninstance', 'steps']

	def create(self, validated_data):
		new_steps = validated_data.pop('steps')
		protocol = Protocol.objects.create(**validated_data)
		for step in new_steps:
			Step.objects.create(protocol=protocol, **step)
		return protocol
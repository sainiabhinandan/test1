from rest_framework import serializers
from .models import ClassifiedDocument

class DocumentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassifiedDocument
        fields = '__all__'
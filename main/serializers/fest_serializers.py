from rest_framework import serializers
from main.models_fest import Fest

class FestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fest
        fields = [
            'id', 'banner', 'title', 'date', 'address',
            'start_time', 'end_time', 'category', 'description'
        ]
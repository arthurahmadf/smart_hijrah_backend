# main/serializers/gamification_serializers.py
from rest_framework import serializers
from main.models_gamification import AmalanCheckin, UserStreak

class AmalanCheckinSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmalanCheckin
        fields = ['amalan', 'status', 'points_earned', 'date']

class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStreak
        fields = ['amalan', 'streak_count']

class LevelInfoSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_profile = serializers.CharField(allow_null=True)
    rank = serializers.IntegerField()
    acquired_points = serializers.IntegerField()
    required_points_to_next_level = serializers.IntegerField()
    level = serializers.CharField()
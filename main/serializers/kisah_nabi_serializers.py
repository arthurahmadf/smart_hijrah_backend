from rest_framework import serializers
from main.models_kisah_nabi import KisahNabi, KisahNabiEpisode
from main.my_utils import generate_url

class KisahNabiEpisodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KisahNabiEpisode
        fields = ['id', 'title', 'description', 'doc_url', 'cover_url']

class KisahNabiSerializer(serializers.ModelSerializer):
    main_cover = serializers.SerializerMethodField()
    episodes = KisahNabiEpisodeSerializer(many=True, read_only=True)
    
    class Meta:
        model = KisahNabi
        fields = ['id', 'prophet_name', 'total_read_count', 'main_cover', 'description', 'episodes']
    
    def get_main_cover(self, obj):
        return generate_url(obj.main_cover, self.context.get('request'))

class KisahNabiListSerializer(serializers.ModelSerializer):
    main_cover = serializers.SerializerMethodField()
    
    class Meta:
        model = KisahNabi
        fields = ['id', 'prophet_name', 'total_read_count', 'main_cover', 'description']
    
    def get_main_cover(self, obj):
        return generate_url(obj.main_cover, self.context.get('request'))
from rest_framework import serializers
from .models import *
from authentication.serializers import UserShowSerializer

class AlbumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Album
        fields = '__all__'


class SongTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongTrack
        fields = '__all__'


class PlayListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayList
        fields = '__all__'


class UserRatingsSerializer(serializers.ModelSerializer):
    user = UserShowSerializer(many=False, read_only=True, )
    class Meta:
        model = UserRatings
        fields = '__all__'


class ArtistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Artist
        fields = '__all__'
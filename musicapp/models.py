from django.db import models
from authentication.models import BaseModel, User
from django.contrib.postgres.fields import ArrayField

# Create your models here.

class SongTrack(models.Model):
    """A ORM for song tracks interactions"""
    
    id = models.CharField(primary_key=True, max_length=100, editable=False)
    name = models.CharField(max_length=1000, null=True, blank=True)
    duration_ms = models.IntegerField(default=0)
    artists = ArrayField(models.CharField(max_length=500, null=True, blank=True), default=list, blank=True)
    genres = ArrayField(models.CharField(max_length=500, null=True, blank=True), default=list, blank=True)
    external_urls = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        """A meta object for defining song tracks table"""

        db_table = "song_track"


class Album(models.Model):
    """A ORM for album interactions"""
    
    id = models.CharField(primary_key=True, max_length=100, editable=False)
    album_type = models.CharField(max_length=200, null=True, blank=True)
    name = models.CharField(max_length=1000, null=True, blank=True)
    release_date = models.CharField(max_length=100, null=True, blank=True)
    artists = ArrayField(models.CharField(max_length=500, null=True, blank=True), default=list, blank=True)
    total_tracks = models.IntegerField(default=0)
    external_urls = models.CharField(max_length=100, null=True, blank=True)
    tracks = models.ManyToManyField(SongTrack, blank=True, related_name="album")

    class Meta:
        """A meta object for defining Albums table"""

        db_table = "albums"


class Artist(models.Model):
    """A ORM for artist interactions"""
    
    id = models.CharField(primary_key=True, max_length=100, editable=False)
    name = models.CharField(max_length=1000, null=True, blank=True)
    external_urls = models.CharField(max_length=100, null=True, blank=True)
    popularity = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        """A meta object for defining Artist table"""

        db_table = "artists"


class PlayList(BaseModel):
    """A ORM for music playlists"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='playlist'
    )
    playlist_name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    tracks = models.ManyToManyField(SongTrack, blank=True)

    class Meta:
        """A meta object for defining Music PlayList table"""

        db_table = "music_playlist"


class UserRatings(BaseModel):
    """A ORM for user ratings"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='song_ratings'
    )
    song_track = models.ForeignKey(SongTrack, null=True, blank=True, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        """A meta object for defining user ratings on a song track table"""

        db_table = "user_ratings"
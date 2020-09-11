# project imports
from .exceptions import *
from base.utils import *
from .services import *
from .serializers import *

# django imports
import random
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q
from operator import or_
from functools import reduce
from rest_framework import generics

# rest_framework imports
from rest_framework import status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.views import APIView
from base.viewsets import BaseAPIViewSet
from authentication.serializers import UserShowSerializer


# API for listing all the songs fetched from the 3rd party Spotify Api 
class AlbumList(BaseAPIViewSet):
    """
    API to get a list of movies or search movies by their attributes
    """

    serializer_class = AlbumSerializer
    search_fields = ['name']

    def list(self, request, *args, **kwargs):
        try:
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)
            params = request.GET
            limit = int(params.get('limit', 20))
            offset = int(params.get('offset', 0))
            if offset and Album.objects.all().count() > offset:
                return Response(responsedata(False, PAGINATION_ERR),\
                    status=status.HTTP_400_BAD_REQUEST)
            res_albums =  AlbumService.get_songs_list(limit, offset)

            # Paginated response          
            return JsonResponse(res_albums, safe=False)

        except (ValidationError, ThirdPartyError, APIException) as e:
            return Response(responsedata(False, str(e)), status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(responsedata(False, "Something went wrong"), status=status.HTTP_400_BAD_REQUEST)


# CRUD api for the user collection of songs
class PlaylistAction(BaseAPIViewSet):

    serializer_class = PlayListSerializer
    model_class = PlayList
    instance_name = 'playlist'
    search_fields = ['tracks__name', 'tracks__genres', 'tracks__artists']
    filter_backends = (filters.SearchFilter,)
    queryset = PlayList.objects.all().order_by("-created_at")


    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        List all the playlists
        """
        if not (request.user.is_authenticated):
            return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

        playlist_map = {}
        queryset = self.filter_queryset(self.get_queryset()).filter(user=request.user)
        pagenumber = request.GET.get('page', 1)
        paginator = Paginator(queryset, 10)

        playlist_qs = paginator.page(pagenumber).object_list
        response = list(playlist_qs.values())

        for playlist in playlist_qs:
            playlist_map[playlist.pk] = playlist

        # Custom response creation
        for res in response:
            res.update({"tracks": list(playlist_map[res.get("uid")].tracks.values('id', 'name', 'duration_ms', 'artists', 'genres', 'external_urls', 'album__name'))})

        # Paginated response
        return JsonResponse(paginate(response, paginator, pagenumber), safe=False)


    def create(self, request):
        try:
            # Checking Authorization
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            user_data = UserShowSerializer(request.user).data
            playlist_info = request.data

            if playlist_info.get("tracks"):
                songs_list = list(set(playlist_info.pop("tracks")))
                songs_qs = SongTrack.objects.filter(id__in=songs_list).count()
                if songs_qs != len(songs_list):
                    raise PlaylistException("Please add songs by their valid ids, incorrect id in songs list")
            else:
                return Response(responsedata(False, "Please add songs for the playlist"),status=status.HTTP_400_BAD_REQUEST)

            if PlayList.objects.filter(user=request.user.uid, playlist_name=playlist_info.get("playlist_name")).exists():
                return Response(responsedata(False, "Playlist by this name already exists for the user"),
                                    status=status.HTTP_400_BAD_REQUEST)

            playlist_info["user"] = request.user.pk
            playlist_serializer = PlayListSerializer(data=playlist_info)

            with transaction.atomic():
                if playlist_serializer.is_valid(raise_exception=True):
                    playlist = playlist_serializer.save(user=request.user)
                    playlist.tracks.add(*songs_list)

                    res_data = playlist_serializer.data
                    res_data.update(user=user_data, tracks=list(playlist.tracks.values()))

            return JsonResponse(responsedata(True, "Playlist of songs created for the user", res_data), \
                            status=status.HTTP_202_ACCEPTED)

        except PlaylistException as e:
            return Response(responsedata(False, str(e)),status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)


    def update(self, request, pk):
        try:
            # Checking Authorization
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            user_data = UserShowSerializer(request.user).data
            playlist_info = request.data
            if PlayList.objects.filter(user=request.user, uid=pk).exists():
                instance = PlayList.objects.get(user=request.user, uid=pk)
            else:
                return Response(responsedata(False, "No playlist exists correspnding to this id for the user"),\
                                                status=status.HTTP_400_BAD_REQUEST)    

            if playlist_info.get("tracks"):
                songs_list = list(set(playlist_info.pop("tracks")))
                songs_qs = SongTrack.objects.filter(id__in=songs_list).count()
                if songs_qs != len(songs_list):
                    raise PlaylistException("One or more invalid song ids in songs list")
            else:
                return Response(responsedata(False, "Please add songs for the playlist"),status=status.HTTP_400_BAD_REQUEST)
            
            if PlayList.objects.filter(user=request.user,playlist_name=playlist_info.get("playlist_name")).exclude(pk=pk).exists():
                return Response(responsedata(False, "Playlist name already exists"),status=status.HTTP_400_BAD_REQUEST)

            playlist_info.update(user=request.user.pk) 
            playlist_serializer = PlayListSerializer(instance, data=playlist_info)

            with transaction.atomic():
                if playlist_serializer.is_valid(raise_exception=True):
                    playlist = playlist_serializer.save(user=request.user)

                    if playlist.tracks.all().exists():
                        playlist.tracks.clear()

                    playlist.tracks.add(*songs_list)

                    res_data = playlist_serializer.data
                    res_data.update(user=user_data, tracks=list(playlist.tracks.values()))

                    return JsonResponse(responsedata(True, "Playlist of songs updated for the user", res_data), \
                                    status=status.HTTP_202_ACCEPTED)

        except PlaylistException as e:
            return Response(responsedata(False, str(e)),status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)


# CRUD api for the searching through collection of songs
class SearchSongs(BaseAPIViewSet):

    serializer_class = SongTrackSerializer
    model_class = SongTrack
    instance_name = 'song_tracks'
    search_fields = ['name', 'genres', 'artists']
    filter_backends = (filters.SearchFilter,)
    queryset = SongTrack.objects.all()


    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        List all the music tracks
        """
        if not (request.user.is_authenticated):
            return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

        queryset = self.filter_queryset(self.get_queryset())
        pagenumber = request.GET.get('page', 1)
        paginator = Paginator(queryset, 10)

        songs_qs = paginator.page(pagenumber).object_list            
        response = list(songs_qs.values('id', 'name', 'duration_ms', 'artists', 'genres', 'external_urls', 'album__name'))

        # Paginated response
        return JsonResponse(paginate(response, paginator, pagenumber), safe=False)

  
    @action(detail=False, methods=['post'])
    def rate_song(self, request, *args, **kwargs):
        """
        Rate a song or Update the rating of songs from the list of available songs
        """
        try:
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            if not SongTrack.objects.filter(id=request.data.get("song_track")).exists():
                return Response(responsedata(False, "Invalid song track id"), status=status.HTTP_400_BAD_REQUEST)
 
            if UserRatings.objects.filter(song_track_id=request.data.get("song_track"), user=request.user).exists():
                instance = UserRatings.objects.get(song_track_id=request.data.get("song_track"), user=request.user)
                user_ratings = UserRatingsSerializer(instance, data=request.data)

                if user_ratings.is_valid(raise_exception=True):
                    user_ratings.save()
                    return JsonResponse(responsedata(True, "{} - track's rating is successfully updated".format(instance.song_track.name), \
                                        user_ratings.data), status=status.HTTP_200_OK)
            else:
                user_ratings = UserRatingsSerializer(data=request.data)
                if user_ratings.is_valid(raise_exception=True):
                    user_ratings.save(user=request.user)
                    song = SongTrack.objects.filter(id=user_ratings.data.get("song_track")).first()

            # Paginated response
                    return JsonResponse(responsedata(True, "{} - track is successfully rated".format(song.name), user_ratings.data), \
                                status=status.HTTP_200_OK)

        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)  


    @action(detail=False, methods=['get'])
    def song_ratings(self, request, *args, **kwargs):
        """
        List all song ratings for the user
        """
        try:
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            queryset = UserRatings.objects.filter(user=request.user)
            pagenumber = request.GET.get('page', 1)
            paginator = Paginator(queryset, 10)

            user_data = UserShowSerializer(request.user).data

            user_ratings_qs = paginator.page(pagenumber).object_list            
            response = list(user_ratings_qs.values('song_track__name', 'rating'))

            response.append({"user":user_data})

            # Paginated response
            return JsonResponse(paginate(response, paginator, pagenumber), safe=False)

        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)                              


# Api for autosuggesting songs based on playlists of user
class AutoSuggest(generics.ListAPIView):
    serializer_class = SongTrackSerializer
    model_class = PlayList

    def list(self, request, *args, **kwargs):
        """
        Autosuggest songs based on playlists of user
        """
        try:
            response = {}
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            queryset = PlayList.objects.filter(user=request.user)
            pagenumber = request.GET.get('page', 1)
            paginator = Paginator(queryset, 10)

            user_data = UserShowSerializer(request.user).data

            playlist_qs = paginator.page(pagenumber).object_list            
            
            genres = list(queryset.values_list("tracks__genres", flat=True))
            artists = list(queryset.values_list("tracks__artists", flat=True))
            albums =  list(queryset.values_list("tracks__album__name", flat=True))

            unique_genres = sum([data[0].split(",") for data in genres], [])

            genre_list = [Q(genres__icontains=x) for x in unique_genres]

            artist_list  = [Q(artists__icontains=x) for x in sum([data for data in artists], [])]

            albums_list = [Q(album__name__icontains=x) for x in albums]

            similar_genre_songs = list(SongTrack.objects.filter(Q(reduce(or_, genre_list))).values("name", "genres"))

            similar_artist_songs = list(SongTrack.objects.filter(Q(reduce(or_, artist_list))).values("name", "artists"))

            similar_album_songs = list(SongTrack.objects.filter(Q(reduce(or_, albums_list))).values("name", "album__name"))

            response.update({"based_on_genre":similar_genre_songs, "based_on_album": similar_album_songs,
                                    "based_on_artist": similar_artist_songs})

            # Paginated response
            return JsonResponse(paginate(response, paginator, pagenumber), safe=False)

        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)


# Api for recommending songs to a user
class RecommendSongs(generics.CreateAPIView):

    def create(self, request, *args, **kwargs):
        try:
            # Checking Authorization
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            data = request.data
            resource_id = data.get("resource_id")
            artists = None

            if SongTrack.objects.filter(id=resource_id).exists():
                song_track =  SongTrack.objects.filter(id=resource_id).values().first()
                resource_url = song_track.get("external_urls")
                resource_name = song_track.get("name")
                artists = song_track.get("artists")[0]

            elif Album.objects.filter(id=resource_id).exists():
                album = Album.objects.filter(id=resource_id).values().first()
                resource_url = album.get("external_urls")
                resource_name = album.get("name")
                artists = album.get("artists")[0]

            elif Artist.objects.filter(id=resource_id).exists():
                artist = Artist.objects.filter(id=resource_id).values().first()
                resource_url = artist.get("external_urls")
                resource_name = artist.get("name")

            else:
                return JsonResponse(responsedata(False, "Invalid resource, not available for sharing"), \
                            status=status.HTTP_400_BAD_REQUEST)
            
            try:
                full_name = request.user.first_name + " " + request.user.last_name
                mail_txt = "recommend_song_mail.txt"
                mail_html = "recommend_song_mail.html"
                send_mail_request(['pooja.a@engineerbabu.in', request.data.get("receiver_mail")],
                    mail_txt, mail_html, "Spotify Recommends", resource_url=resource_url, resource_name=resource_name, \
                    sender=full_name, artists=artists)

                return JsonResponse(responsedata(True, "Mail sent successfully to the user for song recommendation"), \
                            status=status.HTTP_200_OK)
            except Exception:
                return Response(responsedata(False, "Can't send mail"),status=status.HTTP_400_BAD_REQUEST)        

        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)


# Api for autogenerating playlists for a user
class AutoGeneratePlaylist(generics.ListAPIView):

    def get(self, request, *args, **kwargs):
        try:
            # Checking Authorization
            if not (request.user.is_authenticated):
                return Response(responsedata(False, "You are not authorized"), status=status.HTTP_401_UNAUTHORIZED)

            available_genres = SongTrack.objects.all().values_list('genres', flat=True)
            unique_genres = list(set(sum([data[0].split(",") for data in available_genres], [])))
            chosen_genre = random.choice(unique_genres)

            available_artists = SongTrack.objects.all().values_list('artists', flat=True)
            unique_artists = list(set(sum([data[0].split(",") for data in available_artists], []))) 
            chosen_artists = random.choice(unique_artists)
            
            available_albums = list(SongTrack.objects.all().values_list('album__name', flat=True))
            chosen_album = random.choice(available_albums)

            playlist_choices = [chosen_genre, chosen_artists, chosen_album]

            auto_suggest = random.choice(playlist_choices)

            tracks_to_add = list(SongTrack.objects.filter(Q(genres__icontains=auto_suggest)|Q(album__name__icontains=auto_suggest)|\
                                                Q(artists__icontains=auto_suggest))[:10].values())

            return JsonResponse(responsedata(True, "Auto playlist generated for you based on category - {}".format(auto_suggest), tracks_to_add), \
                            status=status.HTTP_200_OK)                                    

        except Exception:
            return Response(responsedata(False, GENERIC_ERR),status=status.HTTP_400_BAD_REQUEST)
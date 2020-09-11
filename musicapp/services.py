import requests, traceback
from .exceptions import *
from .models import *
from .serializers import *
from .constants import *
from django.db import transaction
from MusicProj.settings import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_BASE_URL, SPOTIFY_AUTH_URL



def call_api(method, request_url, headers={}, querystring={}, data={}, timeout=180):
    ''' Generic fucntion to call any API 
        data format -> {
                        'request_url': url_value,
                        'headers': headers_dict,
                        'params': params_dict
                        }
    '''
    return requests.request(method, request_url, headers=headers, \
                    params=querystring, data=data, timeout=timeout)


# service class for calling Spotify api and locally storing the results in db
class AlbumService:
    @classmethod
    def fetch_songs_from_api(cls, album_tracks_response, headers, track_ids, song_tracks, data):
        try:
            with transaction.atomic():
                for track_data in album_tracks_response.get("items"):
                    with transaction.atomic():
                        genres_det = []
                        artists_det = [value["name"] for value in track_data.get("artists")] if track_data.get("artists") else []
                        artist_ids = [value["id"] for value in track_data.get("artists")]
                        external_urls = track_data["external_urls"].get("spotify") if track_data.get('external_urls') else None

                        track_ids.append(track_data.get("id"))

                        querystring = {"ids" : artist_ids}
                        request_url =  SPOTIFY_BASE_URL + 'artists/' 
                        
                        artist_data = call_api('GET', request_url, headers, querystring).json().get("artists")
                        genres_det = list(set([",".join(data.get("genres")) for data in artist_data]))
                        
                        for details in artist_data:
                            if not Artist.objects.filter(id=details.get("id")).exists():
                                artist_url = details["external_urls"].get("spotify") if details.get('external_urls') else None
                                artist_dict = {"name": details.get("name"),"popularity": details.get("popularity"),\
                                            "external_urls":artist_url}            
                                artist_serializer = ArtistSerializer(data=artist_dict)
                                if artist_serializer.is_valid(raise_exception=True):
                                    artist_serializer.save(id=details.get("id"))            

                        track_dict = {"artists": artists_det, "name": track_data.get("name"), "external_urls":external_urls,
                                    "duration_ms": track_data.get("duration_ms"), "genres": genres_det}
                        try:
                            tracks_serializer = SongTrackSerializer(data=track_dict)
                            if tracks_serializer.is_valid(raise_exception=True):
                                tracks_serializer.save(id=track_data.get("id"))
                                song_tracks.append(tracks_serializer.data)
                        except:
                            pass          

                    data["tracks"] = song_tracks
        except:
            raise SongFetchError(SONG_FETCH_ERROR)


    @classmethod
    def fetch_albums_from_api(cls, response, request_url, headers):
        res_album_data = {}
        try:
            if response.status_code != 200:
                raise ThirdPartyError(SONG_FETCH_ERROR)

            page = response.json()
            album_data = page.get("albums").get("items")

            page_data = {field: page.get("albums").get(field) for field in PAGE_FIELDS}

            for data in album_data:
                id = data.pop("id")
                track_ids, song_tracks = [], []

                querystring = {"limit": 30, "offset": 0}

                request_url =  SPOTIFY_BASE_URL + 'albums/' + '{album_id}/tracks'.format(album_id=id)

                album_tracks_response = call_api('GET', request_url, headers, querystring).json()
 
                dict_keys = list(data.keys())
                remove_fields = list(set(dict_keys) - set(ALBUM_FIELDS))

                for key in remove_fields:
                    data.pop(key)
                
                data["artists"] = [value["name"] for value in data.get('artists')] if data.get('artists') else []
                data["external_urls"] = data["external_urls"].get("spotify") if data.get('external_urls') else None

                res_album_data.update(data)
                try:
                    with transaction.atomic():
                        cls.fetch_songs_from_api(album_tracks_response, headers, track_ids, song_tracks, data)

                        album_id = {"id" : id}
                        instance = Album(**album_id)

                        album_serializer = AlbumSerializer(instance, data=res_album_data)
                        if album_serializer.is_valid(raise_exception=True):
                            album_obj = album_serializer.save()
                            album_obj.tracks.add(*track_ids)                            
                except:
                    raise ThirdPartyError(API_ERROR)
                
            album_data.update(page_data=page_data)
            return album_data

        except (ThirdPartyError, SongFetchError) as e:
            raise APIException(str(e))


    @classmethod
    def get_songs_list(cls, limit, offset):
        try:
            import requests
            if not Album.objects.all()[offset:offset+limit].exists():
                auth_response = call_api('POST', SPOTIFY_AUTH_URL, data={
                            'grant_type': 'client_credentials',
                            'client_id': SPOTIFY_CLIENT_ID,
                            'client_secret': SPOTIFY_CLIENT_SECRET,
                        })

                # convert the response to JSON
                auth_response_data = auth_response.json()

                # save the access token
                access_token = auth_response_data['access_token']

                headers = {
                    'Authorization': 'Bearer {token}'.format(token=access_token)
                }

                querystring = {"limit":limit, "offset":offset}

                request_url =  SPOTIFY_BASE_URL + 'browse/new-releases/'

                api_response = call_api('GET', request_url, headers, querystring)

                album_results = cls.fetch_albums_from_api(api_response, request_url, headers)

            else:
                album_queryset = Album.objects.all()[offset:offset+limit] 
                album_results = AlbumSerializer(album_queryset, many=True).data  
                for data in album_results:
                    album_obj = Album.objects.filter(id=data.get("id")).first()
                    music_tracks = list(album_obj.tracks.values())
                    data.update({"tracks": music_tracks}) 

            return album_results
        
        except (ThirdPartyError, ) as e:
            raise APIException(str(e))   
    

    
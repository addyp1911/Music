from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register('fetch-tracks', AlbumList, basename="fetch-tracks")
router.register('playlist', PlaylistAction, basename="playlist")
router.register('search-songs', SearchSongs, basename="search-songs")



urlpatterns = [
    path('', include(router.urls)),
    path('recommend-songs', RecommendSongs.as_view(), name="recommend-songs"),
    path('autosuggest-songs', AutoSuggest.as_view(), name="autosuggest-songs"),
    path('auto-playlist', AutoGeneratePlaylist.as_view(), name="auto-playlist")
]
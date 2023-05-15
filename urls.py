from django.urls import include, path

from profiles import views

urlpatterns = [
    path("profile/", views.UserProfileView.as_view()),
    path("profile/upload-image/", views.UserProfilePictureUpdate.as_view()),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("profile/liked-songs/", views.LikedSongsListView.as_view()),
    path("profile/artists-followed/", views.FollowedArtistsView.as_view()),
    path("trending-songs", views.TrendingSongView.as_view()),
    # api changes
    path("search/", views.SearchAPIView.as_view()),
    path('suggestions/', views.SuggestionView.as_view(), name='suggestions'),
    path("terms-and-conditions/", views.TermsAndConditionsAPIView.as_view(), name="terms_and_conditions"),
]

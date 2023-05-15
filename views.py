from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.forms.models import model_to_dict
from rest_framework import (
    generics,
    pagination,
    permissions,
    status,
    views,
    viewsets,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.artiste.models import Artiste, AudioMedia
from apps.lib.constants import USER_TYPE_ARTISTE, USER_TYPE_FAN
from apps.lib.models import TermsAndConditions
from profiles import serializers
from profiles.models import Media, Profile
from users.constants import ACCOUNT_TYPE_ARTISTE, ACCOUNT_TYPE_FAN
from users.models import Fan

User = get_user_model()


class UserProfileViewe(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Profile.objects.all()

    def get_object(self):
        return Profile.objects.get_or_create(user=self.request.user)[0]


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.account_type == ACCOUNT_TYPE_FAN:
            return serializers.FanProfileSerializer
        elif self.request.user.account_type == ACCOUNT_TYPE_ARTISTE:
            return serializers.ArtisteProfileSerializer

    def get_queryset(self):
        if self.request.user.account_type == ACCOUNT_TYPE_FAN:
            return Fan.objects.all()
        elif self.request.user.account_type == ACCOUNT_TYPE_ARTISTE:
            return Artiste.objects.all()

    def get_object(self):
        if self.request.user.account_type == ACCOUNT_TYPE_FAN:  # type: ignore
            return Fan.objects.get_or_create(user=self.request.user)[0]
        elif self.request.user.account_type == ACCOUNT_TYPE_ARTISTE:  # type: ignore
            return Artiste.objects.get_or_create(user=self.request.user)[0]

    def get(self, request, *args, **kwargs):
        if self.request.user.account_type == ACCOUNT_TYPE_FAN:  # type: ignore
            obj, _ = Fan.objects.get_or_create(user=self.request.user)
        elif self.request.user.account_type == ACCOUNT_TYPE_ARTISTE:  # type: ignore
            obj, _ = Fan.objects.get_or_create(user=self.request.user)
            obj, _ = Artiste.objects.get_or_create(user=self.request.user)
        response=self.retrieve(request, *args, **kwargs)  
        UserData=User.objects.get(email=response.data.get("email_id"))
        user_dict = model_to_dict(UserData)
        response.data["profile_flag"]=user_dict.get("profile_flag")
        return response


class UserProfilePictureUpdate(views.APIView):
    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get_profile(self, user):
        if user.account_type == ACCOUNT_TYPE_FAN:
            return Fan.objects.get_or_create(user=user)[0]
        elif user.account_type == ACCOUNT_TYPE_ARTISTE:
            return Artiste.objects.get_or_create(user=user)[0]

    @swagger_auto_schema(
        operation_id='Upload Profile Picture',
        operation_description='Upload Profile Picture',
        required=['profile_picture'],
        manual_parameters=[
            openapi.Parameter(
                'profile_picture', openapi.IN_FORM, type=openapi.TYPE_FILE, description='Profile Picture'
            ),
        ],
    )
    def patch(self, request, *args, **kwargs):
        user = request.user
        _user=User.objects.get(email=user.email)
        profile = self.get_profile(user)
        if profile is not None:
            _user.profile_flag=True
            _user.save()
            profile.profile_picture = request.data.get("profile_picture")
            profile.save()
        user_dict = model_to_dict(_user)
        return Response({"detail": "Profile picture updated", "profile_flag": user_dict.get("profile_flag")})

        # return Response({"detail": "Profile picture updated","data":(json.dumps(_user))})


class LikedSongsListView(generics.ListAPIView):
    serializer_class = serializers.MediaSerializer
    queryset = Media.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        return self.request.user.liked_media.all()


class FollowedArtistsView(generics.ListAPIView):
    serializer_class = serializers.ArtisteProfileSerializer
    queryset = Profile.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    pagination_class = pagination.LimitOffsetPagination

    def get_queryset(self):
        followed_artists = self.request.user.followed.all()
        profiles = Profile.objects.filter(user__in=followed_artists)
        return profiles
        # return self.request.user.liked_profiles.all()


class MoreOfWhatYouLikeViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.MoreOfWhatYouLikeSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    queryset = Media.objects.all()
    pagination_class = pagination.PageNumberPagination


class PopularArtistViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ArtisteProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Profile.objects.filter(user__user_type="artist")


class TrendingSongView(generics.ListAPIView):
    queryset = Media.objects.all()
    serializer_class = serializers.MediaSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]


class SearchAPIView(generics.GenericAPIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = serializers.MediaSearchSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(in_=openapi.IN_QUERY, type=openapi.TYPE_STRING, name='search', description='SearchAPI'),
        ]
    )
    def get(self, request, format=None):
        search_query = request.query_params.get('search', None)
        if search_query is None:
            return Response({'error': 'Please provide a search term'}, status=status.HTTP_400_BAD_REQUEST)
        songs = AudioMedia.objects.filter(
            Q(title__icontains=search_query) | Q(album__album_name__icontains=search_query)
        )
        songs_serializer = serializers.SuggestionsSerializer(songs, context={"request": request}, many=True)
        artiste = Artiste.objects.filter(
            Q(stage_name__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )
        artiste_serializer = serializers.ArtisteSerializer(artiste, context={"request": request}, many=True)

        data = {
            'songs': songs_serializer.data,
            'artistes': artiste_serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class SuggestionView(views.APIView):
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get(self, request, format=None):
        most_liked_songs = AudioMedia.objects.prefetch_related('likes').all().order_by('-likes')[:20]
        serializer = serializers.SuggestionsSerializer(most_liked_songs, context={"request": request}, many=True)

        most_liked_artists = Artiste.objects.prefetch_related('followers').all().order_by('-followers')[:20]
        most_liked_artists_serializer = serializers.ArtisteSerializer(
            most_liked_artists, context={"request": request}, many=True
        )

        top_trending_songs = AudioMedia.objects.prefetch_related('comments').all().order_by('-comments')[:20]
        trending_serializer = serializers.SuggestionsSerializer(
            top_trending_songs, context={"request": request}, many=True
        )

        data = {
            'most_liked_songs': serializer.data,
            'most_liked_artists': most_liked_artists_serializer.data,
            'top_trending_songs': trending_serializer.data,
        }
        return Response(data, status=status.HTTP_200_OK)


class TermsAndConditionsAPIView(generics.GenericAPIView):
    serializer_class = serializers.TermsAndConditionsSerializer
    queryset = TermsAndConditions.objects.filter(is_active=True).all()
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        if self.request.user.user_type == "artist":
            return super().get_queryset().filter(user_type=USER_TYPE_ARTISTE).order_by('-updated_datetime').first()
        return super().get_queryset().filter(user_type=USER_TYPE_FAN).order_by('-updated_datetime').first()

    @swagger_auto_schema(responses={200: serializers.TermsAndConditionsSerializer()})
    def get(self, request, format=None):
        serializer = self.serializer_class(self.get_queryset())
        return Response(serializer.data, status=status.HTTP_200_OK)

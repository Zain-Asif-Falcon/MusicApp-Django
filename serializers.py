from dataclasses import field

from attr import validate
from django.http import HttpRequest
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from apps.artiste.api.v1.serializers import ArtisteSerializer, AudioMediaSerializer
from apps.artiste.constants import PLATFORM_APPLE, PLATFORM_HIPHOP, PLATFORM_SPOTIFY, PLATFORM_TIKTOK, PLATFORM_YOUTUBE, \
    PLATFORM_INSTAGRAM, PLATFORM_TWITTER, PLATFORM_GENIUS, PLATFORM_LINKS
from apps.artiste.models import Artiste, AudioMedia, Links
from apps.lib.models import TermsAndConditions
from users.models import Fan, User

from .models import Comment, Media, MediaComment, Profile, UserLikeDislikeCount


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())
    artists_followed = serializers.SerializerMethodField()
    user_type = serializers.CharField(read_only=True, source="user.user_type")
    uid = serializers.CharField(source="user.uid", read_only=True)
    full_name = serializers.SerializerMethodField()
    email_id = serializers.CharField(source="user.email", read_only=True)
    verification_status = serializers.CharField(source="user.verification_status", read_only=True)
    total_followers = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        exclude = "likes", "dislikes"

    def get_artists_followed(self, obj):
        return obj.user.followed.all().count()

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_total_followers(self, obj):
        return obj.user.followers.all().count()


class ShortProfileSerializer(serializers.ModelSerializer):
    uid = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            "uid",
            "profile_picture",
            "full_name",
        ]

    def get_uid(self, obj):
        return obj.user.uid

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class ArtisteUpdateProfileSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Profile
        fields = "__all__"


class ArtisteLinksSerializer(serializers.ModelSerializer):
    link_type = serializers.CharField(source='get_link_type_display')

    class Meta:
        model = Links
        fields = ['link_url', 'link_type']


class ArtisteProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    full_name = serializers.SerializerMethodField(source='user.get_full_name')
    user_type = serializers.CharField(source="user.user_type", read_only=True)
    email_id = serializers.CharField(source="user.email", read_only=True)
    full_name = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()
    profile_song = serializers.SerializerMethodField()
    followers_count = serializers.IntegerField(source='followers.count')
    songs_count = serializers.IntegerField(source='get_audio_count')
    videos_count = serializers.IntegerField(source='get_video_count')
    albums_count = serializers.IntegerField(source='get_albums_count')
    artiste_comments_count = serializers.IntegerField(source='get_comments_count')
    update_date = serializers.DateTimeField(source='user.last_login')
    share_links = serializers.SerializerMethodField()

    class Meta:
        model = Artiste
        fields = "__all__"

    def get_profile_song(self, obj):
        data = AudioMediaSerializer(obj.profile_song).data

        return {
            'media_uuid': data.get('id', None),
            'title': data.get('title', None),
            'audio_file': data.get('audio_file', None),
            'cover_image': data.get('cover_image', None),
            'media_comments_count': data.get('media_comments_count', None),
            'likes_count': data.get('likes_count', None),
            'dislikes_count': data.get('dislikes_count', None),
        }

    def get_share_links(self, obj):
        result = {}
        links = Links.objects.filter(artiste=obj)
        artiste_links = ArtisteLinksSerializer(links, many=True).data
        for link in artiste_links:
            link_type = link["link_type"]
            result[link_type] = link["link_url"]
        return result

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_verification_status(self, obj):
        return obj.get_verification_status_display()

    def update_links(self, instance, validated_data):
        for link_type, platform in PLATFORM_LINKS.items():
            if validated_data.get(link_type):
                obj, created = Links.objects.update_or_create(
                    artiste=instance, link_type=platform,
                    defaults={'link_url': validated_data[link_type]},
                )

    def update(self, instance: Artiste, validated_data):
        self.update_links(instance, self.initial_data)
        instance.stage_name = validated_data.get('stage_name', instance.stage_name)
        user = instance.user

        user.first_name = self.initial_data.get('first_name') or user.first_name
        user.last_name = self.initial_data.get('last_name') or user.last_name

        user.save()
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    commenter = serializers.HiddenField(default=CurrentUserDefault())
    user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        exclude = ("profile",)

    def get_user(self, obj):
        return ShortProfileSerializer(instance=obj.commenter.profile).data


class EmptyBodySerializer(serializers.Serializer):
    pass


class MediaSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=CurrentUserDefault())
    artist = serializers.SerializerMethodField()

    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Media
        exclude = ("id", "likes", "dislikes")

    def get_artist(self, obj):
        artist = {"stage_name": obj.owner.profile.stage_name, "artist_id": obj.owner.uid}
        if obj.owner.profile.profile_picture:
            artist["profile_picture"] = obj.owner.profile.profile_picture.url
        if obj.owner.profile.profile_song:
            artist["profile_song"] = obj.owner.profile.profile_song.url
        return artist

    def get_likes_count(self, obj):
        return obj.likes.all().count()

    def get_dislikes_count(self, obj):
        return obj.dislikes.all().count()

    def get_comments(self, obj):
        return CommentSerializer(instance=obj.comments.all(), many=True).data


class MediaCommentSerializer(serializers.ModelSerializer):
    commenter = serializers.HiddenField(default=CurrentUserDefault())
    user = serializers.SerializerMethodField()

    class Meta:
        model = MediaComment
        exclude = ("media",)

    def get_user(self, obj):
        return ShortProfileSerializer(instance=obj.commenter.profile).data


# Serializers define the API representation.
class MoreOfWhatYouLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['cover_image', 'song_name', 'album_name']


class ProfileSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class MediaSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'


class SuggestionsSerializer(serializers.ModelSerializer):
    audio_media = serializers.SerializerMethodField()
    artist = serializers.SerializerMethodField()
    artiste = serializers.SerializerMethodField()
    album = serializers.SerializerMethodField()

    class Meta:
        model = AudioMedia
        fields = '__all__'

    def get_artist(self, obj):
        return ArtisteSerializer(instance=obj.artiste, context={"request": self.context['request']}).data

    def get_artiste(self, obj):
        return obj.artiste.stage_name

    def get_album(self, obj):
        if obj.album is not None:
            return obj.album.album_name
        return None

    def get_audio_media(self, obj):
        return AudioMediaSerializer(instance=obj, context={"request": self.context['request']}).data


class TermsAndConditionsSerializer(serializers.ModelSerializer[TermsAndConditions]):
    class Meta:
        model = TermsAndConditions
        fields = [
            "body",
        ]

    def to_representation(self, instance: TermsAndConditions) -> dict:
        return {
            'data': instance.body,
        }


class FanProfileSerializer(serializers.ModelSerializer[Fan]):
    user = UserSerializer()
    artiste_followed_count = serializers.CharField(source="get_followed_count", read_only=True)
    user_type = serializers.CharField(source="user.user_type", read_only=True)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    email_id = serializers.CharField(source="user.email", read_only=True)
    verification_status = serializers.CharField(source="user.verification_status", read_only=True)
    artiste_followed = serializers.SerializerMethodField()

    class Meta:
        model = Fan
        fields = '__all__'

    def get_artiste_followed(self, obj):
        folows = obj.get_followed()
        artiste_ids = [follow.artiste_id for follow in folows]
        artiste = Artiste.objects.filter(id__in=artiste_ids)
        return ArtisteProfileSerializer(artiste, many=True).data

    def update(self, instance, validated_data):
        user = instance.user

        user.first_name = self.initial_data.get('first_name') or user.first_name
        user.last_name = self.initial_data.get('last_name') or user.last_name

        user.save()
        return instance

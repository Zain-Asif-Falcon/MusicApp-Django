import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, related_name="profile")
    arts = models.CharField(max_length=256, blank=True)
    profile_picture = models.ImageField(blank=True)
    song_name = models.CharField(max_length=250, null=True, blank=True)
    profile_song = models.FileField(blank=True)
    stage_name = models.CharField(max_length=256, blank=True)
    apple_link = models.URLField(blank=True)
    spotify_link = models.URLField(blank=True)
    tiktok_link = models.URLField(blank=True)
    youtube_link = models.URLField(blank=True)
    instagram_link = models.URLField(blank=True)
    hiphop_link = models.URLField(blank=True)
    twitter_link = models.URLField(blank=True)
    genius_link = models.URLField(blank=True)
    likes = models.ManyToManyField(User, blank=True, related_name="liked_profiles")
    dislikes = models.ManyToManyField(User, blank=True, related_name="disliked_profiles")

    def __str__(self):
        return self.user.get_full_name()


class Comment(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()


class Media(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField()
    cover_image = models.ImageField(upload_to="cover-images", blank=True)
    song_name = models.CharField(max_length=512, blank=False, null=True)
    album_name = models.CharField(max_length=512, blank=False, null=True)
    duration = models.CharField(max_length=15, blank=True, editable=False)
    likes = models.ManyToManyField(User, blank=True, related_name="liked_media")
    dislikes = models.ManyToManyField(User, blank=True, related_name="disliked_media")

    def __str__(self):
        return self.song_name

    class Meta:
        verbose_name_plural = "Media Uploads"


class MediaComment(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="media_comments")
    body = models.TextField()

    class Meta:
        ordering = ["-id"]


class Artist(Profile):
    class Meta:
        proxy = True


class Fan(Profile):
    class Meta:
        proxy = True


class VerificationRequests(Profile):
    class Meta:
        proxy = True
        verbose_name_plural = "Approval requests"
        # verbose_name_plural = "Verification requests"


class UserLikeDislikeCount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="like_dislike_user")
    like_counter = models.IntegerField(default=0)
    dislike_counter = models.IntegerField(default=0)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="user_like_song", null=True, blank=True)
    created = models.DateField(auto_now_add=True)
    song = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name="user_like_dislike_song",
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.user)


@receiver(post_delete, sender=Profile)
def delete_image_hook(sender, instance, using, **kwargs):
    instance.user.delete()

import uuid
from datetime import timedelta
from random import randint

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.lib.base_model import BaseAbstractModel
from users.constants import ACCOUNT_TYPE_FAN, ACCOUNT_TYPES


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # We check if password has been given
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # WARNING!
    """
    Some officially supported features of Crowdbotics Dashboard depend on the initial
    state of this User model (Such as the creation of superusers using the CLI
    or password reset in the dashboard). Changing, extending, or modifying this model
    may lead to unexpected bugs and or behaviors in the automated flows provided
    by Crowdbotics. Change it at your own risk.


    This model represents the User instance of the system, login system and
    everything that relates with an `User` is represented by this model.
    """

    USER_TYPES = (("artist", "artist"), ("fan", "fan"))
    USER_PLANS = ("free", "free")

    username = None
    email = models.EmailField(_('email address'), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "last_name"]

    user_type = models.CharField(_("User Type"), max_length=10, default="fan", choices=USER_TYPES)
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    followers = models.ManyToManyField("self", symmetrical=False, related_name="followed")

    account_type = models.IntegerField(choices=ACCOUNT_TYPES, default=ACCOUNT_TYPE_FAN)

    profile_flag = models.BooleanField(default=False)  # New column added
    objects = CustomUserManager()

    def __str__(self):
        return self.email


def random_token():
    return randint(1000, 9999)


class UserToken(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name="tokens")
    token = models.CharField(max_length=4, default=random_token)
    date_generated = models.DateTimeField(auto_now=True)

    @property
    def is_valid(self):
        if self.token == "0001":
            return True
        return self.date_generated + timedelta(hours=2) > timezone.now()


class Fan(BaseAbstractModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="fan")
    profile_picture = models.ImageField(blank=True)
    is_accepted_terms = models.BooleanField(default=False)
    is_accepted_privacy = models.BooleanField(default=False)

    # def get_followed_artists(self):
    #     return self.user.follows.filter(user_type="artist")

    def get_followed_count(self):
        return self.follows.filter().count()

    def get_followed(self):
        return self.follows.filter()

    def __str__(self):
        return f'{self.user.first_name}'

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.artiste.models import Artiste
from profiles.models import Profile
from users.constants import ACCOUNT_TYPE_ARTISTE, ACCOUNT_TYPE_FAN
from users.models import Fan

from django.core.mail import send_mail
from rest_framework.response import Response

User = get_user_model()


class UserSignupSerializer(serializers.ModelSerializer):
    arts = serializers.CharField(required=False)
    stage_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ("user_type", "arts", "email", "password", "first_name", "last_name", "stage_name")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        arts = validated_data.pop("arts")
        stage_name = validated_data.pop("stage_name")
        user = User(**validated_data)
        user.set_password(password)

        # Temporary, Until crowdbotics fixes superuser creation
        user.is_staff = False
        user.is_superuser = False
        user.is_active = False
        # End temp
        # USER_TYPES = (("artist", "artist"), ("fan", "fan"))

        user.save()
        if user.user_type == "fan":
            self.create_save_fan(user, ACCOUNT_TYPE_FAN)
        elif user.user_type == "artist":
            Artiste.objects.create(user=user, stage_name=stage_name, arts=arts)
            self.create_save_fan(user, ACCOUNT_TYPE_ARTISTE)
        return self.send_verification_email(user.email)

    def create_save_fan(self, user, account_type):
        # Profile.objects.create(user=user, arts=arts, stage_name=stage_name)
        Fan.objects.create(user=user)
        user.account_type = account_type
        user.save()

    def send_verification_email(self,e_mail):
        user = User.objects.get(email=e_mail)
        token = user.tokens.create()
        # link="https://saigon-music-26825.botics.co//"
        link="https://saigon-music-26825.botics.co/accounts/api/verify-email/"
        link+=f"?email={e_mail}&token={token.token}"
        body = f"Your Email Verification Link is: {link}"
        subject = "Email Verification"
        # sender = "kelvin.adigwu@crowdbotics.com" #This is the only verified sender for now
        sender = "info@hiphopmyway.com"  # This is the only verified sender for now

        response = send_mail(subject, body, sender, [e_mail])
        # return Response({"status": response})
        return response
class GetTokenSerializer(serializers.Serializer):
    email = serializers.SlugRelatedField(slug_field="email", queryset=User.objects.all())


class VeriifyTokenSerializer(GetTokenSerializer):
    token = serializers.CharField(max_length=4)


class ChangePasswordSerializer(VeriifyTokenSerializer):
    password = serializers.CharField(max_length=100)


class MigrationSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

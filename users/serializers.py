from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
                        }

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email is required.')
        return value

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # Hash the password
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField() #ailarfarzane
    password = serializers.CharField(write_only=True) #1234

    def validate(self, data):
        return data




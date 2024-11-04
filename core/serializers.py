from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    role = serializers.CharField(default='user')
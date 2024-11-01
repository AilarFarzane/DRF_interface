from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversation(models.Model):
    user_role = models.CharField(max_length=50)
    assistant_role = models.CharField(max_length=50, default='gpt-4o-mini')  # Default role for the assistant
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.id} - User: {self.user_role} - Assistant: {self.assistant_role}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    role = models.CharField(max_length=10)  # 'user' or 'assistant'
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role.capitalize()} - {self.created_at}: {self.content[:50]}..."

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):

    #total_tokens = models.IntegerField(default=1000)  # Total tokens the user has
    remaining_tokens = models.IntegerField(default=1000)  # Tokens left for the user

    def __str__(self):
        return self.username

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.contrib.auth.hashers import make_password

class CustomUserManager(UserManager):
    
    def create_user(self, username, email=None, password=None):
        user = self.model(username=username)

        user.set_password(password)
        user.save(using=self._db)
        return user
    
class User(AbstractUser):
    
    objects = CustomUserManager()
    
    REQUIRED_FIELDS = ['email']
    
    is_bot = models.BooleanField(default=False, editable=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
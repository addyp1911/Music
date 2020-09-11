from django.db import models
import uuid, datetime
from .managers import UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin


# Create your models here.
class BaseModel(models.Model):
    """A base model to deal with all the abstract level model creations"""
    class Meta:
        abstract = True

    # uuid field
    uid = models.UUIDField(default=uuid.uuid4,
                           primary_key=True,
                           editable=False)
    # date fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# Create a user model
class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """A ORM for user interactions"""
    
    user_name = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    password = models.CharField(max_length=100)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

 
    # str function to return name instead of object
    def __str__(self):
        """Return full name in representation instead of user object"""
        return self.first_name + ' ' + self.last_name

    class Meta:
        """A meta object for defining name of the user table"""
        db_table = "user"    

    # use User manager to manage create user and super user
    objects = UserManager()

    # define required fields
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
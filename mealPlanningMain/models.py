from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.validators import MaxValueValidator
from django.core.mail import send_mail
from django.conf import settings

# Create your models here.
GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
)

DIETARY_PREFERENCES_CHOICES = (
    ('VEG', 'Vegetarian'),
    ('VGN', 'Vegan'),
    ('GF', 'Gluten-Free'),
    ('HF', 'Halal'),
    ('KF', 'Kosher'),
    ('NO', 'None'),
)


class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(200)],
                                      help_text="Please enter an age up to 200.")
    weight = models.FloatField(null=True, blank=True, help_text="kg")
    height = models.FloatField(null=True, blank=True, help_text="cm")
    dietary_preferences = models.CharField(max_length=3, choices=DIETARY_PREFERENCES_CHOICES, default='NO')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    #
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']

    # def __str__(self):
    #     return self.email

    def send_verification_email(self):
        subject = 'Verify your email'
        message = 'Here is the message for verifying your email address.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email])


class Food(models.Model):
    name = models.CharField(max_length=100)

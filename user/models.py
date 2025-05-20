from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.utils.translation import gettext_lazy as _
class UserManager(BaseUserManager):
    """
    Custom manager for User model without username field.
    """
    use_in_migrations = True

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("The Phone field must be set")
        extra_fields.setdefault('is_active', True)
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone, password, **extra_fields)
class Profession(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
class User(AbstractUser):
    """
        user class
        user_type: 1 for admin, 2 for student, 3 for accanomer
    """
    USER_TYPE_CHOICES = [
        (1,'simple'),
        (2, 'expert'),
        (3, 'company'),
    ]
    user_type = models.IntegerField(choices=USER_TYPE_CHOICES, default=2)
    # Add related_name to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='student_user_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='student_user_set'
    )

    def __str__(self):
        return self.username
    # 
    phone = models.CharField(max_length=20, blank=True, null=True,unique=True)
    name = models.CharField(max_length=20, blank=True, null=True)
    second_name = models.CharField(max_length=20, blank=True, null=True)
    profession = models.ManyToManyField(Profession, related_name='users', blank=True)
    username = models.CharField(max_length=255,blank=True,null=True,unique=True)
    bio = models.TextField(blank=True, null=True)
    img = models.ImageField(upload_to='users/', blank=True, null=True)
    # background_img = models.ImageField(upload_to='users/backgrounds/', blank=True, null=True)
    objects  = UserManager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []
    is_new = models.BooleanField(default=True)
    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        verbose_name = "Foydalanuvchilar"
        verbose_name_plural = "Foydalanuvchilar"
        db_table = "users"

    def __str__(self):
        return self.phone
class SmSCode(models.Model):
    """
        Sms code for phone verification
    """
    phone = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    # Add a timestamp for when the code was created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone
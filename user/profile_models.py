from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os

def get_achievement_image_path(instance, filename):
    """Generate a unique filename for uploaded achievement images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('achievement_images', str(timezone.now().year), 
                       str(timezone.now().month), filename)

def get_portfolio_image_path(instance, filename):
    """Generate a unique filename for uploaded portfolio images"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('portfolio_images', str(timezone.now().year), 
                       str(timezone.now().month), filename)

class Skill(models.Model):
    """
    Model for user skills (IT skills, languages, etc.)
    """
    CATEGORY_CHOICES = [
        ('it', 'IT bilimlar'),
        ('language', 'Chet tillari'),
        ('other', 'Boshqa ko\'nikmalar'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    rating = models.IntegerField(default=0)  # Rating out of 10
    icon = models.CharField(max_length=100, blank=True, null=True)  # Icon identifier or class
    date_added = models.DateField(default=timezone.now)
    
    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        ordering = ['-rating', 'category']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()}) - {self.rating}/10"

class Achievement(models.Model):
    """
    Model for user achievements
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to=get_achievement_image_path, blank=True, null=True)
    date = models.DateField()
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.date.strftime('%Y-%m')}"

class PortfolioItem(models.Model):
    """
    Model for portfolio items
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_items')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    date_completed = models.DateField()
    
    class Meta:
        verbose_name = "Portfolio Item"
        verbose_name_plural = "Portfolio Items"
        ordering = ['-date_completed']
    
    def __str__(self):
        return f"{self.title} - {self.date_completed.strftime('%Y-%m')}"

class PortfolioImage(models.Model):
    """
    Model for portfolio item images (multiple images per portfolio item)
    """
    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=get_portfolio_image_path)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Portfolio Image"
        verbose_name_plural = "Portfolio Images"
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"Image for {self.portfolio_item.title}"

class UserTag(models.Model):
    """
    Model for user tags/skills shown as tags on profile
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Tag"
        verbose_name_plural = "User Tags"
        unique_together = ('user', 'name')
        ordering = ['name']
    
    def __str__(self):
        return self.name

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os

def get_story_file_path(instance, filename):
    """Generate a unique filename for uploaded story files"""
    # Get the file extension
    ext = filename.split('.')[-1]
    # Generate a unique filename with uuid
    filename = f"{uuid.uuid4().hex}.{ext}"
    # Return the path with year/month/day structure
    return os.path.join('story_media', str(timezone.now().year), 
                       str(timezone.now().month), 
                       str(timezone.now().day), 
                       filename)

class Story(models.Model):
    """
    Model for user stories with a single media item (image or video)
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    content = models.TextField(blank=True, null=True)
    media = models.FileField(upload_to=get_story_file_path, max_length=500)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    duration = models.IntegerField(default=24)  # Duration in hours before story expires
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "Story"
        verbose_name_plural = "Stories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Story by {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def expires_at(self):
        """Return the expiration time of the story"""
        return self.created_at + timezone.timedelta(hours=self.duration)
    
    @property
    def is_expired(self):
        """Check if the story has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def filename(self):
        """Return the filename of the media"""
        return self.media.name.split('/')[-1]
    
    @property
    def file_url(self):
        """Return the URL of the media file"""
        return self.media.url if self.media else None

class StoryView(models.Model):
    """
    Model for tracking who has viewed a story
    """
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='viewed_stories')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Story View"
        verbose_name_plural = "Story Views"
        unique_together = ('story', 'viewer')  # A user can only view a story once (for tracking purposes)
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.viewer.username} viewed story by {self.story.user.username}"

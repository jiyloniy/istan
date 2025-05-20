from django.db import models
from django.conf import settings
from django.utils import timezone

class Post(models.Model):
    """
    Model for user posts with media content
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(blank=True, null=True)
    location_name = models.CharField(max_length=255, blank=True, null=True)
    is_public = models.BooleanField(default=True)
    allow_comments = models.BooleanField(default=True)
    allow_likes = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Post by {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def main_media(self):
        """Return the main media for this post"""
        return self.media_items.filter(is_main=True).first()
    
    @property
    def additional_media(self):
        """Return all additional media for this post"""
        return self.media_items.filter(is_main=False)
    
    @property
    def media_count(self):
        """Return the count of all media items for this post"""
        return self.media_items.count()


import uuid
import os

def get_file_path(instance, filename):
    """Generate a unique filename for uploaded files"""
    # Get the file extension
    ext = filename.split('.')[-1]
    # Generate a unique filename with uuid
    filename = f"{uuid.uuid4().hex}.{ext}"
    # Return the path with year/month/day structure
    return os.path.join('post_media', str(timezone.now().year), 
                       str(timezone.now().month), 
                       str(timezone.now().day), 
                       filename)

class MediaItem(models.Model):
    """
    Model for media items (images, videos) attached to posts
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_items')
    file = models.FileField(upload_to=get_file_path, max_length=500)  # Increased max_length and custom upload path
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Media Item"
        verbose_name_plural = "Media Items"
        ordering = ['is_main', 'created_at']
    
    def __str__(self):
        return f"{self.media_type} for post {self.post.id}"
    
    @property
    def filename(self):
        return self.file.name.split('/')[-1]
    
    @property
    def file_url(self):
        return self.file.url if self.file else None


class PostLike(models.Model):
    """
    Model for post likes
    """
    LIKE_TYPES = [
        ('like', 'Like'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    like_type = models.CharField(max_length=10, choices=LIKE_TYPES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Post Like"
        verbose_name_plural = "Post Likes"
        unique_together = ('post', 'user')  # A user can only have one reaction per post
    
    def __str__(self):
        return f"{self.user.username} {self.like_type}d post {self.post.id}"


class PostComment(models.Model):
    """
    Model for post comments
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Post Comment"
        verbose_name_plural = "Post Comments"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on post {self.post.id}"


class SavedPost(models.Model):
    """
    Model for saved posts (bookmarks)
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Saved Post"
        verbose_name_plural = "Saved Posts"
        unique_together = ('post', 'user')  # A user can only save a post once
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved post {self.post.id}"


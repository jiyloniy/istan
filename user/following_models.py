from django.db import models
from django.conf import settings
from django.utils import timezone

class UserFollowing(models.Model):
    """
    Model for user following relationships
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='following'
    )
    following_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "User Following"
        verbose_name_plural = "User Followings"
        unique_together = ('user', 'following_user')  # A user can only follow another user once
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} follows {self.following_user.username}"

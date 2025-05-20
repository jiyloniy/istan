from django.contrib import admin
from .models import User, Profession, SmSCode
from .post_models import Post, MediaItem, PostLike, PostComment, SavedPost
from .story_models import Story, StoryView
from .following_models import UserFollowing

# Register your models here.

@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('-id',)
    list_per_page = 10
    list_display_links = ('id', 'name')
@admin.register(SmSCode)
class SmSCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'code', 'is_verified')
    search_fields = ('phone',)
    ordering = ('-id',)
    list_per_page = 10
    list_display_links = ('id', 'phone')
    fieldsets = (
        (None, {
            'fields': ('phone', 'code', 'is_verified')
        }),
    )

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'caption', 'is_public', 'created_at')
    list_filter = ('is_public', 'allow_comments', 'allow_likes')
    search_fields = ('caption', 'user__username')
    ordering = ('-created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'

@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'media_type', 'is_main', 'created_at')
    list_filter = ('media_type', 'is_main')
    search_fields = ('post__caption',)
    ordering = ('-created_at',)
    list_per_page = 20

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__caption', 'user__username')
    ordering = ('-created_at',)
    list_per_page = 20

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username', 'post__caption')
    ordering = ('-created_at',)
    list_per_page = 20

@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('post__caption', 'user__username')
    ordering = ('-created_at',)
    list_per_page = 20

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'media_type', 'duration', 'is_public', 'created_at')
    list_filter = ('media_type', 'is_public', 'created_at')
    search_fields = ('user__username', 'content')
    ordering = ('-created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'

@admin.register(StoryView)
class StoryViewAdmin(admin.ModelAdmin):
    list_display = ('id', 'story', 'viewer', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('story__user__username', 'viewer__username')
    ordering = ('-viewed_at',)
    list_per_page = 20

@admin.register(UserFollowing)
class UserFollowingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'following_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'following_user__username')
    ordering = ('-created_at',)
    list_per_page = 20

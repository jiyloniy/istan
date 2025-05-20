from django.urls import path
from .views import SmsGenerateView, SmsVerifyView, GetProfession,UserPartialCreate,UserView,PostContetn,StoryCreate,MyStoriesView,FeedStoriesView,ViewStoryView
from .following_views import FollowUserView, GetFollowersView, GetFollowingView, RandomizedPostFeedView
from .post_interaction_views import LikePostView, CommentPostView, GetPostCommentsView, DeleteCommentView, SavePostView, GetSavedPostsView
from .profile_views import UserProfileView, SkillView, AchievementView, PortfolioItemView, UserTagView, CompactProfileView
from .profile_update_views import ProfileUpdateView
from .media_filter_views import MediaFilteredPostsView, UserPostsView
urlpatterns = [
    path('sms/generate/', SmsGenerateView.as_view(), name='sms-generate'),
    path('sms/verify/', SmsVerifyView.as_view(), name='sms-verify'),
    path('get-profession/', GetProfession.as_view(), name='get-profession'),
    path('partial-create/', UserPartialCreate.as_view(), name='user-partial-create'),
    path('me/', UserView.as_view(), name='get-user'),
    path('post/create/', PostContetn.as_view(), name='post-create'),
    path('story/create/', StoryCreate.as_view(), name='story-create'),
    path('story/my-stories/', MyStoriesView.as_view(), name='my-stories'),
    path('story/feed/', FeedStoriesView.as_view(), name='feed-stories'),
    path('story/view/<int:story_id>/', ViewStoryView.as_view(), name='view-story'),
    # User following endpoints
    path('follow/<int:user_id>/', FollowUserView.as_view(), name='follow-user'),
    path('followers/', GetFollowersView.as_view(), name='get-followers'),
    path('following/', GetFollowingView.as_view(), name='get-following'),
    # Post feed endpoint
    path('posts/feed/', RandomizedPostFeedView.as_view(), name='randomized-post-feed'),
    path('posts/media-filter/', MediaFilteredPostsView.as_view(), name='media-filtered-posts'),
    path('posts/user/', UserPostsView.as_view(), name='user-posts'),
    # Post interaction endpoints
    path('posts/<int:post_id>/like/', LikePostView.as_view(), name='like-post'),
    path('posts/<int:post_id>/comment/', CommentPostView.as_view(), name='comment-post'),
    path('posts/<int:post_id>/comments/', GetPostCommentsView.as_view(), name='get-post-comments'),
    path('comments/<int:comment_id>/', DeleteCommentView.as_view(), name='delete-comment'),
    path('posts/<int:post_id>/save/', SavePostView.as_view(), name='save-post'),
    path('posts/saved/', GetSavedPostsView.as_view(), name='get-saved-posts'),
    # Profile endpoints
    path('profile/', UserProfileView.as_view(), name='own-profile'),
    path('profile/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
    path('profile/skills/', SkillView.as_view(), name='add-skill'),
    path('profile/skills/<int:skill_id>/', SkillView.as_view(), name='delete-skill'),
    path('profile/achievements/', AchievementView.as_view(), name='add-achievement'),
    path('profile/achievements/<int:achievement_id>/', AchievementView.as_view(), name='delete-achievement'),
    path('profile/portfolio/', PortfolioItemView.as_view(), name='add-portfolio-item'),
    path('profile/portfolio/<int:portfolio_item_id>/', PortfolioItemView.as_view(), name='delete-portfolio-item'),
    path('profile/tags/', UserTagView.as_view(), name='add-tag'),
    path('profile/tags/<int:tag_id>/', UserTagView.as_view(), name='delete-tag'),
    path('profile/compact/', CompactProfileView.as_view(), name='compact-profile'),
    path('profile/compact/<int:user_id>/', CompactProfileView.as_view(), name='compact-user-profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='update-profile'),
    path('profile/update/<int:user_id>/', ProfileUpdateView.as_view(), name='update-user-profile'),
]
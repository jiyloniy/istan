from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count, Exists, OuterRef
from .response import CustomResponse as Response
from .models import User
from .following_models import UserFollowing
from .post_models import Post
import random

class FollowUserView(APIView):
    """
    View for following/unfollowing a user
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, user_id):
        try:
            # Get the user to follow
            user_to_follow = get_object_or_404(User, id=user_id)
            
            # Check if user is trying to follow themselves
            if request.user.id == user_id:
                return Response.error(
                    message="You cannot follow yourself", 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if already following
            following_exists = UserFollowing.objects.filter(
                user=request.user,
                following_user=user_to_follow
            ).exists()
            
            if following_exists:
                # If already following, unfollow
                UserFollowing.objects.filter(
                    user=request.user,
                    following_user=user_to_follow
                ).delete()
                
                return Response.success(
                    message=f"You have unfollowed {user_to_follow.username}",
                    status=status.HTTP_200_OK
                )
            else:
                # If not following, follow
                UserFollowing.objects.create(
                    user=request.user,
                    following_user=user_to_follow
                )
                
                return Response.success(
                    message=f"You are now following {user_to_follow.username}",
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            return Response.error(
                message=f"Error processing request: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class GetFollowersView(APIView):
    """
    View for getting a user's followers
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all followers of the current user
            followers = UserFollowing.objects.filter(following_user=request.user)
            
            # Prepare response data
            followers_data = []
            for follower in followers:
                followers_data.append({
                    'id': follower.user.id,
                    'username': follower.user.username,
                    'name': follower.user.name,
                    'second_name': follower.user.second_name,
                    'profile_picture': follower.user.img.url if follower.user.img else None,
                    'followed_at': follower.created_at
                })
            
            return Response.success(
                data={'followers': followers_data},
                message='Followers retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving followers: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class GetFollowingView(APIView):
    """
    View for getting users that the current user is following
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all users that the current user is following
            following = UserFollowing.objects.filter(user=request.user)
            
            # Prepare response data
            following_data = []
            for follow in following:
                following_data.append({
                    'id': follow.following_user.id,
                    'username': follow.following_user.username,
                    'name': follow.following_user.name,
                    'second_name': follow.following_user.second_name,
                    'profile_picture': follow.following_user.img.url if follow.following_user.img else None,
                    'followed_at': follow.created_at
                })
            
            return Response.success(
                data={'following': following_data},
                message='Following users retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving following users: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class RandomizedPostFeedView(APIView):
    """
    View for getting a randomized feed of posts from followed users
    with the current user's latest post at the top if it exists.
    For new users with no following relationships, shows random posts from other users.
    Implements pagination with 10 posts per page.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = 10  # Fixed page size of 10 posts per request
            
            # Get all users that the current user is following
            following_users = UserFollowing.objects.filter(user=request.user).values_list('following_user', flat=True)
            
            # Get the latest post from the current user (if any)
            user_latest_post = Post.objects.filter(user=request.user).order_by('-created_at').first()
            
            # Check if the user is following anyone
            has_following = following_users.exists()
            
            # Get all posts for the feed (we'll paginate later)
            if has_following:
                # Get posts from followed users
                feed_posts = Post.objects.filter(
                    user__in=following_users,
                    is_public=True
                ).select_related('user').prefetch_related('media_items')
            else:
                # For new users with no following relationships, get random public posts from other users
                # Exclude the user's own posts to avoid duplication (we'll add the latest one separately)
                feed_posts = Post.objects.filter(
                    is_public=True
                ).exclude(user=request.user).select_related('user').prefetch_related('media_items')
                
                # Limit to 10 random posts for new users
                feed_posts = feed_posts.order_by('?')[:10]
            
            # Convert queryset to list for randomization
            posts_list = list(feed_posts)
            
            # Randomize the order
            random.shuffle(posts_list)
            
            # If the user has a latest post and we're on the first page, add it to the beginning
            if user_latest_post and page == 1:
                # Check if the post is already in the list (could happen if user follows themselves)
                if user_latest_post not in posts_list:
                    posts_list.insert(0, user_latest_post)
                    
            # Calculate total posts and pages
            total_posts = len(posts_list)
            total_pages = (total_posts + page_size - 1) // page_size  # Ceiling division
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_posts)
            
            # Get the paginated subset of posts
            paginated_posts = posts_list[start_idx:end_idx]
            
            # Prepare response data
            posts_data = []
            for post in paginated_posts:  # Use paginated_posts instead of posts_list
                # Get the main media for the post
                main_media = post.main_media
                
                # Get additional media items
                additional_media_items = []
                for media in post.additional_media:
                    additional_media_items.append({
                        'id': media.id,
                        'media_type': media.media_type,
                        'file_url': media.file_url,
                        'filename': media.filename
                    })
                
                # Check if the current user has liked this post
                has_liked = post.likes.filter(user=request.user).exists()
                
                # Check if the current user has saved this post
                has_saved = post.saved_by.filter(user=request.user).exists()
                
                posts_data.append({
                    'id': post.id,
                    'user': {
                        'id': post.user.id,
                        'username': post.user.username,
                        'name': post.user.name,
                        'profile_picture': post.user.img.url if post.user.img else None,
                    },
                    'caption': post.caption,
                    'location_name': post.location_name,
                    'created_at': post.created_at,
                    'likes_count': post.likes.count(),
                    'comments_count': post.comments.count(),
                    'has_liked': has_liked,
                    'has_saved': has_saved,
                    'main_media': {
                        'id': main_media.id if main_media else None,
                        'media_type': main_media.media_type if main_media else None,
                        'file_url': main_media.file_url if main_media else None,
                        'filename': main_media.filename if main_media else None
                    } if main_media else None,
                    'additional_media': additional_media_items,
                    'is_own_post': post.user.id == request.user.id
                })
            
            # Add pagination information to the response
            pagination_info = {
                'current_page': page,
                'total_pages': total_pages,
                'page_size': page_size,
                'total_posts': total_posts,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
            
            return Response.success(
                data={
                    'posts': posts_data,
                    'pagination': pagination_info
                },
                message='Post feed retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving post feed: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

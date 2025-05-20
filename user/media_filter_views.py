from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Exists, OuterRef
import random

from .response import CustomResponse as Response
from .post_models import Post, MediaItem, PostLike, SavedPost
from django.contrib.auth import get_user_model


class UserPostsView(APIView):
    """
    View for getting posts of a specific user
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get user_id from query params (if not provided, use the authenticated user's id)
            user_id = request.query_params.get('user_id', request.user.id)
            
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = 10  # Fixed page size of 10 posts per request
            
            # Get the user
            User = get_user_model()
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response.error(
                    message="User not found",
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all posts by the user
            user_posts = Post.objects.filter(
                user=target_user
            ).select_related('user').prefetch_related('media_items')
            
            # Apply ordering
            user_posts = user_posts.order_by('-created_at')
            
            # Count total posts
            total_posts = user_posts.count()
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            # Get paginated posts
            paginated_posts = user_posts[start_idx:end_idx]
            
            # Process posts
            posts_data = self._process_posts(request, paginated_posts)
            
            # Calculate pagination info
            total_pages = (total_posts + page_size - 1) // page_size  # Ceiling division
            
            pagination_info = {
                'current_page': page,
                'total_pages': total_pages,
                'page_size': page_size,
                'total_posts': total_posts,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
            
            # Return user posts
            return Response.success(
                data={
                    'user': {
                        'id': target_user.id,
                        'username': target_user.username,
                        'name': target_user.name if hasattr(target_user, 'name') else target_user.username,
                        'profile_picture': target_user.img.url if hasattr(target_user, 'img') and target_user.img else None,
                    },
                    'is_own_profile': target_user.id == request.user.id,
                    'posts': posts_data,
                    'pagination': pagination_info
                },
                message='User posts retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving user posts: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _process_posts(self, request, posts):
        """Helper method to process posts and format them for the response"""
        posts_data = []
        
        for post in posts:
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
                    'name': post.user.name if hasattr(post.user, 'name') else post.user.username,
                    'profile_picture': post.user.img.url if hasattr(post.user, 'img') and post.user.img else None,
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
        
        return posts_data


class MediaFilteredPostsView(APIView):
    """
    View for getting posts filtered by media type (image or video)
    Returns separate lists for image posts and video posts
    """
    authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]``
    
    def get(self, request):
        try:
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = 10  # Fixed page size of 10 posts per request
            
            # Get media type filter (optional)
            media_type = request.query_params.get('media_type', None)
            
            # Base query for posts with media items
            base_query = Post.objects.filter(
                is_public=True
            ).select_related('user').prefetch_related('media_items')
            
            # Get posts with images
            image_posts = base_query.filter(
                media_items__media_type='image'
            ).distinct()
            
            # Get posts with videos
            video_posts = base_query.filter(
                media_items__media_type='video'
            ).distinct()
            
            # If media_type is specified, filter by that type only
            if media_type == 'image':
                posts_to_process = image_posts
                total_posts = image_posts.count()
            elif media_type == 'video':
                posts_to_process = video_posts
                total_posts = video_posts.count()
            else:
                # If no media_type specified, we'll return both in separate lists
                # For pagination, we'll use the combined count
                total_posts = image_posts.count() + video_posts.count()
                
                # Apply ordering
                image_posts = image_posts.order_by('-created_at')
                video_posts = video_posts.order_by('-created_at')
                
                # Apply pagination to both lists
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                
                # Get paginated image posts
                paginated_image_posts = image_posts[start_idx:end_idx]
                
                # Get paginated video posts
                paginated_video_posts = video_posts[start_idx:end_idx]
                
                # Process both lists
                image_posts_data = self._process_posts(request, paginated_image_posts)
                video_posts_data = self._process_posts(request, paginated_video_posts)
                
                # Calculate pagination info
                total_pages = (total_posts + page_size - 1) // page_size  # Ceiling division
                
                pagination_info = {
                    'current_page': page,
                    'total_pages': total_pages,
                    'page_size': page_size,
                    'total_posts': total_posts,
                    'has_next': page < total_pages,
                    'has_previous': page > 1
                }
                
                # Return both lists
                return Response.success(
                    data={
                        'image_posts': image_posts_data,
                        'video_posts': video_posts_data,
                        'pagination': pagination_info
                    },
                    message='Media filtered posts retrieved successfully',
                    status=status.HTTP_200_OK
                )
            
            # If we're here, we're filtering by a specific media type
            # Apply ordering
            posts_to_process = posts_to_process.order_by('-created_at')
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            # Get paginated posts
            paginated_posts = posts_to_process[start_idx:end_idx]
            
            # Process posts
            posts_data = self._process_posts(request, paginated_posts)
            
            # Calculate pagination info
            total_pages = (total_posts + page_size - 1) // page_size  # Ceiling division
            
            pagination_info = {
                'current_page': page,
                'total_pages': total_pages,
                'page_size': page_size,
                'total_posts': total_posts,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
            
            # Return filtered posts
            return Response.success(
                data={
                    'posts': posts_data,
                    'pagination': pagination_info
                },
                message=f'{media_type.capitalize()} posts retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving media filtered posts: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _process_posts(self, request, posts):
        """Helper method to process posts and format them for the response"""
        posts_data = []
        
        for post in posts:
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
        
        return posts_data

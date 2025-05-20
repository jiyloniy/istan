from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .response import CustomResponse as Response
from .post_models import Post, PostLike, PostComment, SavedPost

class LikePostView(APIView):
    """
    View for liking/unliking a post
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, post_id):
        try:
            # Get the post
            post = get_object_or_404(Post, id=post_id)
            
            # Check if post allows likes
            if not post.allow_likes:
                return Response.error(
                    message="This post does not allow likes",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has already liked the post
            like_exists = PostLike.objects.filter(
                post=post,
                user=request.user
            ).exists()
            
            if like_exists:
                # If already liked, unlike
                PostLike.objects.filter(
                    post=post,
                    user=request.user
                ).delete()
                
                return Response.success(
                    data={
                        'post_id': post_id,
                        'liked': False,
                        'likes_count': post.likes.count()
                    },
                    message="Post unliked successfully",
                    status=status.HTTP_200_OK
                )
            else:
                # If not liked, like
                PostLike.objects.create(
                    post=post,
                    user=request.user,
                    like_type='like'
                )
                
                return Response.success(
                    data={
                        'post_id': post_id,
                        'liked': True,
                        'likes_count': post.likes.count()
                    },
                    message="Post liked successfully",
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            return Response.error(
                message=f"Error processing request: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class CommentPostView(APIView):
    """
    View for adding a comment to a post
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, post_id):
        try:
            # Get the post
            post = get_object_or_404(Post, id=post_id)
            
            # Check if post allows comments
            if not post.allow_comments:
                return Response.error(
                    message="This post does not allow comments",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the comment text
            text = request.data.get('text')
            
            if not text or text.strip() == '':
                return Response.error(
                    message="Comment text is required",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the comment
            comment = PostComment.objects.create(
                post=post,
                user=request.user,
                text=text
            )
            
            return Response.success(
                data={
                    'comment_id': comment.id,
                    'post_id': post_id,
                    'text': comment.text,
                    'user': {
                        'id': request.user.id,
                        'username': request.user.username,
                        'profile_picture': request.user.img.url if request.user.img else None
                    },
                    'created_at': comment.created_at
                },
                message="Comment added successfully",
                status=status.HTTP_201_CREATED
            )
                
        except Exception as e:
            return Response.error(
                message=f"Error processing request: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class GetPostCommentsView(APIView):
    """
    View for getting comments on a post
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, post_id):
        try:
            # Get the post
            post = get_object_or_404(Post, id=post_id)
            
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = 10  # Fixed page size of 10 comments per request
            
            # Get all comments for the post
            comments = PostComment.objects.filter(post=post).order_by('-created_at')
            
            # Calculate total comments and pages
            total_comments = comments.count()
            total_pages = (total_comments + page_size - 1) // page_size  # Ceiling division
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            # Get the paginated subset of comments
            paginated_comments = comments[start_idx:end_idx]
            
            # Prepare response data
            comments_data = []
            for comment in paginated_comments:
                comments_data.append({
                    'id': comment.id,
                    'text': comment.text,
                    'user': {
                        'id': comment.user.id,
                        'username': comment.user.username,
                        'profile_picture': comment.user.img.url if comment.user.img else None
                    },
                    'created_at': comment.created_at,
                    'is_own_comment': comment.user.id == request.user.id
                })
            
            # Add pagination information to the response
            pagination_info = {
                'current_page': page,
                'total_pages': total_pages,
                'page_size': page_size,
                'total_comments': total_comments,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
            
            return Response.success(
                data={
                    'post_id': post_id,
                    'comments': comments_data,
                    'pagination': pagination_info
                },
                message="Comments retrieved successfully",
                status=status.HTTP_200_OK
            )
                
        except Exception as e:
            return Response.error(
                message=f"Error retrieving comments: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class DeleteCommentView(APIView):
    """
    View for deleting a comment
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def delete(self, request, comment_id):
        try:
            # Get the comment
            comment = get_object_or_404(PostComment, id=comment_id)
            
            # Check if user is the owner of the comment or the post
            if comment.user != request.user and comment.post.user != request.user:
                return Response.error(
                    message="You don't have permission to delete this comment",
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the comment
            comment.delete()
            
            return Response.success(
                message="Comment deleted successfully",
                status=status.HTTP_200_OK
            )
                
        except Exception as e:
            return Response.error(
                message=f"Error deleting comment: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class SavePostView(APIView):
    """
    View for saving/unsaving a post
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, post_id):
        try:
            # Get the post
            post = get_object_or_404(Post, id=post_id)
            
            # Check if user has already saved the post
            save_exists = SavedPost.objects.filter(
                post=post,
                user=request.user
            ).exists()
            
            if save_exists:
                # If already saved, unsave
                SavedPost.objects.filter(
                    post=post,
                    user=request.user
                ).delete()
                
                return Response.success(
                    data={
                        'post_id': post_id,
                        'saved': False
                    },
                    message="Post unsaved successfully",
                    status=status.HTTP_200_OK
                )
            else:
                # If not saved, save
                SavedPost.objects.create(
                    post=post,
                    user=request.user
                )
                
                return Response.success(
                    data={
                        'post_id': post_id,
                        'saved': True
                    },
                    message="Post saved successfully",
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            return Response.error(
                message=f"Error processing request: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class GetSavedPostsView(APIView):
    """
    View for getting saved posts
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get pagination parameters
            page = int(request.query_params.get('page', 1))
            page_size = 10  # Fixed page size of 10 posts per request
            
            # Get all saved posts for the user
            saved_posts = SavedPost.objects.filter(user=request.user).order_by('-created_at')
            
            # Calculate total saved posts and pages
            total_saved_posts = saved_posts.count()
            total_pages = (total_saved_posts + page_size - 1) // page_size  # Ceiling division
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            # Get the paginated subset of saved posts
            paginated_saved_posts = saved_posts[start_idx:end_idx]
            
            # Prepare response data
            posts_data = []
            for saved_post in paginated_saved_posts:
                post = saved_post.post
                
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
                    'has_liked': post.likes.filter(user=request.user).exists(),
                    'has_saved': True,  # Always true since these are saved posts
                    'main_media': {
                        'id': main_media.id if main_media else None,
                        'media_type': main_media.media_type if main_media else None,
                        'file_url': main_media.file_url if main_media else None,
                        'filename': main_media.filename if main_media else None
                    } if main_media else None,
                    'additional_media': additional_media_items,
                    'saved_at': saved_post.created_at
                })
            
            # Add pagination information to the response
            pagination_info = {
                'current_page': page,
                'total_pages': total_pages,
                'page_size': page_size,
                'total_saved_posts': total_saved_posts,
                'has_next': page < total_pages,
                'has_previous': page > 1
            }
            
            return Response.success(
                data={
                    'saved_posts': posts_data,
                    'pagination': pagination_info
                },
                message="Saved posts retrieved successfully",
                status=status.HTTP_200_OK
            )
                
        except Exception as e:
            return Response.error(
                message=f"Error retrieving saved posts: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

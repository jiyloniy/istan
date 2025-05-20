from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from .response import CustomResponse as Response
from .models import User
from .profile_models import Skill, Achievement, PortfolioItem, PortfolioImage, UserTag
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Avg, Count

class UserProfileView(APIView):
    """
    View for getting a user's profile information
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        try:
            # If user_id is not provided, get the current user's profile
            if user_id is None:
                user = request.user
            else:
                user = get_object_or_404(User, id=user_id)
            
            # Get user's skills grouped by category
            skills = {}
            for skill in user.skills.all():
                category = skill.get_category_display()
                if category not in skills:
                    skills[category] = []
                
                skills[category].append({
                    'id': skill.id,
                    'name': skill.name,
                    'rating': skill.rating,
                    'icon': skill.icon,
                    'date_added': skill.date_added
                })
            
            # Get user's achievements
            achievements = []
            for achievement in user.achievements.all():
                achievements.append({
                    'id': achievement.id,
                    'title': achievement.title,
                    'description': achievement.description,
                    'image': achievement.image.url if achievement.image else None,
                    'date': achievement.date,
                    'location': achievement.location
                })
            
            # Get user's portfolio items with images
            portfolio_items = []
            for item in user.portfolio_items.all():
                images = []
                for img in item.images.all():
                    images.append({
                        'id': img.id,
                        'url': img.image.url,
                        'is_primary': img.is_primary
                    })
                
                portfolio_items.append({
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'category': item.category,
                    'date_completed': item.date_completed,
                    'images': images
                })
            
            # Get user's tags
            tags = [tag.name for tag in user.tags.all()]
            
            # Calculate user rating (average of all skill ratings)
            all_skills = user.skills.all()
            user_rating = 0
            if all_skills.exists():
                total_rating = sum(skill.rating for skill in all_skills)
                user_rating = round(total_rating / all_skills.count(), 1)
            
            # Prepare response data
            profile_data = {
                'user_id': user.id,
                'username': user.username,
                'name': user.name,
                'second_name': user.second_name,
                'phone': user.phone,
                'bio': user.bio,
                'profile_picture': user.img.url if user.img else None,
                'rating': user_rating,
                'post_count': user.posts.count(),
                'follower_count': user.followers.count(),
                'following_count': user.following.count(),
                'skills': skills,
                'achievements': achievements,
                'portfolio_items': portfolio_items,
                'tags': tags,
                'is_own_profile': user.id == request.user.id
            }
            
            return Response.success(
                data=profile_data,
                message='Profile retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving profile: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class SkillView(APIView):
    """
    View for managing user skills
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    @transaction.atomic
    def post(self, request):
        try:
            # Extract data from request
            name = request.data.get('name')
            category = request.data.get('category')
            rating = request.data.get('rating')
            icon = request.data.get('icon', None)
            
            # Validate required fields
            if not name or not category or rating is None:
                return Response.error(
                    message="Name, category, and rating are required",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate rating (0-10)
            try:
                rating = int(rating)
                if rating < 0 or rating > 10:
                    return Response.error(
                        message="Rating must be between 0 and 10",
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                return Response.error(
                    message="Rating must be a number",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the skill
            skill = Skill.objects.create(
                user=request.user,
                name=name,
                category=category,
                rating=rating,
                icon=icon
            )
            
            return Response.success(
                data={
                    'id': skill.id,
                    'name': skill.name,
                    'category': skill.get_category_display(),
                    'rating': skill.rating,
                    'icon': skill.icon,
                    'date_added': skill.date_added
                },
                message='Skill added successfully',
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error adding skill: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @transaction.atomic
    def delete(self, request, skill_id):
        try:
            # Get the skill
            skill = get_object_or_404(Skill, id=skill_id)
            
            # Check if user is the owner of the skill
            if skill.user != request.user:
                return Response.error(
                    message="You don't have permission to delete this skill",
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the skill
            skill.delete()
            
            return Response.success(
                message="Skill deleted successfully",
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error deleting skill: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class AchievementView(APIView):
    """
    View for managing user achievements
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @transaction.atomic
    def post(self, request):
        try:
            # Extract data from request
            title = request.data.get('title')
            description = request.data.get('description', '')
            date_str = request.data.get('date')
            location = request.data.get('location', '')
            image = request.FILES.get('image')
            
            # Validate required fields
            if not title or not date_str:
                return Response.error(
                    message="Title and date are required",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse date
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response.error(
                    message="Invalid date format. Use YYYY-MM-DD",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the achievement
            achievement = Achievement.objects.create(
                user=request.user,
                title=title,
                description=description,
                date=date,
                location=location,
                image=image
            )
            
            return Response.success(
                data={
                    'id': achievement.id,
                    'title': achievement.title,
                    'description': achievement.description,
                    'image': achievement.image.url if achievement.image else None,
                    'date': achievement.date,
                    'location': achievement.location
                },
                message='Achievement added successfully',
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error adding achievement: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @transaction.atomic
    def delete(self, request, achievement_id):
        try:
            # Get the achievement
            achievement = get_object_or_404(Achievement, id=achievement_id)
            
            # Check if user is the owner of the achievement
            if achievement.user != request.user:
                return Response.error(
                    message="You don't have permission to delete this achievement",
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the achievement
            achievement.delete()
            
            return Response.success(
                message="Achievement deleted successfully",
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error deleting achievement: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class PortfolioItemView(APIView):
    """
    View for managing portfolio items
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @transaction.atomic
    def post(self, request):
        try:
            # Extract data from request
            title = request.data.get('title')
            description = request.data.get('description', '')
            category = request.data.get('category', '')
            date_str = request.data.get('date_completed')
            images = request.FILES.getlist('images')
            
            # Validate required fields
            if not title or not date_str:
                return Response.error(
                    message="Title and date_completed are required",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not images:
                return Response.error(
                    message="At least one image is required",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse date
            try:
                date_completed = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response.error(
                    message="Invalid date format. Use YYYY-MM-DD",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the portfolio item
            portfolio_item = PortfolioItem.objects.create(
                user=request.user,
                title=title,
                description=description,
                category=category,
                date_completed=date_completed
            )
            
            # Add images
            portfolio_images = []
            for i, image in enumerate(images):
                is_primary = (i == 0)  # First image is primary
                portfolio_image = PortfolioImage.objects.create(
                    portfolio_item=portfolio_item,
                    image=image,
                    is_primary=is_primary
                )
                portfolio_images.append({
                    'id': portfolio_image.id,
                    'url': portfolio_image.image.url,
                    'is_primary': portfolio_image.is_primary
                })
            
            return Response.success(
                data={
                    'id': portfolio_item.id,
                    'title': portfolio_item.title,
                    'description': portfolio_item.description,
                    'category': portfolio_item.category,
                    'date_completed': portfolio_item.date_completed,
                    'images': portfolio_images
                },
                message='Portfolio item added successfully',
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error adding portfolio item: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @transaction.atomic
    def delete(self, request, portfolio_item_id):
        try:
            # Get the portfolio item
            portfolio_item = get_object_or_404(PortfolioItem, id=portfolio_item_id)
            
            # Check if user is the owner of the portfolio item
            if portfolio_item.user != request.user:
                return Response.error(
                    message="You don't have permission to delete this portfolio item",
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the portfolio item (will cascade delete images)
            portfolio_item.delete()
            
            return Response.success(
                message="Portfolio item deleted successfully",
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error deleting portfolio item: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

class UserTagView(APIView):
    """
    View for managing user tags
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]
    
    @transaction.atomic
    def post(self, request):
        try:
            # Extract data from request
            name = request.data.get('name')
            
            # Validate required fields
            if not name:
                return Response.error(
                    message="Tag name is required",
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create the tag (or get if it already exists)
            tag, created = UserTag.objects.get_or_create(
                user=request.user,
                name=name
            )
            
            return Response.success(
                data={
                    'id': tag.id,
                    'name': tag.name,
                    'created': created
                },
                message='Tag added successfully' if created else 'Tag already exists',
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error adding tag: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @transaction.atomic
    def delete(self, request, tag_id):
        try:
            # Get the tag
            tag = get_object_or_404(UserTag, id=tag_id)
            
            # Check if user is the owner of the tag
            if tag.user != request.user:
                return Response.error(
                    message="You don't have permission to delete this tag",
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the tag
            tag.delete()
            
            return Response.success(
                message="Tag deleted successfully",
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error deleting tag: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )


class CompactProfileView(APIView):
    """
    View for getting a compact profile view with basic user information
    as shown in the profile header/card
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request, user_id=None):
        try:
            # If user_id is not provided, get the current user's profile
            if user_id is None:
                user = request.user
            else:
                user = get_object_or_404(User, id=user_id)
            
            # Calculate user rating (average of all skill ratings)
            all_skills = user.skills.all()
            user_rating = 0
            
            # Get post count
            post_count = user.posts.count()
            
            # Get follower count
            follower_count = user.followers.count()
            
            # Get following count
            following_count = user.following.count()
            
            # Check if the current user is following this user
            is_following = False
            if request.user.is_authenticated and request.user != user:
                is_following = user.followers.filter(user=request.user).exists()
            
            # Prepare response data
            profile_data = {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name if user.name else user.username,
                    'full_name': f"{user.name} {user.second_name}" if user.name and user.second_name else user.username,
                    'phone': user.phone,
                    'email': user.email,
                    'profile_picture': user.img.url if user.img else None,
                    # 'background_image': user.background_img.url if user.background_img else None,
                    'bio': user.bio,
                    
                },
                'stats': {
                    'post_count': post_count,
                    'follower_count': follower_count,
                    'following_count': following_count,
                },
                'profession': [
                    {
                        'id': profession.id,
                        'name': profession.name,
                    }
                    for profession in user.profession.all()
                ],
                'is_own_profile': user.id == request.user.id,
                'is_following': is_following,
                'is_verified': user.is_staff,  # Using is_staff as a proxy for verification status
            }
            
            return Response.success(
                data=profile_data,
                message='Profile retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response.error(
                message=f"Error retrieving profile: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

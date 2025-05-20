from django.shortcuts import render
from django.db import transaction
from .response import CustomResponse as Response
from .models import User, SmSCode
from django.utils import timezone
# Create your views here.
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from eskiz_sms import EskizSMS
from user.models import Profession
import random
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
# Import the post models
from .post_models import Post, MediaItem, PostLike, PostComment
# Import the story models
from .story_models import Story, StoryView
email = "qodirxonyusufjanov5@gmail.com"
password = "ThoIH2cYssktvU3Zak8YIlzX9ZMY3BthQYtIAjkU"

class SmsGenerateView(APIView):
    """
        Sms code generation
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        try:
            phone = request.data.get('phone')
            if not phone:
                return Response.error("Phone number is required", status=status.HTTP_400_BAD_REQUEST)
            
            # Generate a 6-digit code
            # code = str(random.randint(1000, 9999))
            code = 1111
            message = f"Bu Eskiz dan test"
            print(code)
            print(phone)
            # try:
            #     # Initialize EskizSMS and send SMS
            #     eskiz = EskizSMS(email=email, password=password)
            #     response = eskiz.send_sms(phone, message)
            #     print(response)
            #     # Check if the response indicates success
            #     # if response.status != 'success':  # Access the 'status' attribute directly
            #     #     return Response.error("Failed to send SMS", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # except Exception as e:
            #     return Response.error(f"Error sending SMS: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create or update the SMS code entry
            sms_code, created = SmSCode.objects.update_or_create(
                phone=phone,
                defaults={'code': code, 'is_verified': False}
            )
            
            # Log the SMS sending (for debugging purposes)
            print(f"Sending SMS to {phone}: Your verification code is {code}")
            
            return Response.success(message="SMS sent successfully", status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response.error(f"Error: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class SmsVerifyView(APIView):
    """
        Sms code verification
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('code')

        if not phone or not code:
            return Response.error("Phone number and code are required", status=status.HTTP_400_BAD_REQUEST)

        try:
            sms_code = SmSCode.objects.get(phone=phone, code=code)
            if sms_code.is_verified:
                return Response.error("Code already verified", status=status.HTTP_400_BAD_REQUEST)
            
            # Mark the code as verified
            sms_code.is_verified = True
            sms_code.save()

            # Optionally, you can create or update the user here
            user, created = User.objects.update_or_create(
                phone=phone,
                defaults={'is_active': True}
            )
            password = str(random.randint(100000, 999999))  # Convert password to string
            user.set_password(password)
            user.save()  # Don't forget to save the user after setting the password

            if user.is_new:
                return Response.success(data={'is_new': True}, message="Code verified successfully", status=status.HTTP_200_OK)
            else:
                # Generate token for the user (JWT)
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                refresh_token = str(refresh)
                access_token = str(access)
                return Response.success(data={'is_new': False, 'refresh': refresh_token, 'access': access_token}, message="Code verified successfully", status=status.HTTP_200_OK)
        except SmSCode.DoesNotExist:
            return Response.error("Invalid code", status=status.HTTP_400_BAD_REQUEST)

class UserPartialCreate(APIView):
    """
        User partial create
    """
    permission_classes = [AllowAny]
    def checkusername(self, username):
        # jiyloniy@istan.uz
        # add @istan.uz
        username = username + "@istan.uz"
        if User.objects.filter(username=username).exists():
            return False
        return True
    @transaction.atomic
    def post(self, request):
        try:
            print(request.data)
            phone = request.data.get('phone')
            name = request.data.get('name')
            username = request.data.get('username')
            second_name = request.data.get('second_name')
            user_type = request.data.get('user_type')
            if not self.checkusername(username):
                return Response.error("Username already exists", status=status.HTTP_400_BAD_REQUEST)
            profession = request.data.get('profession')
            get_user = User.objects.filter(phone=phone).first()
            if not get_user:
                return Response.error("User not found", status=status.HTTP_404_NOT_FOUND)
            if not name or not username or not profession:
                return Response.error("Name, username and profession are required", status=status.HTTP_400_BAD_REQUEST)
            if not get_user.is_new:
                refresh = RefreshToken.for_user(get_user)
                access = refresh.access_token
                refresh_token = str(refresh)
                access_token = str(access)
                return Response.success(data={'is_new':False,'refresh':refresh_token,'access':access_token}, message="User already exists", status=status.HTTP_400_BAD_REQUEST)
            if get_user.is_new:
                get_user.user_type = user_type
                get_user.username = username + "@istan.uz"
                get_user.name = name
                get_user.profession.set(profession) 
                get_user.is_new = False
                get_user.second_name = second_name
                get_user.save()
                refresh = RefreshToken.for_user(get_user)
                access = refresh.access_token
                refresh_token = str(refresh)
                access_token = str(access)
                return Response.success(data={'is_new':True,'refresh':refresh_token,'access':access_token}, message="User created successfully", status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response.error(f"Error: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class GetProfession(APIView):
    """
        Get all profession
    """
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            professions = Profession.objects.all()
            data = []
            for profession in professions:
                data.append({
                    'id': profession.id,
                    'name': profession.name,
                })
            return Response.success(data=data, message="Professions retrieved successfully", status=status.HTTP_200_OK)
        except Exception as e:
            return Response.error(f"Error: {str(e)}", status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class UserView(APIView):
    authentication_classes = [JWTAuthentication]

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'name': user.name + ' ' + user.second_name,
            'profile_picture': user.img.url if user.img else None,
            'phone': user.phone,
            'username': user.username,
            'profession': [profession.name for profession in user.profession.all()],
            'user_type': user.user_type,
        }
        return Response.success(data=data, message="User retrieved successfully", status=status.HTTP_200_OK)
    

class PostContetn(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Focus on handling form data with files

    @transaction.atomic
    def post(self, request):
        try:
            # Log request info for debugging
            print(request)
            print(request.data)
            print(request.content_type)
            
            # Extract data from the request
            caption = request.data.get('caption', '')
            location_name = request.data.get('location_name', '')
            media_type = request.data.get('media_type', '')
            is_public = request.data.get('is_public', 'false').lower() == 'true'
            allow_comments = request.data.get('allow_comments', 'false').lower() == 'true'
            allow_likes = request.data.get('allow_likes', 'false').lower() == 'true'
            
            # Handle file uploads
            media_file = request.FILES.get('media')
            additional_media_files = request.FILES.getlist('additional_media')
            additional_media_types = request.data.getlist('additional_media_types')
            
            # Validate required fields
            if not media_file:
                return Response.error(message="Main media file is required", status=status.HTTP_400_BAD_REQUEST)
            
            # Create the post record
            post = Post.objects.create(
                user=request.user,
                caption=caption,
                location_name=location_name,
                is_public=is_public,
                allow_comments=allow_comments,
                allow_likes=allow_likes
            )
            
            # Save the main media file
            main_media = MediaItem.objects.create(
                post=post,
                file=media_file,
                media_type=media_type,
                is_main=True
            )
            
            # Save additional media files if any
            additional_media_items = []
            for i, file in enumerate(additional_media_files):
                media_type_value = additional_media_types[i] if i < len(additional_media_types) else 'unknown'
                media_item = MediaItem.objects.create(
                    post=post,
                    file=file,
                    media_type=media_type_value,
                    is_main=False
                )
                additional_media_items.append(media_item)
            
            # Prepare response data
            response_data = {
                'post_id': post.id,
                'caption': post.caption,
                'location_name': post.location_name,
                'is_public': post.is_public,
                'allow_comments': post.allow_comments,
                'allow_likes': post.allow_likes,
                'created_at': post.created_at,
                'main_media': {
                    'id': main_media.id,
                    'media_type': main_media.media_type,
                    'filename': main_media.filename,
                    'file_url': main_media.file_url
                },
                'additional_media_count': len(additional_media_items),
                'additional_media': []
            }
            
            
            
            # Return success response with post data
            return Response.success(
                message='Post created successfully', 
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return Response.error(message=f"Error processing request: {str(e)}", status=status.HTTP_400_BAD_REQUEST)


class StoryCreate(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @transaction.atomic
    def post(self, request):
        try:
            # Log request info for debugging
            print(request.data)
            print(request.FILES)
            
            # Extract data from the request
            content = request.data.get('content', '')
            media_type = request.data.get('media_type', 'image')
            duration = int(request.data.get('duration', 24))  # Default 24 hours
            is_public = request.data.get('is_public', 'false').lower() == 'true'
            
            # Handle media file upload
            media_file = request.FILES.get('media')
            
            # Validate required fields
            if not media_file:
                return Response.error(message="Media file is required", status=status.HTTP_400_BAD_REQUEST)
            
            # Validate media type
            if media_type not in ['image', 'video']:
                return Response.error(message="Invalid media type. Must be 'image' or 'video'", status=status.HTTP_400_BAD_REQUEST)
            
            # Create the story record
            story = Story.objects.create(
                user=request.user,
                content=content,
                media=media_file,
                media_type=media_type,
                duration=duration,
                is_public=is_public
            )
            
            # Prepare response data
            response_data = {
                'story_id': story.id,
                'expires_at': story.expires_at,
            }
            
            # Return success response with story data
            return Response.success(
                data=response_data,
                message='Story created successfully', 
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return Response.error(message=f"Error processing request: {str(e)}", status=status.HTTP_400_BAD_REQUEST)


class MyStoriesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get current time
            now = timezone.now()
            
            # Get all non-expired stories for the current user
            stories = Story.objects.filter(
                user=request.user,
                created_at__gte=now - timezone.timedelta(hours=24)  # Only stories from the last 24 hours
            ).order_by('-created_at')
            
            # Prepare response data
            stories_data = []
            for story in stories:
                stories_data.append({
                    'user': {
                        'id': story.user.id,
                        'username': story.user.username,
                        'name': story.user.name,
                        'profile_picture': story.user.img.url if story.user.img else None,
                    },
                    'id': story.id,
                    'content': story.content,
                    'media_url': story.file_url,
                    'media_type': story.media_type,
                    'created_at': story.created_at,
                    'expires_at': story.expires_at,
                    'is_expired': story.is_expired,
                    'view_count': story.views.count(),
                })
            
            return Response.success(
                data={'stories': stories_data},
                message='Stories retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"Error retrieving stories: {str(e)}")
            return Response.error(message=f"Error retrieving stories: {str(e)}", status=status.HTTP_400_BAD_REQUEST)


class FeedStoriesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get current time
            now = timezone.now()
            
            # Get all users that the current user follows using the UserFollowing model
            from .following_models import UserFollowing
            
            # Get the IDs of users that the current user follows
            following_user_ids = UserFollowing.objects.filter(
                user=request.user
            ).values_list('following_user_id', flat=True)
            
            # Get the current user's own active stories
            own_stories = Story.objects.filter(
                user=request.user,
                created_at__gte=now - timezone.timedelta(hours=24)  # Only stories from the last 24 hours
            ).order_by('-created_at')
            
            # Get all non-expired, public stories from users the current user follows
            followed_stories = Story.objects.filter(
                user_id__in=following_user_ids,
                is_public=True,
                created_at__gte=now - timezone.timedelta(hours=24)  # Only stories from the last 24 hours
            ).order_by('-created_at')
            
            # Combine own stories and followed stories
            stories = list(own_stories) + list(followed_stories)
            
            # Group stories by user
            user_stories = {}
            for story in stories:
                if story.user.id not in user_stories:
                    user_stories[story.user.id] = {
                        'user_id': story.user.id,
                        'username': story.user.username,
                        'name': story.user.name,
                        'profile_picture': story.user.img.url if story.user.img else None,
                        'stories': []
                    }
                
                # Check if the current user has viewed this story
                viewed = StoryView.objects.filter(story=story, viewer=request.user).exists()
                
                user_stories[story.user.id]['stories'].append({
                    'id': story.id,
                    'content': story.content,
                    'media_url': story.file_url,
                    'media_type': story.media_type,
                    'created_at': story.created_at,
                    'expires_at': story.expires_at,
                    'viewed': viewed,
                    'is_own': story.user.id == request.user.id
                })
            
            # Convert the dictionary to a list
            result = list(user_stories.values())
            
            return Response.success(
                data={'user_stories': result},
                message='Feed stories retrieved successfully',
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"Error retrieving feed stories: {str(e)}")
            return Response.error(message=f"Error retrieving feed stories: {str(e)}", status=status.HTTP_400_BAD_REQUEST)


class ViewStoryView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, story_id):
        try:
            # Find the story
            try:
                story = Story.objects.get(id=story_id)
            except Story.DoesNotExist:
                return Response.error(message="Story not found", status=status.HTTP_404_NOT_FOUND)
            
            # Check if story is expired
            if story.is_expired:
                return Response.error(message="Story has expired", status=status.HTTP_400_BAD_REQUEST)
            
            # Check if story is public or belongs to the user
            if not story.is_public and story.user != request.user:
                return Response.error(message="You don't have permission to view this story", status=status.HTTP_403_FORBIDDEN)
            
            # Record the view if it doesn't exist already
            view, created = StoryView.objects.get_or_create(
                story=story,
                viewer=request.user
            )
            
            return Response.success(
                message="Story marked as viewed" if created else "Story already viewed",
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            print(f"Error viewing story: {str(e)}")
            return Response.error(message=f"Error viewing story: {str(e)}", status=status.HTTP_400_BAD_REQUEST)
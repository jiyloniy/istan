from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .response import CustomResponse as Response
from .models import User
from .profile_views import CompactProfileView

class ProfileUpdateView(APIView):
    """
    View for updating user bio and profile image
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @transaction.atomic
    def patch(self, request, user_id=None):
        """
        Update user bio and profile image
        """
        try:
            # Only allow users to update their own profile
            if user_id is not None and int(user_id) != request.user.id:
                return Response.error(
                    message="You can only update your own profile",
                    status=status.HTTP_403_FORBIDDEN
                )
            
            user = request.user
            
            # Update bio if provided
            if 'bio' in request.data:
                user.bio = request.data.get('bio')
            
            # Handle profile picture update if provided
            if 'profile_picture' in request.FILES:
                user.img = request.FILES['profile_picture']
            
            # Save user changes
            user.save()
            
            # Return the updated profile using the CompactProfileView
            compact_view = CompactProfileView()
            return compact_view.get(request)
            
        except Exception as e:
            return Response.error(
                message=f"Error updating profile: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

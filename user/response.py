from rest_framework.response import Response

class CustomResponse:
    """
    Custom response class that extends the Django Rest Framework Response class.
    It can be used to standardize the response format across the application.
    """
    
    @staticmethod
    def success(data=None, message="Success", status=200):
        """
        Returns a success response.
        :param data: The data to be returned in the response.
        :param message: A message to be included in the response.
        :param status: The HTTP status code for the response.
        :return: A Response object with the specified data, message, and status code.
        """
        return Response({
            "status": "success",
            "message": message,
            "data": data
        }, status=status)
    
    @staticmethod
    def error(message="Error", status=400):
        """
        Returns an error response.
        :param message: A message to be included in the response.
        :param status: The HTTP status code for the response.
        :return: A Response object with the specified message and status code.
        """
        return Response({
            "status": "error",
            "message": message
        }, status=status)
    
    @staticmethod
    def not_found(message="Not Found", status=404):
        """
        Returns a not found response.
        :param message: A message to be included in the response.
        :param status: The HTTP status code for the response.
        :return: A Response object with the specified message and status code.
        """
        return Response({
            "status": "not_found",
            "message": message
        }, status=status)
    
    @staticmethod
    def forbidden(message="Forbidden", status=403):
        """
        Returns a forbidden response.
        :param message: A message to be included in the response.
        :param status: The HTTP status code for the response.
        :return: A Response object with the specified message and status code.
        """
        return Response({
            "status": "forbidden",
            "message": message
        }, status=status)

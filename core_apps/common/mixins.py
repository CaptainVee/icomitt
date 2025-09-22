from rest_framework.response import Response
from rest_framework import status

class StandardResponseMixin:
    """
    Mixin to provide standardized response methods for views.
    Use this for explicit control over success responses and custom error handling.
    """
    
    def success_response(self, data=None, message="", status_code=status.HTTP_200_OK):
        """Return standardized success response"""
        return Response({
            "success": True,
            "data": data or {},
            "message": message
        }, status=status_code)
    
    def error_response(self, error_message, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Return standardized error response.
        Note: Global exception handler will also format errors, but this gives you explicit control.
        """
        return Response({
            "success": False,
            "error": error_message
        }, status=status_code)
    
    def format_serializer_errors(self, errors):
        """Format serializer errors into a readable string"""
        if isinstance(errors, dict):
            error_messages = []
            for field, field_errors in errors.items():
                if field == 'non_field_errors':
                    if isinstance(field_errors, list):
                        error_messages.extend([str(err) for err in field_errors])
                    else:
                        error_messages.append(str(field_errors))
                else:
                    if isinstance(field_errors, list):
                        for error in field_errors:
                            error_messages.append(f"{field}: {error}")
                    else:
                        error_messages.append(f"{field}: {field_errors}")
            return "; ".join(error_messages)
        elif isinstance(errors, list):
            return "; ".join([str(err) for err in errors])
        return str(errors)
    
    def validate_serializer(self, serializer_class, data):
        """
        Helper method to validate serializer and return standardized responses.
        Returns (serializer, error_response) tuple.
        """
        serializer = serializer_class(data=data)
        if not serializer.is_valid():
            error_message = self.format_serializer_errors(serializer.errors)
            return None, self.error_response(error_message)
        return serializer, None

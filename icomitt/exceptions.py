from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """
    Custom exception handler to standardize all error responses globally.
    This catches errors from any view (including third-party packages).
    """
    response = exception_handler(exc, context)
    
    if response is not None:
        # Check if response is already in our standardized format
        if isinstance(response.data, dict) and 'success' in response.data:
            return response
            
        custom_response_data = {
            'success': False,
            'error': ''
        }
        
        # Handle different types of error responses
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                custom_response_data['error'] = str(response.data['detail'])
            elif 'non_field_errors' in response.data:
                if isinstance(response.data['non_field_errors'], list):
                    custom_response_data['error'] = '; '.join(response.data['non_field_errors'])
                else:
                    custom_response_data['error'] = str(response.data['non_field_errors'])
            else:
                # Handle field-specific validation errors
                error_messages = []
                for field, errors in response.data.items():
                    if isinstance(errors, list):
                        for error in errors:
                            if field == 'non_field_errors':
                                error_messages.append(str(error))
                            else:
                                error_messages.append(f"{field}: {error}")
                    else:
                        if field == 'non_field_errors':
                            error_messages.append(str(errors))
                        else:
                            error_messages.append(f"{field}: {errors}")
                custom_response_data['error'] = '; '.join(error_messages)
                
        elif isinstance(response.data, list):
            custom_response_data['error'] = '; '.join([str(item) for item in response.data])
        else:
            custom_response_data['error'] = str(response.data)
        
        # Ensure we don't have empty error messages
        if not custom_response_data['error']:
            custom_response_data['error'] = 'An error occurred'
            
        response.data = custom_response_data
    
    return response

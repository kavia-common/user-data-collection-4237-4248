import json
from pathlib import Path
from threading import Lock
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import UserDataSerializer

# Thread-safe file lock for concurrent access
file_lock = Lock()

# Path to the JSON storage file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / 'user_submissions.json'


def _read_submissions():
    """
    Read user submissions from the JSON file safely.
    
    Returns:
        list: List of user submission dictionaries
    """
    if not DATA_FILE.exists():
        return []
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        # If file is corrupted, return empty list
        return []
    except Exception as e:
        # Log error in production
        print(f"Error reading submissions: {str(e)}")
        return []


def _write_submissions(submissions):
    """
    Write user submissions to the JSON file safely.
    
    Args:
        submissions (list): List of user submission dictionaries
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first, then rename (atomic operation)
        temp_file = DATA_FILE.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(submissions, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_file.replace(DATA_FILE)
        return True
    except Exception as e:
        print(f"Error writing submissions: {str(e)}")
        return False


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method='post',
    operation_id='submit_user_data',
    operation_description='Submit user data to be stored in JSON file',
    operation_summary='Submit User Data',
    request_body=UserDataSerializer,
    responses={
        201: openapi.Response(
            description='User data successfully submitted',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        ),
        400: openapi.Response(description='Invalid input data'),
        500: openapi.Response(description='Internal server error')
    },
    tags=['user-data']
)
@swagger_auto_schema(
    method='get',
    operation_id='get_user_data',
    operation_description='Retrieve all submitted user data from JSON file',
    operation_summary='Get All User Data',
    responses={
        200: openapi.Response(
            description='List of all user submissions',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    )
                }
            )
        ),
        500: openapi.Response(description='Internal server error')
    },
    tags=['user-data']
)
@api_view(['POST', 'GET'])
def user_data(request):
    """
    Handle user data submission and retrieval.
    
    POST: Submit new user data (name, email, age) to be stored in JSON file
    GET: Retrieve all submitted user data from JSON file
    
    The data is stored in user_submissions.json with thread-safe file access.
    """
    if request.method == 'POST':
        # Validate incoming data
        serializer = UserDataSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'message': 'Validation failed',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Thread-safe file operations
        with file_lock:
            try:
                # Read existing submissions
                submissions = _read_submissions()
                
                # Add new submission with timestamp
                from datetime import datetime
                new_submission = {
                    **serializer.validated_data,
                    'submitted_at': datetime.utcnow().isoformat()
                }
                submissions.append(new_submission)
                
                # Write back to file
                if not _write_submissions(submissions):
                    return Response(
                        {'message': 'Failed to save submission'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                return Response(
                    {
                        'message': 'User data submitted successfully',
                        'data': new_submission
                    },
                    status=status.HTTP_201_CREATED
                )
            
            except Exception as e:
                return Response(
                    {'message': f'Internal server error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    
    elif request.method == 'GET':
        # Thread-safe file read
        with file_lock:
            try:
                submissions = _read_submissions()
                return Response(
                    {
                        'count': len(submissions),
                        'data': submissions
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'message': f'Internal server error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import QuestionTypeConfig
from reading.serializers.question_type_config import QuestionTypeConfigSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class QuestionTypeConfigView(APIView):
    """
    QuestionTypeConfigView: Handles CRUD operations for Question Type Configuration data.
    
    This view manages the dynamic question type system, allowing administrators to:
    - Create new question types without code changes
    - Configure requirements for each question type
    - Enable/disable question types
    - Manage question type metadata
    
    This view uses Shared Authentication Service for microservices communication:
    1. Receives requests with JWT tokens from the authentication project
    2. Uses SharedAuthPermission to verify tokens by calling the auth project
    3. Performs CRUD operations on Question Type Configuration data
    4. Returns appropriate responses with detailed logging
    
    Supported Operations:
    - POST: Create new Question Type Configuration entry
    - PUT: Update existing Question Type Configuration entry by ID
    - DELETE: Delete Question Type Configuration entry by ID
    - GET: Retrieve all Question Type Configuration entries
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    
    Key Features:
    - Dynamic question type management
    - Configuration-driven approach
    - Comprehensive logging for debugging
    - Error handling and validation
    """
    permission_classes = [SharedAuthPermission]  # Uses shared auth service
    authentication_classes = []  # No local authentication, relies on shared service

    def post(self, request):
        """
        Create a new Question Type Configuration entry.
        
        This method allows administrators to dynamically add new question types
        to the system without requiring code changes. It creates a new configuration
        that defines the behavior and requirements for a specific question type.
        
        This method:
        1. Logs the request details for debugging
        2. Validates the incoming data using QuestionTypeConfigSerializer
        3. Saves the data to the database
        4. Returns the created data or validation errors
        
        Args:
            request: HTTP request object with Question Type Configuration data and JWT token
                - type_code: Unique identifier for the question type (e.g., 'MC', 'TFNG')
                - display_name: Human-readable name (e.g., 'Multiple Choice')
                - description: Detailed description of the question type
                - requires_options: Whether this type needs multiple choice options
                - requires_word_limit: Whether this type needs word limit
                - requires_image: Whether this type needs images
                - is_active: Whether this type is available for use
            
        Returns:
            Response with created data (201) or validation errors (400)
        """
        logger.info("=== QUESTION TYPE CONFIG POST METHOD CALLED ===")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request headers: {request.headers}")
        
        # Log user info from shared auth service for debugging
        logger.info(f"User ID: {getattr(request, 'user_id', 'N/A')}")
        logger.info(f"Organization ID: {getattr(request, 'organization_id', 'N/A')}")
        logger.info(f"User Email: {getattr(request, 'user_email', 'N/A')}")
        
        try:
            # Validate and save the data using the serializer
            serializer = QuestionTypeConfigSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()  # Save to database
                logger.info(f"Question Type Config created successfully: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating Question Type Config: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Update a Question Type Configuration entry by ID.
        
        This method:
        1. Retrieves the Question Type Configuration object by primary key
        2. Updates the data with partial updates allowed
        3. Returns the updated data or appropriate error responses
        
        Args:
            request: HTTP request object with updated data and JWT token
            pk: Primary key (ID) of the Question Type Configuration object to update
            
        Returns:
            Response with updated data (200), not found (404), or validation errors (400)
        """
        logger.info(f"=== QUESTION TYPE CONFIG PUT METHOD CALLED for ID: {pk} ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Get the Question Type Configuration object from database
            config_obj = QuestionTypeConfig.objects.get(pk=pk)
            
            # Update the object with partial data (allows updating only some fields)
            serializer = QuestionTypeConfigSerializer(config_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Question Type Config updated successfully: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except QuestionTypeConfig.DoesNotExist:
            logger.error(f"Question Type Config with ID {pk} not found")
            return Response(
                {'error': 'Question Type Config not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating Question Type Config: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """
        Delete a Question Type Configuration entry by ID.
        
        This method:
        1. Retrieves the Question Type Configuration object by primary key
        2. Deletes the object from the database
        3. Returns success or appropriate error responses
        
        Args:
            request: HTTP request object with JWT token
            pk: Primary key (ID) of the Question Type Configuration object to delete
            
        Returns:
            Response with success (204), not found (404), or error (500)
        """
        logger.info(f"=== QUESTION TYPE CONFIG DELETE METHOD CALLED for ID: {pk} ===")
        
        try:
            # Get the Question Type Configuration object from database
            config_obj = QuestionTypeConfig.objects.get(pk=pk)
            
            # Delete the object
            config_obj.delete()
            logger.info(f"Question Type Config with ID {pk} deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
                
        except QuestionTypeConfig.DoesNotExist:
            logger.error(f"Question Type Config with ID {pk} not found")
            return Response(
                {'error': 'Question Type Config not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting Question Type Config: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get all Question Type Configuration entries.
        
        This method retrieves all question type configurations from the database,
        allowing frontend applications to dynamically build question type selection
        interfaces and understand the requirements for each question type.
        
        This method:
        1. Retrieves all Question Type Configuration objects
        2. Serializes them for API response
        3. Returns the complete list of available question types
        
        Args:
            request: HTTP request object with JWT token
            
        Returns:
            Response with all Question Type Configuration data (200) or error (500)
            The response includes:
            - id: Primary key
            - type_code: Unique identifier (e.g., 'MC', 'TFNG')
            - display_name: Human-readable name
            - description: Detailed description
            - is_active: Whether this type is available
            - requires_options: Whether options are needed
            - requires_word_limit: Whether word limit is needed
            - requires_image: Whether images are needed
            - created_at: When this config was created
        """
        logger.info("=== QUESTION TYPE CONFIG GET METHOD CALLED ===")
        
        try:
            # Get all Question Type Configuration objects from database
            config_objects = QuestionTypeConfig.objects.all()
            serializer = QuestionTypeConfigSerializer(config_objects, many=True)
            
            logger.info(f"Retrieved {len(serializer.data)} Question Type Config objects")
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error retrieving Question Type Config objects: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

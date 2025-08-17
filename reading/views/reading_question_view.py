from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import Question
from reading.serializers.reading_question import ReadingQuestionSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class ReadingQuestionView(APIView):
    """
    ReadingQuestionView: Handles CRUD operations for Reading Question data.
    
    This view uses Shared Authentication Service for microservices communication:
    1. Receives requests with JWT tokens from the authentication project
    2. Uses SharedAuthPermission to verify tokens by calling the auth project
    3. Performs CRUD operations on Reading Question data with proper permission checking
    4. Returns appropriate responses with detailed logging
    5. NEW: Automatically updates question ranges and maintains sequential ordering
    
    Supported Operations:
    - POST: Create new Reading Question entry (with auto range calculation)
    - PUT: Update existing Reading Question entry by ID (with range recalculation)
    - DELETE: Delete Reading Question entry by ID (with range recalculation)
    - GET: Retrieve all Reading Question entries for organization
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def post(self, request):
        """
        Create a new Reading Question entry with automatic range calculation.
        
        This method:
        1. Logs the request details for debugging
        2. Validates the incoming data using ReadingQuestionSerializer
        3. Saves the data to the database
        4. NEW: Automatically calculates and updates question ranges for all questions in the passage
        5. Returns the created data or validation errors
        
        Args:
            request: HTTP request object with Reading Question data and JWT token
            
        Returns:
            Response with created data (201) or validation errors (400)
        """
        logger.info("=== READING QUESTION POST METHOD CALLED ===")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request headers: {request.headers}")
        
        # Log user info from shared auth service
        logger.info(f"User ID: {getattr(request, 'user_id', 'N/A')}")
        logger.info(f"Organization ID: {getattr(request, 'organization_id', 'N/A')}")
        logger.info(f"User Email: {getattr(request, 'user_email', 'N/A')}")
        
        try:
            # Get organization_id from authenticated user and auto-assign it
            user_org_id = getattr(request, 'organization_id', None)
            if user_org_id:
                # Add organization_id to request data if not present
                if 'organization_id' not in request.data:
                    request.data['organization_id'] = user_org_id
                    logger.info(f"Auto-assigned organization_id: {user_org_id}")
                else:
                    # Verify that client-sent organization_id matches authenticated user
                    client_org_id = request.data.get('organization_id')
                    if str(client_org_id) != str(user_org_id):
                        logger.error(f"Organization ID mismatch: Client sent {client_org_id}, User has {user_org_id}")
                        return Response(
                            {'error': 'Organization ID does not match authenticated user'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                logger.error("No organization_id found in authenticated user")
                return Response(
                    {'error': 'User organization not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate and save the data
            serializer = ReadingQuestionSerializer(data=request.data)
            if serializer.is_valid():
                # Create the question (this will auto-calculate order_number and question_range)
                question = serializer.save()
                logger.info(f"Reading Question created successfully: {serializer.data}")
                
                # NEW: Update question ranges for all questions in the passage
                passage_id = question.passage.id
                self._update_all_question_ranges(passage_id)
                logger.info(f"Updated question ranges for passage {passage_id}")
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating Reading Question: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Update a Reading Question entry by ID with range recalculation.
        
        This method:
        1. Retrieves the Reading Question object by primary key
        2. Checks if the user has permission to edit this question (same organization)
        3. Updates the data with partial updates allowed
        4. NEW: Recalculates question ranges for all questions in the passage
        5. Returns the updated data or appropriate error responses
        
        Args:
            request: HTTP request object with updated data and JWT token
            pk: Primary key (ID) of the Reading Question object to update
            
        Returns:
            Response with updated data (200), not found (404), or permission denied (403)
        """
        logger.info(f"=== READING QUESTION PUT METHOD CALLED for ID: {pk} ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Get the Reading Question object from database
            question_obj = Question.objects.get(pk=pk)
            
            # Check if user has permission to edit this question (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if question_obj.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot edit question org {question_obj.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Auto-assign organization_id for updates if not provided
            user_org_id = getattr(request, 'organization_id', None)
            if user_org_id and 'organization_id' not in request.data:
                request.data['organization_id'] = user_org_id
                logger.info(f"Auto-assigned organization_id for update: {user_org_id}")
            
            # Update the object with partial data (allows updating only some fields)
            serializer = ReadingQuestionSerializer(question_obj, data=request.data, partial=True)
            if serializer.is_valid():
                # Update the question (this will auto-calculate question_range)
                question = serializer.save()
                logger.info(f"Reading Question updated successfully: {serializer.data}")
                
                # NEW: Update question ranges for all questions in the passage
                passage_id = question.passage.id
                self._update_all_question_ranges(passage_id)
                logger.info(f"Updated question ranges for passage {passage_id}")
                
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Question.DoesNotExist:
            logger.error(f"Reading Question with ID {pk} not found")
            return Response(
                {'error': 'Reading Question not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating Reading Question: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """
        Delete a Reading Question entry by ID with range recalculation.
        
        This method:
        1. Retrieves the Reading Question object by primary key
        2. Checks if the user has permission to delete this question (same organization)
        3. Deletes the object from the database
        4. NEW: Recalculates question ranges for all remaining questions in the passage
        5. Returns success or appropriate error responses
        
        Args:
            request: HTTP request object with JWT token
            pk: Primary key (ID) of the Reading Question object to delete
            
        Returns:
            Response with success (204), not found (404), or permission denied (403)
        """
        logger.info(f"=== READING QUESTION DELETE METHOD CALLED for ID: {pk} ===")
        
        try:
            # Get the Reading Question object from database
            question_obj = Question.objects.get(pk=pk)
            
            # Check if user has permission to delete this question (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if question_obj.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot delete question org {question_obj.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Store passage_id before deletion for range recalculation
            passage_id = question_obj.passage.id
            
            # Delete the object
            question_obj.delete()
            logger.info(f"Reading Question with ID {pk} deleted successfully")
            
            # NEW: Update question ranges for all remaining questions in the passage
            self._update_all_question_ranges(passage_id)
            logger.info(f"Updated question ranges for passage {passage_id} after deletion")
            
            return Response(status=status.HTTP_204_NO_CONTENT)
                
        except Question.DoesNotExist:
            logger.error(f"Reading Question with ID {pk} not found")
            return Response(
                {'error': 'Reading Question not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting Reading Question: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get all Reading Question entries for the user's organization.
        
        This method:
        1. Gets the organization_id from query parameters
        2. Validates that the user has permission to view this organization's data
        3. Retrieves all Reading Question objects for the organization
        4. Returns the serialized data with updated question ranges
        
        Args:
            request: HTTP request object with JWT token and organization_id query parameter
            
        Returns:
            Response with all Reading Question data (200), bad request (400), or permission denied (403)
        """
        logger.info("=== READING QUESTION GET METHOD CALLED ===")
        
        try:
            # Get organization_id from query parameters
            organization_id = request.query_params.get('organization_id')
            if not organization_id:
                logger.error("Organization ID not provided in query parameters")
                return Response(
                    {'error': 'Organization ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user has permission to view this organization's data
            user_org_id = getattr(request, 'organization_id', None)
            if str(user_org_id) != organization_id:
                logger.error(f"Permission denied: User org {user_org_id} cannot view org {organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get all Reading Question objects for the organization
            question_objects = Question.objects.filter(organization_id=organization_id)
            serializer = ReadingQuestionSerializer(question_objects, many=True)
            
            logger.info(f"Retrieved {len(serializer.data)} Reading Question objects for organization {organization_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error retrieving Reading Question objects: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _update_all_question_ranges(self, passage_id):
        """
        Update question ranges for all questions in a passage.
        
        This helper method ensures that all questions in a passage have
        correctly calculated question ranges after any CRUD operation.
        
        Args:
            passage_id (int): The ID of the passage to update ranges for
        """
        try:
            # Get all questions in the passage
            questions = Question.objects.filter(passage_id=passage_id)
            
            # Update ranges for each question
            for question in questions:
                question.update_question_range()
            
            logger.info(f"Updated question ranges for {questions.count()} questions in passage {passage_id}")
        except Exception as e:
            logger.error(f"Error updating question ranges for passage {passage_id}: {str(e)}")

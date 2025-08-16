from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import Passage, ReadingTest
from reading.serializers.passage import PassageSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class PassageView(APIView):
    """
    PassageView: Handles CRUD operations for Reading Passage data.
    
    This view uses Shared Authentication Service for microservices communication:
    1. Receives requests with JWT tokens from the authentication project
    2. Uses SharedAuthPermission to verify tokens by calling the auth project
    3. Performs CRUD operations on Reading Passage data with proper permission checking
    4. Returns appropriate responses with detailed logging
    
    Supported Operations:
    - POST: Create new Reading Passage entry
    - PUT: Update existing Reading Passage entry by ID
    - DELETE: Delete Reading Passage entry by ID
    - GET: Retrieve all Reading Passage entries for organization
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def post(self, request):
        """
        Create a new Reading Passage entry.
        
        This method:
        1. Logs the request details for debugging
        2. Validates the incoming data using PassageSerializer
        3. Saves the data to the database
        4. Returns the created data or validation errors
        
        Args:
            request: HTTP request object with Reading Passage data and JWT token
            
        Returns:
            Response with created data (201) or validation errors (400)
        """
        logger.info("=== READING PASSAGE POST METHOD CALLED ===")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request headers: {request.headers}")
        
        # Log user info from shared auth service
        logger.info(f"User ID: {getattr(request, 'user_id', 'N/A')}")
        logger.info(f"Organization ID: {getattr(request, 'organization_id', 'N/A')}")
        logger.info(f"User Email: {getattr(request, 'user_email', 'N/A')}")
        
        try:
            # Get organization_id from authenticated user
            user_org_id = getattr(request, 'organization_id', None)
            if not user_org_id:
                logger.error("No organization_id found in authenticated user")
                return Response(
                    {'error': 'User organization not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify that the test belongs to the user's organization
            test_id = request.data.get('test')
            if test_id:
                try:
                    test_obj = ReadingTest.objects.get(id=test_id)
                    if test_obj.organization_id != str(user_org_id):
                        logger.error(f"Permission denied: User org {user_org_id} cannot create passage for test org {test_obj.organization_id}")
                        return Response(
                            {'error': 'Permission denied - test does not belong to your organization'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except ReadingTest.DoesNotExist:
                    logger.error(f"Test with ID {test_id} not found")
                    return Response(
                        {'error': 'Specified test does not exist'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Validate and save the data
            serializer = PassageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Reading Passage created successfully: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating Reading Passage: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Update a Reading Passage entry by ID.
        
        This method:
        1. Retrieves the Reading Passage object by primary key
        2. Checks if the user has permission to edit this passage (same organization)
        3. Updates the data with partial updates allowed
        4. Returns the updated data or appropriate error responses
        
        Args:
            request: HTTP request object with updated data and JWT token
            pk: Primary key (ID) of the Reading Passage object to update
            
        Returns:
            Response with updated data (200), not found (404), or permission denied (403)
        """
        logger.info(f"=== READING PASSAGE PUT METHOD CALLED for ID: {pk} ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Get the Reading Passage object from database
            passage_obj = Passage.objects.get(pk=pk)
            
            # Check if user has permission to edit this passage (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if passage_obj.test.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot edit passage org {passage_obj.test.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
                                                # Verify that the test belongs to the user's organization (if test is being updated)
            test_id = request.data.get('test')
            if test_id:
                try:
                    test_obj = ReadingTest.objects.get(id=test_id)
                    if test_obj.organization_id != str(user_org_id):
                        logger.error(f"Permission denied: User org {user_org_id} cannot update passage to test org {test_obj.organization_id}")
                        return Response(
                            {'error': 'Permission denied - test does not belong to your organization'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except ReadingTest.DoesNotExist:
                    logger.error(f"Test with ID {test_id} not found")
                    return Response(
                        {'error': 'Specified test does not exist'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Update the object with partial data (allows updating only some fields)
            serializer = PassageSerializer(passage_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Reading Passage updated successfully: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Passage.DoesNotExist:
            logger.error(f"Reading Passage with ID {pk} not found")
            return Response(
                {'error': 'Reading Passage not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating Reading Passage: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """
        Delete a Reading Passage entry by ID.
        
        This method:
        1. Retrieves the Reading Passage object by primary key
        2. Checks if the user has permission to delete this passage (same organization)
        3. Deletes the object from the database
        4. Returns success or appropriate error responses
        
        Args:
            request: HTTP request object with JWT token
            pk: Primary key (ID) of the Reading Passage object to delete
            
        Returns:
            Response with success (204), not found (404), or permission denied (403)
        """
        logger.info(f"=== READING PASSAGE DELETE METHOD CALLED for ID: {pk} ===")
        
        try:
            # Get organization_id from authenticated user
            user_org_id = getattr(request, 'organization_id', None)
            if not user_org_id:
                logger.error("No organization_id found in authenticated user")
                return Response(
                    {'error': 'User organization not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the Reading Passage object from database
            passage_obj = Passage.objects.get(pk=pk)
            
            # Check if user has permission to delete this passage (same organization)
            if passage_obj.test.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot delete passage org {passage_obj.test.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the object
            passage_obj.delete()
            logger.info(f"Reading Passage with ID {pk} deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
                
        except Passage.DoesNotExist:
            logger.error(f"Reading Passage with ID {pk} not found")
            return Response(
                {'error': 'Reading Passage not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting Reading Passage: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get all Reading Passage entries for the user's organization.
        
        This method:
        1. Gets the organization_id from query parameters
        2. Validates that the user has permission to view this organization's data
        3. Retrieves all Reading Passage objects for the organization
        4. Returns the serialized data
        
        Args:
            request: HTTP request object with JWT token and organization_id query parameter
            
        Returns:
            Response with all Reading Passage data (200), bad request (400), or permission denied (403)
        """
        logger.info("=== READING PASSAGE GET METHOD CALLED ===")
        
        try:
            # Get organization_id from authenticated user
            user_org_id = getattr(request, 'organization_id', None)
            if not user_org_id:
                logger.error("No organization_id found in authenticated user")
                return Response(
                    {'error': 'User organization not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get organization_id from query parameters (for backward compatibility)
            organization_id = request.query_params.get('organization_id')
            if not organization_id:
                # Auto-assign organization_id from authenticated user
                organization_id = user_org_id
                logger.info(f"Auto-assigned organization_id for GET: {user_org_id}")
            else:
                # Verify that client-sent organization_id matches authenticated user
                if str(organization_id) != str(user_org_id):
                    logger.error(f"Organization ID mismatch: Client sent {organization_id}, User has {user_org_id}")
                    return Response(
                        {'error': 'Organization ID does not match authenticated user'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # Get all Reading Passage objects for the organization
            passage_objects = Passage.objects.filter(test__organization_id=organization_id)
            serializer = PassageSerializer(passage_objects, many=True)
            
            logger.info(f"Retrieved {len(serializer.data)} Reading Passage objects for organization {organization_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error retrieving Reading Passage objects: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

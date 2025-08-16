from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import ReadingTest
from reading.serializers.reading_test import ReadingTestSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class ReadingTestView(APIView):
    """
    ReadingTestView: Handles CRUD operations for Reading Test data.
    
    This view uses Shared Authentication Service for microservices communication:
    1. Receives requests with JWT tokens from the authentication project
    2. Uses SharedAuthPermission to verify tokens by calling the auth project
    3. Performs CRUD operations on Reading Test data with proper permission checking
    4. Returns appropriate responses with detailed logging
    
    Supported Operations:
    - POST: Create new Reading Test entry
    - PUT: Update existing Reading Test entry by ID
    - DELETE: Delete Reading Test entry by ID
    - GET: Retrieve all Reading Test entries for organization
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def post(self, request):
        """
        Create a new Reading Test entry.
        
        This method:
        1. Logs the request details for debugging
        2. Validates the incoming data using ReadingTestSerializer
        3. Saves the data to the database
        4. Returns the created data or validation errors
        
        Args:
            request: HTTP request object with Reading Test data and JWT token
            
        Returns:
            Response with created data (201) or validation errors (400)
        """
        logger.info("=== READING TEST POST METHOD CALLED ===")
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
            serializer = ReadingTestSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Reading Test created successfully: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating Reading Test: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Update a Reading Test entry by ID.
        
        This method:
        1. Retrieves the Reading Test object by primary key
        2. Checks if the user has permission to edit this test (same organization)
        3. Updates the data with partial updates allowed
        4. Returns the updated data or appropriate error responses
        
        Args:
            request: HTTP request object with updated data and JWT token
            pk: Primary key (ID) of the Reading Test object to update
            
        Returns:
            Response with updated data (200), not found (404), or permission denied (403)
        """
        logger.info(f"=== READING TEST PUT METHOD CALLED for ID: {pk} ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Get the Reading Test object from database
            test_obj = ReadingTest.objects.get(pk=pk)
            
            # Check if user has permission to edit this test (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if test_obj.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot edit test org {test_obj.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Auto-assign organization_id for updates if not provided
            if user_org_id and 'organization_id' not in request.data:
                request.data['organization_id'] = user_org_id
                logger.info(f"Auto-assigned organization_id for update: {user_org_id}")
            
            # Update the object with partial data (allows updating only some fields)
            serializer = ReadingTestSerializer(test_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Reading Test updated successfully: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer validation failed: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except ReadingTest.DoesNotExist:
            logger.error(f"Reading Test with ID {pk} not found")
            return Response(
                {'error': 'Reading Test not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating Reading Test: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """
        Delete a Reading Test entry by ID.
        
        This method:
        1. Retrieves the Reading Test object by primary key
        2. Checks if the user has permission to delete this test (same organization)
        3. Deletes the object from the database
        4. Returns success or appropriate error responses
        
        Args:
            request: HTTP request object with JWT token
            pk: Primary key (ID) of the Reading Test object to delete
            
        Returns:
            Response with success (204), not found (404), or permission denied (403)
        """
        logger.info(f"=== READING TEST DELETE METHOD CALLED for ID: {pk} ===")
        
        try:
            # Get organization_id from authenticated user and auto-assign it
            user_org_id = getattr(request, 'organization_id', None)
            if not user_org_id:
                logger.error("No organization_id found in authenticated user")
                return Response(
                    {'error': 'User organization not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the Reading Test object from database
            test_obj = ReadingTest.objects.get(pk=pk)
            
            # Check if user has permission to delete this test (same organization)
            if test_obj.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot delete test org {test_obj.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Delete the object
            test_obj.delete()
            logger.info(f"Reading Test with ID {pk} deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
                
        except ReadingTest.DoesNotExist:
            logger.error(f"Reading Test with ID {pk} not found")
            return Response(
                {'error': 'Reading Test not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting Reading Test: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get all Reading Test entries for the user's organization.
        
        This method:
        1. Gets the organization_id from query parameters
        2. Validates that the user has permission to view this organization's data
        3. Retrieves all Reading Test objects for the organization
        4. Returns the serialized data
        
        Args:
            request: HTTP request object with JWT token and organization_id query parameter
            
        Returns:
            Response with all Reading Test data (200), bad request (400), or permission denied (403)
        """
        logger.info("=== READING TEST GET METHOD CALLED ===")
        
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
            
            # Get all Reading Test objects for the organization
            test_objects = ReadingTest.objects.filter(organization_id=organization_id)
            serializer = ReadingTestSerializer(test_objects, many=True)
            
            logger.info(f"Retrieved {len(serializer.data)} Reading Test objects for organization {organization_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error retrieving Reading Test objects: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

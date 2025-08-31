from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from reading.models import ReadingTest
from reading.serializers import ReadingTestSerializer
from reading.permissions import SharedAuthPermission

# Set up logging for debugging and monitoring
logger = logging.getLogger(__name__)

class ReadingTestView(APIView):
    """
    API view for managing ReadingTest objects.
    
    This view provides CRUD operations for ReadingTest model instances.
    It includes organization-based data isolation and comprehensive error handling.
    
    Key Features:
    - POST: Create a new reading test
    - GET: Retrieve reading tests (all or by ID)
    - PUT: Update an existing reading test
    - DELETE: Delete a reading test
    - Organization-based data isolation
    - Comprehensive validation and error handling
    """
    
    # Require authentication for all operations
    permission_classes = [SharedAuthPermission]
    authentication_classes = []  # No local authentication, relies on shared service
    
    def post(self, request):
        """
        Create a new reading test.
        
        This method creates a new ReadingTest instance with the provided data.
        It automatically assigns the organization_id from the authenticated user.
        
        Args:
            request: The HTTP request object containing test data
            
        Returns:
            Response: JSON response with created test data or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Creating new reading test for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Prepare data for serializer
            data = request.data.copy()
            data['organization_id'] = organization_id
            
            logger.info(f"Data being sent to serializer: {data}")
            
            # Validate and create the test
            serializer = ReadingTestSerializer(data=data)
            if serializer.is_valid():
                # Use transaction to ensure data consistency
                with transaction.atomic():
                    reading_test = serializer.save()
                
                # Log successful creation
                logger.info(f"Successfully created reading test: {reading_test.test_id}")
                logger.info(f"Test organization_id: {reading_test.organization_id}")
                logger.info(f"Expected organization_id: {organization_id}")
                
                # Return the created test data
                return Response({
                    'message': 'Reading test created successfully',
                    'test': ReadingTestSerializer(reading_test).data
                }, status=status.HTTP_201_CREATED)
            else:
                # Log validation errors
                logger.warning(f"Validation error creating reading test: {serializer.errors}")
                return Response({
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error creating reading test: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, test_id=None):
        """
        Retrieve reading test(s).
        
        This method retrieves either a specific reading test by ID or all reading tests
        for the authenticated user's organization.
        
        Args:
            request: The HTTP request object
            test_id (str, optional): The UUID of the specific test to retrieve
            
        Returns:
            Response: JSON response with test data or error message
        """
        logger.info("=== READING TEST VIEW GET METHOD CALLED ===")
        logger.info(f"Request path: {request.path}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Authorization header: {request.headers.get('Authorization')}")
        
        try:
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            logger.info(f"Organization ID from request: {organization_id}")
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            if test_id:
                # Retrieve a specific test by ID
                logger.info(f"Retrieving reading test: {test_id} for organization: {organization_id}")
                
                # Get the test and verify organization ownership
                reading_test = get_object_or_404(ReadingTest, test_id=test_id)
                
                # Check if the test belongs to the user's organization
                if reading_test.organization_id != organization_id:
                    logger.warning(f"Unauthorized access attempt to test {test_id} by organization {organization_id}")
                    return Response({
                        'message': 'Access denied'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Return the specific test data
                return Response({
                    'message': 'Reading test retrieved successfully',
                    'test': ReadingTestSerializer(reading_test).data
                }, status=status.HTTP_200_OK)
            else:
                # Retrieve all tests for the organization
                logger.info(f"Retrieving all reading tests for organization: {organization_id}")
                
                # Get all tests for the organization
                reading_tests = ReadingTest.objects.filter(organization_id=organization_id)
                
                # Serialize the tests
                serializer = ReadingTestSerializer(reading_tests, many=True)
                
                # Return all tests data
                return Response({
                    'message': 'Reading tests retrieved successfully',
                    'tests': serializer.data,
                    'count': len(serializer.data)
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error retrieving reading test(s): {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, test_id):
        """
        Update an existing reading test.
        
        This method updates an existing ReadingTest instance with the provided data.
        It verifies organization ownership before allowing updates.
        
        Args:
            request: The HTTP request object containing updated test data
            test_id (str): The UUID of the test to update
            
        Returns:
            Response: JSON response with updated test data or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Updating reading test: {test_id} for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the test and verify organization ownership
            reading_test = get_object_or_404(ReadingTest, test_id=test_id)
            
            # Check if the test belongs to the user's organization
            if reading_test.organization_id != organization_id:
                logger.warning(f"Unauthorized update attempt to test {test_id} by organization {organization_id}")
                return Response({
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Prepare data for serializer (ensure organization_id is preserved)
            data = request.data.copy()
            data['organization_id'] = organization_id
            
            # Validate and update the test
            serializer = ReadingTestSerializer(reading_test, data=data, partial=True)
            if serializer.is_valid():
                # Use transaction to ensure data consistency
                with transaction.atomic():
                    updated_test = serializer.save()
                
                # Log successful update
                logger.info(f"Successfully updated reading test: {test_id}")
                
                # Return the updated test data
                return Response({
                    'message': 'Reading test updated successfully',
                    'test': ReadingTestSerializer(updated_test).data
                }, status=status.HTTP_200_OK)
            else:
                # Log validation errors
                logger.warning(f"Validation error updating reading test: {serializer.errors}")
                return Response({
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error updating reading test: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, test_id):
        """
        Delete a reading test.
        
        This method deletes an existing ReadingTest instance.
        It verifies organization ownership before allowing deletion.
        
        Args:
            request: The HTTP request object
            test_id (str): The UUID of the test to delete
            
        Returns:
            Response: JSON response with success or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Deleting reading test: {test_id} for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the test and verify organization ownership
            reading_test = get_object_or_404(ReadingTest, test_id=test_id)
            
            # Check if the test belongs to the user's organization
            if reading_test.organization_id != organization_id:
                logger.warning(f"Unauthorized delete attempt to test {test_id} by organization {organization_id}")
                return Response({
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Store test name for logging
            test_name = reading_test.test_name
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Delete the test (this will cascade to related passages and questions)
                reading_test.delete()
            
            # Log successful deletion
            logger.info(f"Successfully deleted reading test: {test_id} ({test_name})")
            
            # Return success message
            return Response({
                'message': 'Reading test deleted successfully',
                'deleted_test_id': test_id
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error deleting reading test: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
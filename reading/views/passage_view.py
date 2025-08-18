from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from reading.models import Passage, ReadingTest
from reading.serializers import PassageSerializer
from reading.permissions import SharedAuthPermission

# Set up logging for debugging and monitoring
logger = logging.getLogger(__name__)

class PassageView(APIView):
    """
    API view for managing Passage objects.
    
    This view provides CRUD operations for Passage model instances.
    It includes test-based data isolation and comprehensive error handling.
    
    Key Features:
    - POST: Create a new passage
    - GET: Retrieve passages (all or by ID)
    - PUT: Update an existing passage
    - DELETE: Delete a passage
    - Test-based data isolation
    - Comprehensive validation and error handling
    """
    
    # Require authentication for all operations
    permission_classes = [SharedAuthPermission]
    authentication_classes = []  # No local authentication, relies on shared service
    
    def post(self, request):
        """
        Create a new passage.
        
        This method creates a new Passage instance with the provided data.
        It verifies that the test belongs to the authenticated user's organization.
        
        Args:
            request: The HTTP request object containing passage data
            
        Returns:
            Response: JSON response with created passage data or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Creating new passage for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the test ID from request data
            test_id = request.data.get('test')
            if not test_id:
                return Response({
                    'message': 'Test ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Attempting to create passage for test_id: {test_id}")
            logger.info(f"Request organization_id: {organization_id}")
            
            # Verify that the test belongs to the user's organization
            try:
                test = ReadingTest.objects.get(test_id=test_id)
                logger.info(f"Found test: {test.test_id}")
                logger.info(f"Test organization_id: {test.organization_id}")
                logger.info(f"Request organization_id: {organization_id}")
                logger.info(f"Organization match: {test.organization_id == organization_id}")
                
                if test.organization_id != organization_id:
                    logger.warning(f"Unauthorized access attempt to test {test_id} by organization {organization_id}")
                    return Response({
                        'message': 'Access denied - test not found or not owned by your organization'
                    }, status=status.HTTP_403_FORBIDDEN)
            except ReadingTest.DoesNotExist:
                return Response({
                    'message': 'Test not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate and create the passage
            serializer = PassageSerializer(data=request.data)
            if serializer.is_valid():
                # Use transaction to ensure data consistency
                with transaction.atomic():
                    passage = serializer.save()
                
                # Log successful creation
                logger.info(f"Successfully created passage: {passage.passage_id}")
                
                # Return the created passage data
                return Response({
                    'message': 'Passage created successfully',
                    'passage': PassageSerializer(passage).data
                }, status=status.HTTP_201_CREATED)
            else:
                # Log validation errors
                logger.warning(f"Validation error creating passage: {serializer.errors}")
                return Response({
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error creating passage: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, passage_id=None):
        """
        Retrieve passage(s).
        
        This method retrieves either a specific passage by ID or all passages
        for a specific test that belongs to the authenticated user's organization.
        
        Args:
            request: The HTTP request object
            passage_id (str, optional): The UUID of the specific passage to retrieve
            
        Returns:
            Response: JSON response with passage data or error message
        """
        try:
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            if passage_id:
                # Retrieve a specific passage by ID
                logger.info(f"Retrieving passage: {passage_id} for organization: {organization_id}")
                
                # Get the passage and verify test ownership
                passage = get_object_or_404(Passage, passage_id=passage_id)
                
                # Check if the passage's test belongs to the user's organization
                if passage.test.organization_id != organization_id:
                    logger.warning(f"Unauthorized access attempt to passage {passage_id} by organization {organization_id}")
                    return Response({
                        'message': 'Access denied'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Return the specific passage data
                return Response({
                    'message': 'Passage retrieved successfully',
                    'passage': PassageSerializer(passage).data
                }, status=status.HTTP_200_OK)
            else:
                # Retrieve passages for a specific test
                test_id = request.query_params.get('test_id')
                if not test_id:
                    return Response({
                        'message': 'Test ID is required as query parameter'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                logger.info(f"Retrieving passages for test: {test_id} for organization: {organization_id}")
                
                # Verify that the test belongs to the user's organization
                try:
                    test = ReadingTest.objects.get(test_id=test_id)
                    if test.organization_id != organization_id:
                        logger.warning(f"Unauthorized access attempt to test {test_id} by organization {organization_id}")
                        return Response({
                            'message': 'Access denied - test not found or not owned by your organization'
                        }, status=status.HTTP_403_FORBIDDEN)
                except ReadingTest.DoesNotExist:
                    return Response({
                        'message': 'Test not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get all passages for the test
                passages = Passage.objects.filter(test=test)
                
                # Serialize the passages
                serializer = PassageSerializer(passages, many=True)
                
                # Return all passages data
                return Response({
                    'message': 'Passages retrieved successfully',
                    'passages': serializer.data,
                    'count': len(serializer.data)
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error retrieving passage(s): {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, passage_id):
        """
        Update an existing passage.
        
        This method updates an existing Passage instance with the provided data.
        It verifies test ownership before allowing updates.
        
        Args:
            request: The HTTP request object containing updated passage data
            passage_id (str): The UUID of the passage to update
            
        Returns:
            Response: JSON response with updated passage data or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Updating passage: {passage_id} for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the passage and verify test ownership
            passage = get_object_or_404(Passage, passage_id=passage_id)
            
            # Check if the passage's test belongs to the user's organization
            if passage.test.organization_id != organization_id:
                logger.warning(f"Unauthorized update attempt to passage {passage_id} by organization {organization_id}")
                return Response({
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate and update the passage
            serializer = PassageSerializer(passage, data=request.data, partial=True)
            if serializer.is_valid():
                # Use transaction to ensure data consistency
                with transaction.atomic():
                    updated_passage = serializer.save()
                
                # Log successful update
                logger.info(f"Successfully updated passage: {passage_id}")
                
                # Return the updated passage data
                return Response({
                    'message': 'Passage updated successfully',
                    'passage': PassageSerializer(updated_passage).data
                }, status=status.HTTP_200_OK)
            else:
                # Log validation errors
                logger.warning(f"Validation error updating passage: {serializer.errors}")
                return Response({
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error updating passage: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, passage_id):
        """
        Delete a passage.
        
        This method deletes an existing Passage instance.
        It verifies test ownership before allowing deletion.
        
        Args:
            request: The HTTP request object
            passage_id (str): The UUID of the passage to delete
            
        Returns:
            Response: JSON response with success or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Deleting passage: {passage_id} for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the passage and verify test ownership
            passage = get_object_or_404(Passage, passage_id=passage_id)
            
            # Check if the passage's test belongs to the user's organization
            if passage.test.organization_id != organization_id:
                logger.warning(f"Unauthorized delete attempt to passage {passage_id} by organization {organization_id}")
                return Response({
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Store passage title for logging
            passage_title = passage.title or f"Passage {passage.order}"
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Delete the passage (this will cascade to related question types and questions)
                passage.delete()
            
            # Log successful deletion
            logger.info(f"Successfully deleted passage: {passage_id} ({passage_title})")
            
            # Return success message
            return Response({
                'message': 'Passage deleted successfully',
                'deleted_passage_id': passage_id
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error deleting passage: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

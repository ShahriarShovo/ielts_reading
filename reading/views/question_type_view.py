from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging

from reading.models import QuestionType, Passage, ReadingTest
from reading.serializers import QuestionTypeSerializer
from reading.permissions import SharedAuthPermission

# Set up logging for debugging and monitoring
logger = logging.getLogger(__name__)

class QuestionTypeView(APIView):
    """
    API view for managing QuestionType objects.
    
    This view provides CRUD operations for QuestionType model instances.
    It includes passage-based data isolation and comprehensive error handling.
    
    Key Features:
    - POST: Create a new question type
    - GET: Retrieve question types (all or by ID)
    - PUT: Update an existing question type
    - DELETE: Delete a question type
    - Passage-based data isolation
    - Comprehensive validation and error handling
    - JSON question data management
    """
    
    # Require authentication for all operations
    permission_classes = [SharedAuthPermission]
    authentication_classes = []  # No local authentication, relies on shared service
    
    def post(self, request):
        """
        Create a new question type.
        
        This method creates a new QuestionType instance with the provided data.
        It verifies that the passage belongs to the authenticated user's organization.
        
        Args:
            request: The HTTP request object containing question type data
            
        Returns:
            Response: JSON response with created question type data or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Creating new question type for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the passage ID from request data
            passage_id = request.data.get('passage')
            if not passage_id:
                return Response({
                    'message': 'Passage ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify that the passage belongs to the user's organization
            try:
                passage = Passage.objects.get(passage_id=passage_id)
                if passage.test.organization_id != organization_id:
                    logger.warning(f"Unauthorized access attempt to passage {passage_id} by organization {organization_id}")
                    return Response({
                        'message': 'Access denied - passage not found or not owned by your organization'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Passage.DoesNotExist:
                return Response({
                    'message': 'Passage not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Debug: Log request data for diagram label completion
            if request.data.get('type') in ['Diagram Label Completion', 'diagram-label-completion']:
                logger.info(f"=== DIAGRAM LABEL COMPLETION CREATE DEBUG ===")
                logger.info(f"Request data type: {request.data.get('type')}")
                logger.info(f"Request data expected_range: {request.data.get('expected_range')}")
                logger.info(f"Request data actual_count: {request.data.get('actual_count')}")
                logger.info(f"Request data keys: {list(request.data.keys())}")
            
            # Validate and create the question type
            serializer = QuestionTypeSerializer(
                data=request.data,
                context={'passage': passage}
            )
            if serializer.is_valid():
                # Debug: Log validated data
                if request.data.get('type') in ['Diagram Label Completion', 'diagram-label-completion']:
                    logger.info(f"Validated data expected_range: {serializer.validated_data.get('expected_range')}")
                    logger.info(f"Validated data actual_count: {serializer.validated_data.get('actual_count')}")
                
                # Use transaction to ensure data consistency
                with transaction.atomic():
                    question_type = serializer.save()
                    
                    # Debug: Log saved question type
                    if question_type.type in ['Diagram Label Completion', 'diagram-label-completion']:
                        logger.info(f"Saved question_type.expected_range: {question_type.expected_range}")
                        logger.info(f"Saved question_type.actual_count: {question_type.actual_count}")
                
                # Log successful creation
                logger.info(f"Successfully created question type: {question_type.question_type_id}")
                
                # Return the created question type data
                return Response({
                    'message': 'Question type created successfully',
                    'question_type': QuestionTypeSerializer(question_type).data
                }, status=status.HTTP_201_CREATED)
            else:
                # Log validation errors
                logger.warning(f"Validation error creating question type: {serializer.errors}")
                return Response({
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error creating question type: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request, question_type_id=None):
        """
        Retrieve question type(s).
        
        This method retrieves either a specific question type by ID or all question types
        for a specific passage that belongs to the authenticated user's organization.
        
        Args:
            request: The HTTP request object
            question_type_id (str, optional): The UUID of the specific question type to retrieve
            
        Returns:
            Response: JSON response with question type data or error message
        """
        try:
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            if question_type_id:
                # Retrieve a specific question type by ID
                logger.info(f"Retrieving question type: {question_type_id} for organization: {organization_id}")
                
                # Get the question type and verify passage ownership
                question_type = get_object_or_404(QuestionType, question_type_id=question_type_id)
                
                # Check if the question type's passage belongs to the user's organization
                if question_type.passage.test.organization_id != organization_id:
                    logger.warning(f"Unauthorized access attempt to question type {question_type_id} by organization {organization_id}")
                    return Response({
                        'message': 'Access denied'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Return the specific question type data
                return Response({
                    'message': 'Question type retrieved successfully',
                    'question_type': QuestionTypeSerializer(question_type).data
                }, status=status.HTTP_200_OK)
            else:
                # Retrieve question types for a specific passage
                passage_id = request.query_params.get('passage_id')
                if not passage_id:
                    return Response({
                        'message': 'Passage ID is required as query parameter'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                logger.info(f"Retrieving question types for passage: {passage_id} for organization: {organization_id}")
                
                # Verify that the passage belongs to the user's organization
                try:
                    passage = Passage.objects.get(passage_id=passage_id)
                    if passage.test.organization_id != organization_id:
                        logger.warning(f"Unauthorized access attempt to passage {passage_id} by organization {organization_id}")
                        return Response({
                            'message': 'Access denied - passage not found or not owned by your organization'
                        }, status=status.HTTP_403_FORBIDDEN)
                except Passage.DoesNotExist:
                    return Response({
                        'message': 'Passage not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Get all question types for the passage
                question_types = QuestionType.objects.filter(passage=passage)
                
                # Serialize the question types
                serializer = QuestionTypeSerializer(question_types, many=True)
                
                # Return all question types data
                return Response({
                    'message': 'Question types retrieved successfully',
                    'question_types': serializer.data,
                    'count': len(serializer.data)
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error retrieving question type(s): {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, question_type_id):
        """
        Update an existing question type.
        
        This method updates an existing QuestionType instance with the provided data.
        It verifies passage ownership before allowing updates.
        
        Args:
            request: The HTTP request object containing updated question type data
            question_type_id (str): The UUID of the question type to update
            
        Returns:
            Response: JSON response with updated question type data or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Updating question type: {question_type_id} for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the question type and verify passage ownership
            question_type = get_object_or_404(QuestionType, question_type_id=question_type_id)
            
            # Check if the question type's passage belongs to the user's organization
            if question_type.passage.test.organization_id != organization_id:
                logger.warning(f"Unauthorized update attempt to question type {question_type_id} by organization {organization_id}")
                return Response({
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate and update the question type
            serializer = QuestionTypeSerializer(
                question_type, 
                data=request.data, 
                partial=True,
                context={'passage': question_type.passage}
            )
            if serializer.is_valid():
                # Use transaction to ensure data consistency
                with transaction.atomic():
                    updated_question_type = serializer.save()
                
                # Log successful update
                logger.info(f"Successfully updated question type: {question_type_id}")
                
                # Return the updated question type data
                return Response({
                    'message': 'Question type updated successfully',
                    'question_type': QuestionTypeSerializer(updated_question_type).data
                }, status=status.HTTP_200_OK)
            else:
                # Log validation errors
                logger.warning(f"Validation error updating question type: {serializer.errors}")
                return Response({
                    'message': 'Validation error',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error updating question type: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, question_type_id):
        """
        Delete a question type.
        
        This method deletes an existing QuestionType instance.
        It verifies passage ownership before allowing deletion.
        
        Args:
            request: The HTTP request object
            question_type_id (str): The UUID of the question type to delete
            
        Returns:
            Response: JSON response with success or error message
        """
        try:
            # Log the request for debugging
            logger.info(f"Deleting question type: {question_type_id} for organization: {request.organization_id}")
            
            # Get organization ID from the authenticated user
            organization_id = request.organization_id
            
            # Convert to string for consistent comparison
            organization_id = str(organization_id)
            
            # Get the question type and verify passage ownership
            question_type = get_object_or_404(QuestionType, question_type_id=question_type_id)
            
            # Check if the question type's passage belongs to the user's organization
            if question_type.passage.test.organization_id != organization_id:
                logger.warning(f"Unauthorized delete attempt to question type {question_type_id} by organization {organization_id}")
                return Response({
                    'message': 'Access denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Store question type info for logging
            question_type_info = f"{question_type.type} (Order: {question_type.order})"
            
            # Use transaction to ensure data consistency
            with transaction.atomic():
                # Delete the question type (this will cascade to related individual questions)
                question_type.delete()
            
            # Log successful deletion
            logger.info(f"Successfully deleted question type: {question_type_id} ({question_type_info})")
            
            # Return success message
            return Response({
                'message': 'Question type deleted successfully',
                'deleted_question_type_id': question_type_id
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Error deleting question type: {str(e)}")
            return Response({
                'message': 'Internal server error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

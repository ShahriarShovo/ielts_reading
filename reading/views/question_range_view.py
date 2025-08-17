from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import Question, QuestionTypeConfig
from reading.serializers.question_range import QuestionRangeSerializer, QuestionRangeInfoSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class QuestionRangeView(APIView):
    """
    QuestionRangeView: Handles question range calculations and updates.
    
    This view provides endpoints for:
    1. Calculating question ranges for all questions in a passage
    2. Updating question ranges when questions are added/deleted/reordered
    3. Getting range information for frontend display
    4. Providing progress indicators for question types
    
    Supported Operations:
    - GET: Calculate and retrieve question ranges for a passage
    - POST: Update question ranges for all questions in a passage
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def get(self, request):
        """
        Calculate and retrieve question ranges for a passage.
        
        This method:
        1. Gets passage_id from query parameters
        2. Validates user permissions for the passage
        3. Calculates question ranges for all question types in the passage
        4. Returns structured range information for frontend display
        
        Args:
            request: HTTP request object with passage_id query parameter and JWT token
            
        Returns:
            Response with range information (200) or error responses
        """
        logger.info("=== QUESTION RANGE GET METHOD CALLED ===")
        
        try:
            # Get passage_id from query parameters
            passage_id = request.query_params.get('passage_id')
            if not passage_id:
                logger.error("Passage ID not provided in query parameters")
                return Response(
                    {'error': 'Passage ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate the passage exists and user has permission
            from reading.models import Passage
            try:
                passage = Passage.objects.get(id=passage_id)
            except Passage.DoesNotExist:
                logger.error(f"Passage with ID {passage_id} not found")
                return Response(
                    {'error': 'Passage not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user has permission to view this passage (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if passage.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot view passage org {passage.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Calculate ranges using the serializer
            range_serializer = QuestionRangeSerializer(data={'passage_id': passage_id})
            if range_serializer.is_valid():
                ranges = range_serializer.calculate_ranges_for_passage(passage_id)
                
                # Format the response for frontend
                formatted_ranges = []
                for question_type, range_data in ranges.items():
                    # Get question type display name
                    try:
                        type_config = QuestionTypeConfig.objects.get(type_code=question_type)
                        display_name = type_config.display_name
                    except QuestionTypeConfig.DoesNotExist:
                        display_name = question_type
                    
                    # Create formatted range info
                    range_info = {
                        'question_type': question_type,
                        'display_name': display_name,
                        'range': range_data['range'],
                        'first_order': range_data['first_order'],
                        'last_order': range_data['last_order'],
                        'count': range_data['count'],
                        'progress_text': f"{range_data['count']} {display_name} questions added"
                    }
                    formatted_ranges.append(range_info)
                
                logger.info(f"Calculated ranges for passage {passage_id}: {formatted_ranges}")
                return Response({
                    'passage_id': passage_id,
                    'ranges': formatted_ranges,
                    'total_questions': sum(r['count'] for r in formatted_ranges)
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Range serializer validation failed: {range_serializer.errors}")
                return Response(range_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error calculating question ranges: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Update question ranges for all questions in a passage.
        
        This method:
        1. Gets passage_id from request data
        2. Validates user permissions for the passage
        3. Updates question ranges for all questions in the passage
        4. Returns summary of the update operation
        
        Args:
            request: HTTP request object with passage_id and JWT token
            
        Returns:
            Response with update summary (200) or error responses
        """
        logger.info("=== QUESTION RANGE POST METHOD CALLED ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Validate the request data
            range_serializer = QuestionRangeSerializer(data=request.data)
            if range_serializer.is_valid():
                passage_id = request.data.get('passage_id')
                
                # Update all question ranges
                result = range_serializer.update_all_ranges(passage_id)
                
                logger.info(f"Updated question ranges: {result}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Range serializer validation failed: {range_serializer.errors}")
                return Response(range_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error updating question ranges: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestionRangeByPassageView(APIView):
    """
    QuestionRangeByPassageView: Get question ranges for a specific passage.
    
    This view provides a dedicated endpoint for getting question ranges
    for a specific passage, including detailed information about each
    question type and its range.
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def get(self, request, passage_id):
        """
        Get question ranges for a specific passage.
        
        Args:
            request: HTTP request object with JWT token
            passage_id: ID of the passage to get ranges for
            
        Returns:
            Response with detailed range information (200) or error responses
        """
        logger.info(f"=== QUESTION RANGE BY PASSAGE GET METHOD CALLED for passage {passage_id} ===")
        
        try:
            # Validate the passage exists and user has permission
            from reading.models import Passage
            try:
                passage = Passage.objects.get(id=passage_id)
            except Passage.DoesNotExist:
                logger.error(f"Passage with ID {passage_id} not found")
                return Response(
                    {'error': 'Passage not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user has permission to view this passage (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if passage.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot view passage org {passage.organization_id}")
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get all questions in the passage, ordered by order_number
            questions = Question.objects.filter(passage_id=passage_id).order_by('order_number')
            
            # Group questions by type
            questions_by_type = {}
            for question in questions:
                if question.question_type not in questions_by_type:
                    questions_by_type[question.question_type] = []
                questions_by_type[question.question_type].append(question)
            
            # Calculate ranges for each question type
            ranges = []
            for question_type, type_questions in questions_by_type.items():
                if type_questions:
                    # Get order numbers for this question type
                    order_numbers = [q.order_number for q in type_questions]
                    first_order = min(order_numbers)
                    last_order = max(order_numbers)
                    
                    # Get question type display name
                    try:
                        type_config = QuestionTypeConfig.objects.get(type_code=question_type)
                        display_name = type_config.display_name
                    except QuestionTypeConfig.DoesNotExist:
                        display_name = question_type
                    
                    # Create range info
                    range_info = {
                        'question_type': question_type,
                        'display_name': display_name,
                        'range': f"Questions {first_order}-{last_order}",
                        'first_order': first_order,
                        'last_order': last_order,
                        'count': len(type_questions),
                        'progress_text': f"{len(type_questions)} {display_name} questions added",
                        'questions': [
                            {
                                'id': q.id,
                                'order_number': q.order_number,
                                'question_text': q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                                'instruction': q.instruction,
                                'answer_format': q.answer_format
                            }
                            for q in type_questions
                        ]
                    }
                    ranges.append(range_info)
            
            logger.info(f"Retrieved ranges for passage {passage_id}: {len(ranges)} question types")
            return Response({
                'passage_id': passage_id,
                'passage_title': passage.title,
                'ranges': ranges,
                'total_questions': sum(r['count'] for r in ranges)
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting question ranges for passage {passage_id}: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

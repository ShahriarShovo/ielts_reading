from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import Question
from reading.serializers.question_reorder import QuestionReorderSerializer, QuestionReorderInfoSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class QuestionReorderView(APIView):
    """
    QuestionReorderView: Handles question reordering operations.
    
    This view provides endpoints for:
    1. Reordering questions within a passage
    2. Updating order numbers to maintain sequential ordering (1,2,3,4,5...)
    3. Recalculating question ranges after reordering
    4. Getting current question order information for frontend display
    
    Supported Operations:
    - POST: Reorder questions in a passage
    - GET: Get current question order information for a passage
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def post(self, request):
        """
        Reorder questions in a passage.
        
        This method:
        1. Validates the reordering request data
        2. Checks user permissions for the passage
        3. Performs the reordering operation in a database transaction
        4. Updates all order numbers to maintain sequential ordering
        5. Recalculates question ranges for all questions
        6. Returns summary of the reordering operation
        
        Args:
            request: HTTP request object with reordering data and JWT token
            
        Returns:
            Response with reordering summary (200) or error responses
        """
        logger.info("=== QUESTION REORDER POST METHOD CALLED ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Validate the reordering request data
            reorder_serializer = QuestionReorderSerializer(data=request.data)
            if reorder_serializer.is_valid():
                passage_id = request.data.get('passage_id')
                question_orders = request.data.get('question_orders')
                
                # Validate user permissions for the passage
                from reading.models import Passage
                try:
                    passage = Passage.objects.get(id=passage_id)
                except Passage.DoesNotExist:
                    logger.error(f"Passage with ID {passage_id} not found")
                    return Response(
                        {'error': 'Passage not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Check if user has permission to reorder questions in this passage (same organization)
                user_org_id = getattr(request, 'organization_id', None)
                if passage.organization_id != str(user_org_id):
                    logger.error(f"Permission denied: User org {user_org_id} cannot reorder questions in passage org {passage.organization_id}")
                    return Response(
                        {'error': 'Permission denied'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Perform the reordering operation
                result = reorder_serializer.reorder_questions(passage_id, question_orders)
                
                logger.info(f"Question reordering completed: {result}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Reorder serializer validation failed: {reorder_serializer.errors}")
                return Response(reorder_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error reordering questions: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get current question order information for a passage.
        
        This method:
        1. Gets passage_id from query parameters
        2. Validates user permissions for the passage
        3. Retrieves all questions in the passage with their current order
        4. Returns structured order information for frontend display
        
        Args:
            request: HTTP request object with passage_id query parameter and JWT token
            
        Returns:
            Response with order information (200) or error responses
        """
        logger.info("=== QUESTION REORDER GET METHOD CALLED ===")
        
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
            
            # Get all questions in the passage, ordered by current order_number
            questions = Question.objects.filter(passage_id=passage_id).order_by('order_number')
            
            # Serialize the questions for response
            reorder_info_serializer = QuestionReorderInfoSerializer(questions, many=True)
            
            logger.info(f"Retrieved order information for {len(questions)} questions in passage {passage_id}")
            return Response({
                'passage_id': passage_id,
                'passage_title': passage.title,
                'questions': reorder_info_serializer.data,
                'total_questions': len(questions)
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting question order information: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestionReorderByPassageView(APIView):
    """
    QuestionReorderByPassageView: Get question order information for a specific passage.
    
    This view provides a dedicated endpoint for getting question order information
    for a specific passage, including detailed information about each question's
    current order and range.
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def get(self, request, passage_id):
        """
        Get question order information for a specific passage.
        
        Args:
            request: HTTP request object with JWT token
            passage_id: ID of the passage to get order information for
            
        Returns:
            Response with detailed order information (200) or error responses
        """
        logger.info(f"=== QUESTION REORDER BY PASSAGE GET METHOD CALLED for passage {passage_id} ===")
        
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
            
            # Group questions by type for better organization
            questions_by_type = {}
            for question in questions:
                if question.question_type not in questions_by_type:
                    questions_by_type[question.question_type] = []
                questions_by_type[question.question_type].append(question)
            
            # Create structured response
            question_groups = []
            for question_type, type_questions in questions_by_type.items():
                group_info = {
                    'question_type': question_type,
                    'question_type_display': type_questions[0].get_question_type_display(),
                    'questions': [
                        {
                            'id': q.id,
                            'order_number': q.order_number,
                            'question_text': q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                            'question_range': q.question_range,
                            'instruction': q.instruction,
                            'answer_format': q.answer_format,
                            'points': q.points,
                            'word_limit': q.word_limit
                        }
                        for q in type_questions
                    ],
                    'count': len(type_questions),
                    'range': type_questions[0].question_range if type_questions else ""
                }
                question_groups.append(group_info)
            
            logger.info(f"Retrieved order information for passage {passage_id}: {len(questions)} questions in {len(question_groups)} groups")
            return Response({
                'passage_id': passage_id,
                'passage_title': passage.title,
                'question_groups': question_groups,
                'total_questions': len(questions),
                'total_groups': len(question_groups)
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting question order information for passage {passage_id}: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

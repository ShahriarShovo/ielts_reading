from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from reading.models import ReadingTest, Passage
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class QuestionCountView(APIView):
    """
    QuestionCountView: Get the total question count for a test.
    
    This view provides an endpoint to get the total number of questions
    across all passages in a test.
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def get(self, request):
        """
        Get the total question count for a test.
        
        Args:
            request: HTTP request object with test_id query parameter and JWT token
            
        Returns:
            Response with question count (200) or error responses
        """
        logger.info("=== QUESTION COUNT GET METHOD CALLED ===")
        
        try:
            # Get test_id from query parameters
            test_id = request.query_params.get('test_id')
            if not test_id:
                logger.error("Test ID not provided in query parameters")
                return Response(
                    {'error': 'Test ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate the test exists and user has permission
            try:
                test = ReadingTest.objects.get(test_id=test_id)
            except ReadingTest.DoesNotExist:
                logger.error(f"Test with ID {test_id} not found")
                return Response(
                    {'error': 'Test not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user has permission to view this test (same organization)
            user_org_id = getattr(request, 'organization_id', None)
            if test.organization_id != str(user_org_id):
                logger.error(f"Permission denied: User org {user_org_id} cannot view test org {test.organization_id}")
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get all passages for this test
            passages = Passage.objects.filter(test=test).order_by('order')
            
            # Calculate total question count
            total_questions = 0
            for passage in passages:
                passage_count = passage.get_question_count()
                logger.info(f"Passage {passage.order} ({passage.title}): {passage_count} questions")
                total_questions += passage_count
            
            logger.info(f"Calculated question count for test {test_id}: {total_questions}")
            
            return Response({
                'test_id': test_id,
                'question_count': total_questions
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error calculating question count: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

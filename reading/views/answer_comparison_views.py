# ielts_reading/core/reading/views/answer_comparison_views.py
# API endpoints for answer comparison and scoring

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

from reading.permissions import SharedAuthPermission
from reading.utils.answer_comparison import compare_answers
from reading.views.test_answers import get_test_answers

logger = logging.getLogger('reading')

class CompareAnswersView(APIView):
    """
    API endpoint to compare student answers with correct answers.
    
    This endpoint:
    1. Receives student answers and test_id
    2. Gets correct answers for the test
    3. Compares answers using comparison logic
    4. Returns detailed results with band score
    
    Used by Academiq for answer comparison and scoring.
    """
    permission_classes = [SharedAuthPermission]
    
    def post(self, request):
        try:
            # Get request data
            student_answers = request.data.get('student_answers', {})
            test_id = request.data.get('test_id')
            
            if not test_id:
                return Response({
                    'error': 'test_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not student_answers:
                return Response({
                    'error': 'student_answers is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Comparing answers for test {test_id}")
            logger.info(f"Student answers: {len(student_answers)} questions")
            
            # Create a mock request object for get_test_answers function
            from django.http import HttpRequest
            mock_request = HttpRequest()
            mock_request.user_id = getattr(request, 'user_id', None)
            mock_request.organization_id = getattr(request, 'organization_id', None)
            
            # Get correct answers for this test
            correct_answers_response = get_test_answers(mock_request, test_id)
            
            if correct_answers_response.status_code != 200:
                return Response({
                    'error': 'Could not retrieve correct answers for this test'
                }, status=status.HTTP_404_NOT_FOUND)
            
            correct_answers_data = correct_answers_response.data
            correct_answers = correct_answers_data.get('answers', {})
            logger.info(f"Retrieved {len(correct_answers)} correct answers")
            
            # Compare answers
            comparison_results = compare_answers(student_answers, correct_answers)
            
            logger.info(f"Comparison complete: {comparison_results['correct_answers']}/{comparison_results['total_questions']} correct, Band: {comparison_results['band_score']}")
            
            return Response({
                'success': True,
                'results': comparison_results,
                'test_id': test_id,
                'message': f"Comparison complete: {comparison_results['correct_answers']}/{comparison_results['total_questions']} correct"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error comparing answers: {str(e)}")
            return Response({
                'error': f'Failed to compare answers: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BandScoreCalculationView(APIView):
    """
    API endpoint to calculate band score from correct answer count.
    
    Simple endpoint that takes correct_count and returns band score.
    """
    permission_classes = [SharedAuthPermission]
    
    def post(self, request):
        try:
            from reading.utils.answer_comparison import calculate_band_score
            
            correct_count = request.data.get('correct_count')
            
            if correct_count is None:
                return Response({
                    'error': 'correct_count is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                correct_count = int(correct_count)
            except (ValueError, TypeError):
                return Response({
                    'error': 'correct_count must be a valid integer'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if correct_count < 0 or correct_count > 40:
                return Response({
                    'error': 'correct_count must be between 0 and 40'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            band_score = calculate_band_score(correct_count)
            
            return Response({
                'success': True,
                'correct_count': correct_count,
                'band_score': band_score,
                'total_questions': 40
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error calculating band score: {str(e)}")
            return Response({
                'error': f'Failed to calculate band score: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ielts_reading/core/reading/views/test_answers.py
# This file provides API endpoints for getting correct answers from reading tests
# Used by Academiq to compare student answers with teacher's correct answers

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from reading.models import ReadingTest, Passage, QuestionType
from reading.permissions import SharedAuthPermission

logger = logging.getLogger('reading')

@api_view(['GET'])
@permission_classes([])  # Temporarily disable authentication for testing
def get_test_answers(request, test_id):
    """
    Get correct answers for a specific reading test.
    
    This endpoint is called by Academiq to get correct answers
    for comparison with student answers.
    
    Args:
        request: HTTP request object with JWT token
        test_id: UUID of the reading test
        
    Returns:
        Response with correct answers organized by question number
    """
    logger.info(f"=== GET TEST ANSWERS CALLED === Test ID: {test_id}")
    
    try:
        # Get the reading test
        test = ReadingTest.objects.get(test_id=test_id)
        logger.info(f"Found test: {test.test_name}")
        
        answers = {}
        question_counter = 1  # Global question counter (1-40)
        
        # Iterate through passages in order
        for passage in test.passages.all().order_by('order'):
            logger.info(f"Processing passage {passage.order}: {passage.title}")
            
            # Iterate through question types in order
            for question_type in passage.questions.all().order_by('order'):
                logger.info(f"Processing question type: {question_type.type}")
                
                # Iterate through questions in this question type
                for question in question_type.questions_data:
                    question_number = question.get('number', 1)
                    correct_answer = question.get('answer', '')
                    
                    # Store answer with global question number
                    answers[str(question_counter)] = {
                        'correct_answer': correct_answer,
                        'question_type': question_type.type,
                        'passage_id': str(passage.passage_id),
                        'question_type_id': str(question_type.question_type_id),
                        'local_question_number': question_number,
                        'global_question_number': question_counter
                    }
                    
                    question_counter += 1
                    
                    # Safety check: don't exceed 40 questions
                    if question_counter > 40:
                        logger.warning(f"Exceeded 40 questions limit. Stopping at question {question_counter-1}")
                        break
                
                # Safety check: don't exceed 40 questions
                if question_counter > 40:
                    break
            
            # Safety check: don't exceed 40 questions
            if question_counter > 40:
                break
        
        logger.info(f"Returning {len(answers)} correct answers for test {test_id}")
        
        return Response({
            'test_id': test_id,
            'test_name': test.test_name,
            'total_questions': len(answers),
            'answers': answers
        }, status=status.HTTP_200_OK)
        
    except ReadingTest.DoesNotExist:
        logger.error(f"Test not found: {test_id}")
        return Response({
            'error': 'Test not found',
            'test_id': test_id
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"Error getting test answers: {str(e)}")
        return Response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

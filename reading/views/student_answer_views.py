from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.utils import timezone
import logging
import uuid

from reading.models import StudentAnswer, QuestionType, SubmitAnswer
from reading.permissions import SharedAuthPermission

logger = logging.getLogger(__name__)

class SubmitStudentAnswersView(APIView):
    """
    SubmitStudentAnswersView: Handles student answer submission for reading exams.
    """
    
    permission_classes = [SharedAuthPermission]
    authentication_classes = []  # Disable default JWT authentication since we use custom permission
    
    def post(self, request):
        """
        Submit student answers for a reading exam session.
        """
        try:
            logger.info("=== SUBMIT STUDENT ANSWERS CALLED ===")
            logger.info(f"Request user_id: {getattr(request, 'user_id', 'NOT SET')}")
            logger.info(f"Request organization_id: {getattr(request, 'organization_id', 'NOT SET')}")
            logger.info(f"Request user_email: {getattr(request, 'user_email', 'NOT SET')}")
            
            # Log request data for debugging
            logger.info(f"Request data keys: {list(request.data.keys())}")
            logger.info(f"Request data: {request.data}")
            
            # Extract data from request
            session_id = request.data.get('session_id')
            answers_data = request.data.get('answers', [])
            
            logger.info(f"Extracted session_id: {session_id}")
            logger.info(f"Extracted answers_data type: {type(answers_data)}")
            logger.info(f"Extracted answers_data length: {len(answers_data) if isinstance(answers_data, list) else 'Not a list'}")
            
            # Validate required fields
            if not session_id:
                logger.error("Validation failed: session_id is missing")
                return Response({
                    'error': 'session_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(answers_data, list):
                logger.error(f"Validation failed: answers_data is not a list. Type: {type(answers_data)}")
                return Response({
                    'error': 'answers must be a list'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Allow empty submissions - students can submit without answering any questions
            if len(answers_data) == 0:
                logger.info("Student submitted with no answers - creating empty submission")
                
                # For empty submissions, get test_id from request or derive from session_id
                test_id_from_request = request.data.get('test_id')
                
                if test_id_from_request:
                    logger.info(f"Using test_id from request: {test_id_from_request}")
                    empty_submission_test_id = test_id_from_request
                else:
                    # Derive from session_id and generate proper UUID for compatibility
                    session_uuid_namespace = uuid.UUID('12345678-1234-5678-1234-123456789abc')
                    empty_submission_test_id = str(uuid.uuid5(session_uuid_namespace, f"session-{session_id}"))
                    logger.warning(f"No test_id provided, generated UUID from session_id: {empty_submission_test_id}")
                
                # Create empty submission record
                submit_answer = SubmitAnswer.objects.create(
                    session_id=session_id,
                    test_id=empty_submission_test_id,
                    student_id=request.data.get('student_id'),
                    organization_id=request.data.get('organization_id', 1),
                    total_questions=0
                )
                
                logger.info(f"Created empty submission for session {session_id} with test_id: {empty_submission_test_id}")
                
                return Response({
                    'message': 'Empty submission saved successfully.',
                    'result': {
                        'submit_id': str(submit_answer.submit_id),
                        'session_id': session_id,
                        'test_id': empty_submission_test_id,
                        'total_questions': 0,
                        'submitted_at': timezone.now().isoformat(),
                        'answers': [],
                        'message': 'Empty submission - no answers provided.'
                    }
                }, status=status.HTTP_200_OK)
            
            logger.info(f"Processing {len(answers_data)} answers for session {session_id}")
            
            # Process answers in a transaction
            with transaction.atomic():
                # Extract test_id from the request data, answers, or derive from session_id
                test_id = None
                
                # Try multiple sources for test_id
                if answers_data and len(answers_data) > 0:
                    # Try to get test_id from the first answer
                    test_id = answers_data[0].get('test_id')
                
                if not test_id:
                    # Fall back to request data
                    test_id = request.data.get('test_id')
                
                if not test_id:
                    # As a last resort, generate a UUID from session_id for compatibility
                    # This allows us to save student data even without proper test_id
                    # Create deterministic UUID based on session_id
                    session_uuid_namespace = uuid.UUID('12345678-1234-5678-1234-123456789abc')
                    test_id = str(uuid.uuid5(session_uuid_namespace, f"session-{session_id}"))
                    logger.warning(f"No test_id provided, generated UUID from session_id: {test_id}")
                else:
                    logger.info(f"Using provided test_id: {test_id}")
                
                # Delete any existing submissions for this session to avoid UNIQUE constraint conflicts
                existing_submission = SubmitAnswer.objects.filter(session_id=session_id).first()
                if existing_submission:
                    logger.info(f"Deleting existing submission for session {session_id}")
                    # Delete all related StudentAnswer records first
                    existing_submission.student_answers.all().delete()
                    existing_submission.delete()
                
                # Step 1: Create SubmitAnswer record
                submit_answer = SubmitAnswer.objects.create(
                    session_id=session_id,
                    test_id=test_id,  # Use extracted test_id
                    student_id=request.data.get('student_id'),
                    organization_id=request.data.get('organization_id', 1),
                    total_questions=len(answers_data)
                )
                
                processed_answers = []
                total_questions = len(answers_data)
                
                for answer_data in answers_data:
                    question_number = answer_data.get('question_number')
                    question_type_id = answer_data.get('question_type_id')
                    student_answer = answer_data.get('student_answer')
                    
                    logger.info(f"Processing answer - Q{question_number}: {student_answer} (type_id: {question_type_id})")
                    
                    # Validate answer data - only require question_number and student_answer
                    if not question_number or student_answer is None:
                        logger.error(f"Answer validation failed for question {question_number}: question_number={question_number}, student_answer={student_answer}")
                        return Response({
                            'error': f'Missing required fields for question {question_number}. Need question_number and student_answer.'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # For now, store student answers with minimal data
                    # We'll create a dummy QuestionType or find an existing one to satisfy the FK constraint
                    # This is temporary until comparison logic is implemented
                    
                    # Try to find any existing QuestionType to satisfy the FK constraint
                    # This is a temporary workaround
                    dummy_question_type = None
                    try:
                        # Skip trying to find actual question type for temp IDs (like 'temp-1')
                        if question_type_id and not question_type_id.startswith('temp-'):
                            dummy_question_type = QuestionType.objects.filter(question_type_id=question_type_id).first()
                        
                        # If not found or is a temp ID, get any QuestionType as placeholder
                        if not dummy_question_type:
                            dummy_question_type = QuestionType.objects.first()
                            logger.warning(f"Using placeholder QuestionType for question {question_number} with temp ID: {question_type_id}")
                    except Exception as e:
                        logger.error(f"Error finding QuestionType: {str(e)}")
                        # Get any QuestionType as fallback
                        dummy_question_type = QuestionType.objects.first()
                    
                    if not dummy_question_type:
                        return Response({
                            'error': 'No QuestionType found in database - please set up question types first'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    # Create StudentAnswer record with the answer data
                    # Store the actual question_type_id in the student_answer field for now
                    answer_data_with_type = {
                        'answer': student_answer,
                        'original_question_type_id': question_type_id,  # Store for later use
                        'submitted_by_frontend': True
                    }
                    
                    student_answer_obj, created = StudentAnswer.objects.get_or_create(
                        submit_answer=submit_answer,
                        question_number=question_number,
                        defaults={
                            'question_type': dummy_question_type,  # Temporary placeholder
                            'student_answer': answer_data_with_type,  # Store as JSON with metadata
                            'session_id': session_id,  # Keep for backward compatibility
                            'is_correct': False,  # Default to False until comparison is done
                            'scored_at': None    # Will be set later during comparison
                        }
                    )
                    
                    if not created:
                        # Update existing answer
                        student_answer_obj.student_answer = answer_data_with_type
                        student_answer_obj.session_id = session_id  # Update session_id
                        student_answer_obj.is_correct = False  # Reset to False for re-scoring
                        student_answer_obj.scored_at = None    # Reset for re-scoring
                        student_answer_obj.save()
                    
                    # Add to processed answers (simplified response)
                    processed_answers.append({
                        'question_number': question_number,
                        'student_answer': student_answer,
                        'question_type_id': question_type_id,  # Store for future use
                        'saved': True
                    })
                
                # Prepare response (without comparison results)
                result = {
                    'submit_id': str(submit_answer.submit_id),
                    'session_id': session_id,
                    'test_id': str(submit_answer.test_id),
                    'total_questions': total_questions,
                    'submitted_at': timezone.now().isoformat(),
                    'answers': processed_answers,
                    'message': 'Answers saved successfully. Results will be calculated by Academiq.'
                }
                
                logger.info(f"Successfully saved {total_questions} answers for session {session_id}")
                
                return Response({
                    'message': 'Student answers saved successfully. Results will be calculated by Academiq.',
                    'result': result
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error submitting student answers: {str(e)}")
            return Response({
                'error': f'An error occurred while submitting answers: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([SharedAuthPermission])
def get_student_answers_for_comparison(request, session_id):
    """
    Get student answers for comparison by Academiq.
    This endpoint is called by Academiq to get student answers and compare them.
    """
    try:
        logger.info(f"Getting student answers for comparison - session {session_id}")
        logger.info(f"Request user_id: {getattr(request, 'user_id', 'NOT SET')}")
        logger.info(f"Request organization_id: {getattr(request, 'organization_id', 'NOT SET')}")
        logger.info(f"Request user_email: {getattr(request, 'user_email', 'NOT SET')}")
        
        # Get the SubmitAnswer record for this session
        submit_answer = SubmitAnswer.objects.filter(session_id=session_id).first()
        
        if not submit_answer:
            return Response({
                'error': f'No submission found for session {session_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all student answers for this submission
        student_answers = submit_answer.get_student_answers()
        
        if not student_answers.exists():
            return Response({
                'error': f'No student answers found for session {session_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        answers_for_comparison = []
        
        for student_answer in student_answers:
            # Get the question from QuestionType
            question_type = student_answer.question_type
            
            # Find the specific question in questions_data
            question = None
            for q in question_type.questions_data:
                if q.get('question_number') == student_answer.question_number:
                    question = q
                    break
            
            if question:
                correct_answer = question.get('correct_answer')
                
                answers_for_comparison.append({
                    'question_number': student_answer.question_number,
                    'student_answer': student_answer.student_answer,
                    'correct_answer': correct_answer,
                    'question_type': question_type.type,
                    'question_type_id': str(question_type.question_type_id)
                })
        
        logger.info(f"Found {len(answers_for_comparison)} answers for comparison")
        
        return Response({
            'session_id': session_id,
            'total_answers': len(answers_for_comparison),
            'answers': answers_for_comparison
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting student answers for comparison: {str(e)}")
        return Response({
            'error': f'An error occurred while getting answers: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([SharedAuthPermission])
def update_student_answer_results(request, session_id):
    """
    Update student answer results after comparison by Academiq.
    This endpoint is called by Academiq to update comparison results.
    """
    try:
        logger.info(f"Updating student answer results for session {session_id}")
        
        results_data = request.data.get('results', [])
        
        if not results_data:
            return Response({
                'error': 'No results data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated_count = 0
        
        with transaction.atomic():
            for result in results_data:
                question_number = result.get('question_number')
                is_correct = result.get('is_correct')
                band_score = result.get('band_score')
                
                if question_number is not None and is_correct is not None:
                    # Update StudentAnswer
                    student_answer = StudentAnswer.objects.filter(
                        submit_answer__session_id=session_id,
                        question_number=question_number
                    ).first()
                    
                    if student_answer:
                        student_answer.is_correct = is_correct
                        student_answer.band_score = band_score
                        student_answer.scored_at = timezone.now()
                        student_answer.save()
                        updated_count += 1
        
        logger.info(f"Updated {updated_count} student answers for session {session_id}")
        
        return Response({
            'message': f'Successfully updated {updated_count} student answers',
            'session_id': session_id,
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating student answer results: {str(e)}")
        return Response({
            'error': f'An error occurred while updating results: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([SharedAuthPermission])
def get_exam_results(request, session_id):
    """
    Get exam results for a specific session.
    """
    try:
        logger.info(f"Getting exam results for session {session_id}")
        
        # Get session summary
        summary = StudentAnswer.get_session_summary(session_id)
        
        if summary['total_questions'] == 0:
            return Response({
                'error': f'No answers found for session {session_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get detailed answers
        answers = StudentAnswer.get_session_answers(session_id)
        detailed_answers = []
        
        for answer in answers:
            detailed_answers.append({
                'question_number': answer.question_number,
                'student_answer': answer.student_answer,
                'is_correct': answer.is_correct,
                'band_score': float(answer.band_score) if answer.band_score else None,
                'question_type': answer.question_type.type,
                'submitted_at': answer.submitted_at.isoformat()
            })
        
        result = {
            **summary,
            'detailed_answers': detailed_answers
        }
        
        return Response({
            'message': 'Exam results retrieved successfully',
            'result': result
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting exam results: {str(e)}")
        return Response({
            'error': f'An error occurred while getting results: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

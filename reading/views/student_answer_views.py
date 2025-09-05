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
                    total_questions=40  # IELTS Reading always has 40 questions
                )
                
                logger.info(f"Created empty submission for session {session_id} with test_id: {empty_submission_test_id}")
                
                return Response({
                    'message': 'Empty submission saved successfully.',
                    'result': {
                        'submit_id': str(submit_answer.submit_id),
                        'session_id': session_id,
                        'test_id': empty_submission_test_id,
                        'total_questions': 40,
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
                
                # PRIORITY 1: Try request data first (this is what frontend sends)
                test_id = request.data.get('test_id')
                
                if not test_id:
                # Try multiple sources for test_id
                # PRIORITY 2: Try to get test_id from the first answer
                    if answers_data and len(answers_data) > 0:
                        # Try to get test_id from the first answer
                        test_id = answers_data[0].get('test_id')
                
                # if not test_id:
                #     # Fall back to request data
                #     test_id = request.data.get('test_id')
                
                if not test_id:
                    # Try to get test_id from exam session data
                    # PRIORITY 3: Try to get test_id from exam session data
                    test_id = self._get_test_id_from_session(session_id)
                    if test_id:
                        logger.info(f"Found test_id from session data: {test_id}")
                
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
                    total_questions=40  # IELTS Reading always has 40 questions
                )
                
                processed_answers = []
                total_questions = 40  # IELTS Reading always has 40 questions
                
                # Validate that we have exactly 40 questions (IELTS Reading standard)
                if total_questions != 40:
                    logger.warning(f"Expected 40 questions but received {total_questions}. This might indicate missing questions.")
                
                # Create a map of answers for easy lookup
                answers_map = {}
                for answer_data in answers_data:
                    question_number = answer_data.get('question_number')
                    student_answer = answer_data.get('student_answer')
                    if question_number:
                        answers_map[question_number] = answer_data
                
                # Enhanced question processing with proper mapping
                logger.info("=== ENHANCED QUESTION PROCESSING ===")
                
                # Get the actual test data to map question numbers to question types
                from reading.models import ReadingTest
                actual_question_types = {}
                
                try:
                    # Try to get the actual test to map questions properly
                    reading_test = ReadingTest.objects.get(test_id=test_id)
                    logger.info(f"Found reading test: {reading_test.test_name}")
                    
                    # Build question number to question type mapping
                    question_counter = 1
                    for passage in reading_test.passages.all().order_by('order'):
                        for question_type in passage.questions.all().order_by('order'):
                            for question in question_type.questions_data:
                                if question_counter <= 40:
                                    actual_question_types[question_counter] = {
                                        'question_type_obj': question_type,
                                        'question_type_id': str(question_type.question_type_id),
                                        'question_type_name': question_type.type,
                                        'correct_answer': question.get('answer', ''),
                                        'passage_id': str(passage.passage_id)
                                    }
                                    question_counter += 1
                    
                    logger.info(f"Built mapping for {len(actual_question_types)} questions")
                    
                except ReadingTest.DoesNotExist:
                    logger.warning(f"Reading test {test_id} not found, using fallback mapping")
                except Exception as e:
                    logger.error(f"Error building question mapping: {str(e)}")
                
                # Process all 40 questions (1-40) with enhanced mapping
                for question_number in range(1, 41):
                    answer_data = answers_map.get(question_number, {})
                    student_answer = answer_data.get('student_answer', '')
                    frontend_question_type = answer_data.get('question_type', 'unknown')
                    
                    logger.info(f"Processing Q{question_number}: '{student_answer}' (Frontend type: {frontend_question_type})")
                    
                    # Get the actual question type from mapping
                    question_type_obj = None
                    question_type_id = None
                    
                    if question_number in actual_question_types:
                        # Use actual question type from test
                        question_type_obj = actual_question_types[question_number]['question_type_obj']
                        question_type_id = actual_question_types[question_number]['question_type_id']
                        logger.info(f"Q{question_number}: Using actual question type {actual_question_types[question_number]['question_type_name']}")
                    else:
                        # Fallback: try to find by frontend-provided ID
                        frontend_type_id = answer_data.get('question_type_id')
                        if frontend_type_id and not frontend_type_id.startswith('temp-'):
                            try:
                                question_type_obj = QuestionType.objects.get(question_type_id=frontend_type_id)
                                question_type_id = frontend_type_id
                                logger.info(f"Q{question_number}: Using frontend-provided question type")
                            except QuestionType.DoesNotExist:
                                logger.warning(f"Q{question_number}: Frontend question type {frontend_type_id} not found")
                        
                        # Final fallback: use any available question type
                        if not question_type_obj:
                            question_type_obj = QuestionType.objects.first()
                            if question_type_obj:
                                question_type_id = str(question_type_obj.question_type_id)
                                logger.warning(f"Q{question_number}: Using fallback question type")
                    
                    if not question_type_obj:
                        logger.error("No question types available in database")
                        return Response({
                            'error': 'No QuestionType found in database - please set up question types first'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
                    # Create enhanced answer data with proper metadata
                    enhanced_answer_data = {
                        'student_answer': student_answer,
                        'question_type_id': question_type_id,
                        'question_type_name': question_type_obj.type,
                        'frontend_question_type': frontend_question_type,
                        'has_actual_mapping': question_number in actual_question_types,
                        'submitted_at': timezone.now().isoformat(),
                        'answer_source': 'enhanced_frontend'
                    }
                    
                    # Add correct answer if available from mapping
                    if question_number in actual_question_types:
                        enhanced_answer_data['correct_answer'] = actual_question_types[question_number]['correct_answer']
                        enhanced_answer_data['passage_id'] = actual_question_types[question_number]['passage_id']
                    
                    # Create or update StudentAnswer record
                    student_answer_obj, created = StudentAnswer.objects.get_or_create(
                        submit_answer=submit_answer,
                        question_number=question_number,
                        defaults={
                            'question_type': question_type_obj,
                            'student_answer': enhanced_answer_data,
                            'session_id': session_id,
                            'is_correct': False,  # Will be calculated later
                            'scored_at': None
                        }
                    )
                    
                    if not created:
                        # Update existing answer with enhanced data
                        student_answer_obj.question_type = question_type_obj
                        student_answer_obj.student_answer = enhanced_answer_data
                        student_answer_obj.session_id = session_id
                        student_answer_obj.is_correct = False  # Reset for re-scoring
                        student_answer_obj.scored_at = None
                        student_answer_obj.save()
                        logger.info(f"Q{question_number}: Updated existing answer")
                    else:
                        logger.info(f"Q{question_number}: Created new answer")
                    
                    # Add to processed answers with enhanced metadata
                    processed_answers.append({
                        'question_number': question_number,
                        'student_answer': student_answer,
                        'question_type_id': question_type_id,
                        'question_type_name': question_type_obj.type,
                        'has_actual_mapping': question_number in actual_question_types,
                        'frontend_type': frontend_question_type,
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

    def _get_test_id_from_session(self, session_id):
        """
        Get the correct test_id for a session from exam session data.
        
        This method tries to find the test_id from various sources:
        1. From existing SubmitAnswer records
        2. From exam session data
        3. From student answer data
        
        Args:
            session_id: Session ID to find test_id for
            
        Returns:
            str: Test ID if found, None otherwise
        """
        try:
            # First, check if there's an existing SubmitAnswer with correct test_id
            existing_submission = SubmitAnswer.objects.filter(session_id=session_id).first()
            if existing_submission:
                # Check if this test_id actually exists and has questions
                from reading.models import ReadingTest
                try:
                    test = ReadingTest.objects.get(test_id=existing_submission.test_id)
                    if test.passages.exists():
                        logger.info(f"Found existing test_id from SubmitAnswer: {existing_submission.test_id}")
                        return str(existing_submission.test_id)
                except ReadingTest.DoesNotExist:
                    logger.warning(f"Existing test_id {existing_submission.test_id} not found in ReadingTest")
                    
            # Try to find from exam session data (you may need to implement this based on your exam session structure)
            # For now, we'll try to find from any existing student answers
            student_answers = StudentAnswer.objects.filter(session_id=session_id)
            if student_answers.exists():
                # Check if any answer has test_id in metadata
                for answer in student_answers:
                    if isinstance(answer.student_answer, dict):
                        test_id = answer.student_answer.get('test_id')
                        if test_id:
                            # Verify this test_id exists
                            from reading.models import ReadingTest
                            try:
                                test = ReadingTest.objects.get(test_id=test_id)
                                if test.passages.exists():
                                    logger.info(f"Found test_id from student answer metadata: {test_id}")
                                    return str(test_id)
                            except ReadingTest.DoesNotExist:
                                logger.warning(f"Test_id {test_id} from metadata not found in ReadingTest")
            
            # If no test_id found, return None
            logger.warning(f"No valid test_id found for session {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting test_id from session {session_id}: {str(e)}")
            return None
    
    
    # # New function
    # def _get_test_id_from_session(self, session_id):
    #     """
    #     Get the correct test_id for a session from exam session data.
        
    #     This method tries to find the test_id from various sources in priority order:
    #     1. From ReadingExamSession via API call to Academiq (PRIMARY)
    #     2. From existing SubmitAnswer records
    #     3. From student answer metadata
        
    #     Args:
    #         session_id: Session ID to find test_id for
            
    #     Returns:
    #         str: Test ID if found, None otherwise
    #     """
    #     try:
    #         # PRIORITY 1: Try to get test_id from ReadingExamSession via API call to Academiq
    #         try:
    #             import requests
    #             academiq_url = f"http://127.0.0.1:8000/api/start-exam/reading-exam-sessions/{session_id}/"
    #             logger.info(f"Fetching session data from Academiq: {academiq_url}")
                
    #             response = requests.get(academiq_url, timeout=10)
    #             if response.status_code == 200:
    #                 session_data = response.json()
    #                 test_id = session_data.get('reading_test_id') or session_data.get('test_id')
                    
    #                 if test_id:
    #                     # Verify this test_id exists in our ReadingTest database
    #                     from reading.models import ReadingTest
    #                     try:
    #                         test = ReadingTest.objects.get(test_id=test_id)
    #                         if test.passages.exists():
    #                             logger.info(f"Found valid test_id from ReadingExamSession: {test_id}")
    #                             return str(test_id)
    #                     except ReadingTest.DoesNotExist:
    #                         logger.warning(f"Test_id {test_id} from ReadingExamSession not found in ReadingTest")
    #                 else:
    #                     logger.warning(f"No test_id found in ReadingExamSession data: {session_data}")
    #             else:
    #                 logger.warning(f"Failed to fetch session from Academiq. Status: {response.status_code}")
                    
    #         except requests.exceptions.RequestException as e:
    #             logger.error(f"Error calling Academiq API for session {session_id}: {str(e)}")
    #         except Exception as e:
    #             logger.error(f"Unexpected error fetching session data: {str(e)}")

    #         # PRIORITY 2: Check if there's an existing SubmitAnswer with correct test_id
    #         existing_submission = SubmitAnswer.objects.filter(session_id=session_id).first()
    #         if existing_submission:
    #             # Check if this test_id actually exists and has questions
    #             from reading.models import ReadingTest
    #             try:
    #                 test = ReadingTest.objects.get(test_id=existing_submission.test_id)
    #                 if test.passages.exists():
    #                     logger.info(f"Found existing test_id from SubmitAnswer: {existing_submission.test_id}")
    #                     return str(existing_submission.test_id)
    #             except ReadingTest.DoesNotExist:
    #                 logger.warning(f"Existing test_id {existing_submission.test_id} not found in ReadingTest")

    #         # PRIORITY 3: Try to find from student answer metadata
    #         student_answers = StudentAnswer.objects.filter(session_id=session_id)
    #         if student_answers.exists():
    #             # Check if any answer has test_id in metadata
    #             for answer in student_answers:
    #                 if isinstance(answer.student_answer, dict):
    #                     test_id = answer.student_answer.get('test_id')
    #                     if test_id:
    #                         # Verify this test_id exists
    #                         from reading.models import ReadingTest
    #                         try:
    #                             test = ReadingTest.objects.get(test_id=test_id)
    #                             if test.passages.exists():
    #                                 logger.info(f"Found test_id from student answer metadata: {test_id}")
    #                                 return str(test_id)
    #                         except ReadingTest.DoesNotExist:
    #                             logger.warning(f"Test_id {test_id} from metadata not found in ReadingTest")
            
    #         # If no test_id found, return None
    #         logger.warning(f"No valid test_id found for session {session_id}")
    #         return None
            
    #     except Exception as e:
    #         logger.error(f"Error getting test_id from session {session_id}: {str(e)}")
    #         return None


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

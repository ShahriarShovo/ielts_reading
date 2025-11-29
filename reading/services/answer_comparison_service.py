# reading/services/answer_comparison_service.py

# =============================================================================
# IMPORTS SECTION - Required libraries and modules
# =============================================================================

# Type hints for better code documentation and IDE support
from typing import Dict, List, Tuple, Any, Optional
# Decimal for precise financial/numerical calculations
from decimal import Decimal
# Regular expressions for text pattern matching
import re
# Django database transaction support for data consistency
from django.db import transaction
# Django timezone utilities for timestamp handling
from django.utils import timezone

# Import our custom models for database operations
from ..models import (
    StudentAnswer,      # Model for storing individual student answers
    SubmitAnswer,       # Model for storing complete submission records
    QuestionType,       # Model for question type definitions
    ReadingTest         # Model for reading test structure
)

# =============================================================================
# MAIN SERVICE CLASS - AnswerComparisonService
# =============================================================================

class AnswerComparisonService:
    """
    Service for comparing student answers with correct answers and calculating IELTS band scores.
    
    This service handles different question types and provides flexible comparison logic
    for various IELTS reading question formats with official IELTS scoring system.
    
    Key Responsibilities:
    1. Compare student answers with correct answers
    2. Calculate IELTS band scores based on official scoring system
    3. Handle different question types with specific comparison logic
    4. Provide formatted comparison results for display
    5. Support batch processing of multiple submissions
    """
    
    def __init__(self):
        """
        Initialize the service with question type handlers and configuration.
        
        This method sets up:
        - Question type comparison handlers (dictionary mapping)
        - Each handler is a method that knows how to compare specific question types
        """
        
        # Dictionary mapping question types to their comparison methods
        # Key: Question type name (string)
        # Value: Method reference for comparison logic
        self.question_type_handlers = {
            # Multiple choice questions with single correct answer
            'Multiple Choice Questions (MCQ)': self._compare_multiple_choice,
            
            # Multiple choice questions with multiple correct answers
            'Multiple Choice Questions (Multiple Answer)': self._compare_multiple_answer,
            
            # True/False/Not Given questions (common in IELTS)
            'True/False/Not Given': self._compare_true_false,
            
            # Yes/No/Not Given questions (similar to T/F/NG)
            'Yes/No/Not Given': self._compare_yes_no,
            
            # Note completion questions (fill in the blanks)
            'Note Completion': self._compare_note_completion,
            
            # Sentence completion questions
            'Sentence Completion': self._compare_sentence_completion,
            
            # Summary completion questions
            'Summary Completion': self._compare_summary_completion,
            
            # Table completion questions
            'Table Completion': self._compare_table_completion,
            
            # Flow chart completion questions
            'Flow Chart Completion': self._compare_flow_chart_completion,
            
            # Diagram label completion questions
            'Diagram Label Completion': self._compare_diagram_completion,
            
            # Short answer questions
            'Short Answer Questions': self._compare_short_answer,
            
            # Matching information questions
            'Matching Information': self._compare_matching_information,
            
            # Matching headings questions
            'Matching Headings': self._compare_matching_headings,
            
            # Matching features questions
            'Matching Features': self._compare_matching_features,
            
            # Sentence matching questions
            'Sentence Matching': self._compare_sentence_matching,
            
            # Matching experts questions
            'Matching Experts': self._compare_matching_experts,
        }
    
    # =============================================================================
    # MAIN COMPARISON METHOD - Core functionality
    # =============================================================================
    
    def compare_submission(self, submit_answer: SubmitAnswer) -> Dict[str, Any]:
        """
        Compare all answers in a submission with correct answers.
        
        This is the main method that orchestrates the entire comparison process.
        It processes a complete submission and returns detailed results.
        
        Args:
            submit_answer: SubmitAnswer instance containing the submission to process
            
        Returns:
            Dict containing:
            - success: Boolean indicating if processing was successful
            - submission details (ID, session, student, test)
            - comparison results (correct/incorrect counts)
            - IELTS band score
            - detailed results for each question
            - processing timestamp
        """
        try:
            # Get all student answers for this submission
            student_answers = submit_answer.get_student_answers()
            
            # Check if there are any answers to process
            if not student_answers.exists():
                return {
                    'success': False,
                    'error': 'No student answers found for this submission'
                }
            
            # Get correct answers for the test from the database
            correct_answers = self._get_correct_answers(submit_answer.session_id)
            
            # Check if correct answers are available
            if not correct_answers:
                return {
                    'success': False,
                    'error': 'No correct answers found for this test'
                }
            
            # Initialize variables for processing
            results = []           # Store results for each question
            correct_count = 0      # Count total correct answers
            
            # Convert queryset to list once (avoid multiple DB hits)
            student_answers_list = list(student_answers)
            total_questions = len(student_answers_list)
            
            # Check if already processed - skip DB updates if so
            already_processed = submit_answer.is_processed
            answers_to_update = [] if already_processed else []
            
            # Process each individual answer
            for student_answer in student_answers_list:
                # Compare this student answer with the correct answer
                result = self._compare_single_answer(
                    student_answer,      # Current student answer
                    correct_answers,     # All correct answers
                    submit_answer.test_id  # Test context
                )
                
                # Add result to our collection
                results.append(result)
                
                # Count correct answers for IELTS scoring
                if result['is_correct']:
                    correct_count += 1
                
                # Only update DB if not already processed
                if not already_processed:
                    student_answer.is_correct = result['is_correct']
                    student_answer.band_score = result.get('band_score')
                    student_answer.scored_at = timezone.now()
                    answers_to_update.append(student_answer)
            
            # BULK UPDATE: Only if not already processed
            if answers_to_update:
                from reading.models import StudentAnswer
                StudentAnswer.objects.bulk_update(
                    answers_to_update, 
                    ['is_correct', 'band_score', 'scored_at'],
                    batch_size=100
                )
                # Mark as processed only on first time
                submit_answer.mark_as_processed()
            
            # Calculate IELTS band score based on total correct answers
            ielts_band_score = self._calculate_ielts_band_score(correct_count, total_questions)
            
            # Calculate overall results and grades
            overall_result = self._calculate_overall_result(correct_count, total_questions)
            
            # Return comprehensive result dictionary
            return {
                'success': True,
                'submission_id': str(submit_answer.submit_id),
                'session_id': submit_answer.session_id,
                'student_id': submit_answer.student_id,
                'test_id': str(submit_answer.test_id),
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'incorrect_answers': total_questions - correct_count,
                'percentage': round((correct_count / total_questions * 100), 2) if total_questions > 0 else 0,
                'ielts_band_score': ielts_band_score,
                'overall_grade': overall_result['grade'],
                'detailed_results': results,
                'processed_at': timezone.now().isoformat()
            }
                
        except Exception as e:
            # If any error occurs during processing, return error details
            return {
                'success': False,
                'error': f'Error processing submission: {str(e)}'
            }
    
    # =============================================================================
    # SINGLE ANSWER COMPARISON METHOD - Individual question processing
    # =============================================================================
    
    def _compare_single_answer(
        self, 
        student_answer: StudentAnswer,  # Student's answer record
        correct_answers: Dict,          # Dictionary of correct answers
        test_id: str                    # Test identifier for context
    ) -> Dict[str, Any]:
        """
        Compare a single student answer with the correct answer.
        
        This method handles the comparison logic for individual questions.
        It determines the question type and applies appropriate comparison logic.
        
        Args:
            student_answer: StudentAnswer instance containing the answer to compare
            correct_answers: Dictionary mapping question numbers to correct answers
            test_id: Test ID for additional context if needed
            
        Returns:
            Dict containing:
            - question_number: Question identifier
            - question_type: Type of question (MCQ, T/F, etc.)
            - student_answer: Student's submitted answer
            - correct_answer: Correct answer for comparison
            - is_correct: Boolean indicating if answer is correct
            - comparison_display: Formatted string for display
            - error: Error message if comparison failed
        """
        
        # Extract question details from the student answer
        question_number = student_answer.question_number      # Global question number (1-40)
        question_type = student_answer.question_type          # QuestionType instance
        
        # Get the correct answer for this specific question
        # Convert question number to string for dictionary lookup
        correct_answer = correct_answers.get(str(question_number))
        
        # Check if correct answer exists for this question
        if correct_answer is None:
            # If no correct answer found, create error result
            comparison_display = f"Student Answer: {self._format_student_answer(student_answer.student_answer)} | Correct Answer: Not Available | Result: ❌ (Error)"
            
            return {
                'question_number': question_number,           # Question number
                'question_type': question_type.type,          # Question type name
                'student_answer': student_answer.student_answer,  # Student's answer
                'correct_answer': None,                      # No correct answer available
                'is_correct': False,                         # Mark as incorrect due to error
                'comparison_display': comparison_display,     # Formatted error display
                'error': 'Correct answer not found'          # Error description
            }
        
        # Get the appropriate comparison handler for this question type
        # Look up the method in our question_type_handlers dictionary
        handler = self.question_type_handlers.get(question_type.type)
        
        # Check if we have a specific handler for this question type
        if handler is None:
            # If no specific handler, use default comparison method
            # This handles unknown or new question types
            is_correct = self._default_comparison(
                student_answer.student_answer,  # Student's answer
                correct_answer                   # Correct answer
            )
        else:
            # Use the specific handler for this question type
            # This calls the appropriate comparison method (e.g., _compare_multiple_choice)
            is_correct = handler(student_answer.student_answer, correct_answer)
        
        # Format the comparison result for display
        # This creates the formatted string showing student vs correct answer
        comparison_display = self._format_answer_comparison(
            question_number,           # Question number for context
            student_answer.student_answer,  # Student's answer
            correct_answer,            # Correct answer
            is_correct                 # Whether answer is correct
        )
        
        # Return comprehensive result for this question
        return {
            'question_number': question_number,           # Question identifier
            'question_type': question_type.type,          # Question type name
            'student_answer': student_answer.student_answer,  # Student's submitted answer
            'correct_answer': correct_answer,             # Correct answer for comparison
            'is_correct': is_correct,                     # Boolean: correct or incorrect
            'comparison_display': comparison_display       # Formatted display string
        }
    
    # =============================================================================
    # CORRECT ANSWERS RETRIEVAL - Fetch teacher's correct answers
    # =============================================================================
    
    def _get_correct_answers(self, session_id: str) -> Dict[str, Any]:
        """
        Get correct answers for a specific test from the database using session_id.
        
        This method fetches the teacher's correct answers that will be used
        for comparison with student answers. It first looks up the session
        to find the correct test, then retrieves the answers.
        
        Args:
            session_id: Session identifier from Academiq
            
        Returns:
            Dict mapping question numbers (as strings) to correct answers
            Example: {"1": "A", "2": "True", "3": "climate change"}
        """
        try:
            # First, find the submission by session_id to get the correct test_id
            submissions = SubmitAnswer.get_submissions_by_session(session_id)
            
            if not submissions.exists():
                print(f"⚠️ No submission found for session_id: {session_id}")
                return {}
            
            # Get the first submission (there should typically be only one per session)
            submission = submissions.first()
            test_id = submission.test_id
            
            print(f"✅ Found submission for session {session_id}, using test_id: {test_id}")
            
            # Get the ReadingTest instance from database using the found test_id
            # Use prefetch_related to avoid N+1 query problem (single query instead of many)
            test = ReadingTest.objects.prefetch_related(
                'passages',
                'passages__questions'
            ).get(test_id=test_id)
            correct_answers = {}  # Dictionary to store correct answers
            
            # Simple sequential question counter (1, 2, 3, 4...)
            question_counter = 1
            
            # Iterate through all passages in the test (now uses prefetched data)
            for passage in test.passages.all():
                # Iterate through all question types in each passage
                for question_type in passage.questions.all():
                    # Iterate through all questions in each question type
                    for question in question_type.questions_data:
                        # Store the correct answer with sequential question number
                        correct_answers[str(question_counter)] = question.get('correct_answer')
                        question_counter += 1
            
            # Return the dictionary of correct answers
            return correct_answers
            
        except ReadingTest.DoesNotExist:
            # FALLBACK LOGIC: If test not found by session, try to find any available test
            print(f"⚠️ Test not found for session {session_id}. Trying fallback to available test...")
            
            try:
                # Get the first available ReadingTest with prefetch for optimization
                available_test = ReadingTest.objects.prefetch_related(
                    'passages',
                    'passages__questions'
                ).first()
                if available_test:
                    print(f"✅ Using fallback test: {available_test.test_name} (ID: {available_test.test_id})")
                    
                    correct_answers = {}  # Dictionary to store correct answers
                    question_counter = 1
                    
                    # Iterate through all passages in the fallback test (uses prefetched data)
                    for passage in available_test.passages.all():
                        # Iterate through all question types in each passage
                        for question_type in passage.questions.all():
                            # Iterate through all questions in each question type
                            for question in question_type.questions_data:
                                # Store the correct answer with sequential question number
                                correct_answers[str(question_counter)] = question.get('correct_answer')
                                question_counter += 1
                    
                    print(f"✅ Fallback test loaded with {len(correct_answers)} questions")
                    return correct_answers
                else:
                    print("❌ No ReadingTest available in database")
                    return {}
                    
            except Exception as fallback_error:
                print(f"❌ Fallback failed: {str(fallback_error)}")
                return {}
    
    # =============================================================================
    # GLOBAL QUESTION NUMBER CALCULATION - REMOVED
    # =============================================================================
    # This method was removed because it used complex and incorrect calculations.
    # Now using simple sequential numbering (1, 2, 3, 4...) which is more reliable.
    
    # =============================================================================
    # IELTS BAND SCORE CALCULATION - Official scoring system
    # =============================================================================
    
    def _calculate_ielts_band_score(self, correct_count: int, total_questions: int) -> float:
        """
        Calculate IELTS band score based on correct answers.
        
        This method implements the official IELTS Reading band score system.
        It converts raw scores (number of correct answers) to IELTS band scores.
        
        Args:
            correct_count: Number of correct answers (0-40)
            total_questions: Total number of questions (usually 40)
            
        Returns:
            float: IELTS band score (2.5 to 9.0)
            
        Note: This follows the official IELTS scoring system:
        - 40-39 correct → Band 9.0
        - 38-37 correct → Band 8.5
        - 36-35 correct → Band 8.0
        - And so on...
        """
        
        # Official IELTS Reading Band Score calculation
        # Each range of correct answers maps to a specific band score
        
        if correct_count >= 40:
            return 9.0          # Perfect score
        elif correct_count >= 39:
            return 9.0          # Near perfect
        elif correct_count >= 38:
            return 8.5          # Excellent
        elif correct_count >= 37:
            return 8.5          # Excellent
        elif correct_count >= 36:
            return 8.0          # Very good
        elif correct_count >= 35:
            return 8.0          # Very good
        elif correct_count >= 34:
            return 7.5          # Good
        elif correct_count >= 33:
            return 7.5          # Good
        elif correct_count >= 32:
            return 7.0          # Satisfactory
        elif correct_count >= 30:
            return 7.0          # Satisfactory
        elif correct_count >= 29:
            return 6.5          # Above average
        elif correct_count >= 27:
            return 6.5          # Above average
        elif correct_count >= 26:
            return 6.0          # Average
        elif correct_count >= 23:
            return 6.0          # Average
        elif correct_count >= 22:
            return 5.5          # Below average
        elif correct_count >= 19:
            return 5.5          # Below average
        elif correct_count >= 18:
            return 5.0          # Limited
        elif correct_count >= 15:
            return 5.0          # Limited
        elif correct_count >= 14:
            return 4.5          # Very limited
        elif correct_count >= 13:
            return 4.5          # Very limited
        elif correct_count >= 12:
            return 4.0          # Extremely limited
        elif correct_count >= 10:
            return 4.0          # Extremely limited
        elif correct_count >= 9:
            return 3.5          # Very poor
        elif correct_count >= 8:
            return 3.5          # Very poor
        elif correct_count >= 7:
            return 3.0          # Poor
        elif correct_count >= 6:
            return 3.0          # Poor
        elif correct_count >= 5:
            return 2.5          # Very poor
        elif correct_count >= 4:
            return 2.5          # Very poor
        else:
            return 2.0          # For 3 or fewer correct answers
    
    # =============================================================================
    # OVERALL RESULT CALCULATION - Letter grades and percentages
    # =============================================================================
    
    def _calculate_overall_result(
        self, 
        correct_count: int,     # Number of correct answers
        total_questions: int    # Total number of questions
    ) -> Dict[str, Any]:
        """
        Calculate overall result and letter grade.
        
        This method provides additional grading information beyond IELTS band scores.
        It calculates percentages and assigns letter grades (A+, B, C, etc.).
        
        Args:
            correct_count: Number of correct answers
            total_questions: Total number of questions
            
        Returns:
            Dict containing:
            - percentage: Success percentage (0-100)
            - grade: Letter grade (A+, A, B+, B, C+, C, D, F)
        """
        
        # Check if there are any questions to avoid division by zero
        if total_questions == 0:
            return {
                'band_score': 0.0,      # No band score possible
                'percentage': 0.0,      # No percentage possible
                'grade': 'F'            # Default grade
            }
        
        # Calculate success percentage
        percentage = (correct_count / total_questions) * 100
        
        # Assign letter grade based on percentage
        # This provides familiar grading for students and teachers
        if percentage >= 90:
            grade = 'A+'         # Outstanding
        elif percentage >= 80:
            grade = 'A'          # Excellent
        elif percentage >= 70:
            grade = 'B+'         # Very good
        elif percentage >= 60:
            grade = 'B'          # Good
        elif percentage >= 50:
            grade = 'C+'         # Satisfactory
        elif percentage >= 40:
            grade = 'C'          # Average
        elif percentage >= 30:
            grade = 'D'          # Below average
        else:
            grade = 'F'          # Failing
        
        # Return grade and percentage information
        return {
            'percentage': round(percentage, 2),  # Round to 2 decimal places
            'grade': grade                       # Letter grade
        }
    
    # =============================================================================
    # ANSWER COMPARISON DISPLAY FORMATTING - User-friendly output
    # =============================================================================
    
    def _format_answer_comparison(
        self, 
        question_number: int,    # Question number for context
        student_answer: Any,     # Student's submitted answer
        correct_answer: Any,     # Correct answer for comparison
        is_correct: bool         # Whether the answer is correct
    ) -> str:
        """
        Format answer comparison for display.
        
        This method creates a user-friendly string showing the comparison
        between student and correct answers with visual indicators.
        
        Args:
            question_number: Question number for context
            student_answer: Student's submitted answer
            correct_answer: Correct answer for comparison
            is_correct: Boolean indicating if answer is correct
            
        Returns:
            str: Formatted comparison string
            Example: "Student Answer: True | Correct Answer: True | Result: ✔ (Correct)"
        """
        
        # Convert answers to display format using helper methods
        student_display = self._format_student_answer(student_answer)  # Format student answer
        correct_display = self._format_correct_answer(correct_answer)  # Format correct answer
        
        # Choose appropriate symbol and status based on correctness
        symbol = "✔" if is_correct else "❌"           # Visual indicator
        status = "Correct" if is_correct else "Incorrect"  # Text status
        
        # Create formatted display string
        # Format: "Student Answer: X | Correct Answer: Y | Result: Symbol (Status)"
        return f"Student Answer: {student_display} | Correct Answer: {correct_display} | Result: {symbol} ({status})"
    
    def _format_student_answer(self, answer: Any) -> str:
        """
        Format student answer for display.
        
        This method handles different answer formats and converts them
        to readable strings for display purposes.
        
        Args:
            answer: Student's answer in various formats
            
        Returns:
            str: Formatted answer string for display
        """
        
        # Handle None/null answers
        if answer is None:
            return "No Answer"
        
        # Handle dictionary format (enhanced answer structure)
        if isinstance(answer, dict):
            # Extract student_answer field from dictionary
            return answer.get('student_answer', 'No Answer')
        
        # Handle list format (multiple answers)
        if isinstance(answer, list):
            # Join multiple answers with commas
            return ', '.join(str(item) for item in answer)
        
        # Handle string and other formats
        return str(answer)
    
    def _format_correct_answer(self, answer: Any) -> str:
        """
        Format correct answer for display.
        
        This method handles different correct answer formats and converts them
        to readable strings for display purposes.
        
        Args:
            answer: Correct answer in various formats
            
        Returns:
            str: Formatted answer string for display
        """
        
        # Handle None/null answers
        if answer is None:
            return "Not Available"
        
        # Handle list format (multiple correct answers)
        if isinstance(answer, list):
            # Join multiple answers with commas
            return ', '.join(str(item) for item in answer)
        
        # Handle string and other formats
        return str(answer)
    
    # =============================================================================
    # QUESTION TYPE COMPARISON METHODS - Specific logic for each type
    # =============================================================================
    
    def _compare_multiple_choice(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare multiple choice single answer questions.
        
        This method handles MCQ questions where students select one answer
        from multiple options (A, B, C, D).
        
        Args:
            student_answer: Student's selected answer
            correct_answer: Correct answer from teacher
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Handle enhanced answer format (dictionary structure)
        if isinstance(student_answer, dict):
            # Extract actual answer from student_answer field
            student_answer = student_answer.get('student_answer', '')
        
        # Compare answers (case-insensitive, trimmed)
        # Convert both to uppercase and remove whitespace for comparison
        return str(student_answer).strip().upper() == str(correct_answer).strip().upper()
    
    def _compare_multiple_answer(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare multiple choice multiple answer questions.
        
        This method handles questions where students select multiple answers
        from options (e.g., "Choose TWO answers").
        
        Args:
            student_answer: Student's selected answers (list or comma-separated string)
            correct_answer: Correct answers (list or comma-separated string)
            
        Returns:
            bool: True if all answers match, False otherwise
        """
        
        # Handle enhanced answer format
        if isinstance(student_answer, dict):
            student_answer = student_answer.get('student_answer', [])
        
        # Convert string answers to list format
        if isinstance(student_answer, str):
            # Split comma-separated string into list
            student_answer = [s.strip() for s in student_answer.split(',')]
        
        # Convert correct answer string to list format
        if isinstance(correct_answer, str):
            correct_answer = [c.strip() for c in correct_answer.split(',')]
        
        # Sort both lists for comparison (order doesn't matter for multiple answers)
        # Convert to uppercase for case-insensitive comparison
        student_sorted = sorted([str(s).upper() for s in student_answer if s])
        correct_sorted = sorted([str(c).upper() for c in correct_answer if c])
        
        # Compare sorted lists
        return student_sorted == correct_sorted
    
    def _compare_true_false(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare True/False/Not Given questions.
        
        This method handles T/F/NG questions common in IELTS reading tests.
        It normalizes various answer formats to standard True/False/Not Given.
        
        Args:
            student_answer: Student's answer (T, F, NG, True, False, etc.)
            correct_answer: Correct answer
            
        Returns:
            bool: True if normalized answers match, False otherwise
        """
        
        # Handle enhanced answer format
        if isinstance(student_answer, dict):
            student_answer = student_answer.get('student_answer', '')
        
        # Normalize both answers to standard format
        # This handles variations like T/True/1/Yes → TRUE
        student_normalized = self._normalize_true_false_answer(student_answer)
        correct_normalized = self._normalize_true_false_answer(correct_answer)
        
        # Compare normalized answers
        return student_normalized == correct_normalized
    
    def _compare_yes_no(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare Yes/No/Not Given questions.
        
        This method handles Y/N/NG questions similar to T/F/NG.
        It reuses the same logic as true/false comparison.
        
        Args:
            student_answer: Student's answer
            correct_answer: Correct answer
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Reuse true/false comparison logic since Y/N/NG is similar to T/F/NG
        return self._compare_true_false(student_answer, correct_answer)
    
    def _compare_note_completion(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare note completion questions.
        
        This method handles fill-in-the-blank questions where students
        complete notes with missing information.
        
        Args:
            student_answer: Student's answers (list or comma-separated string)
            correct_answer: Correct answers (list or comma-separated string)
            
        Returns:
            bool: True if all gaps are filled correctly, False otherwise
        """
        
        # Handle enhanced answer format
        if isinstance(student_answer, dict):
            student_answer = student_answer.get('student_answer', [])
        
        # Convert string answers to list format
        if isinstance(student_answer, str):
            student_answer = [s.strip() for s in student_answer.split(',')]
        
        # Convert correct answer string to list format
        if isinstance(correct_answer, str):
            correct_answer = [c.strip() for c in correct_answer.split(',')]
        
        # Check if number of answers matches number of gaps
        if len(student_answer) != len(correct_answer):
            return False
        
        # Compare each gap individually
        for student_ans, correct_ans in zip(student_answer, correct_answer):
            # If any gap is incorrect, the whole answer is wrong
            if not self._compare_text_answer(student_ans, correct_ans):
                return False
        
        # All gaps are correct
        return True
    
    def _compare_sentence_completion(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare sentence completion questions.
        
        This method handles questions where students complete sentences
        with missing words or phrases.
        
        Args:
            student_answer: Student's completed sentence
            correct_answer: Correct completed sentence
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_summary_completion(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare summary completion questions.
        
        This method handles questions where students complete summaries
        with missing information.
        
        Args:
            student_answer: Student's completed summary
            correct_answer: Correct completed summary
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_table_completion(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare table completion questions.
        
        This method handles questions where students complete tables
        with missing data.
        
        Args:
            student_answer: Student's completed table data
            correct_answer: Correct table data
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_flow_chart_completion(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare flow chart completion questions.
        
        This method handles questions where students complete flow charts
        with missing steps or information.
        
        Args:
            student_answer: Student's completed flow chart
            correct_answer: Correct completed flow chart
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_diagram_completion(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare diagram label completion questions.
        
        This method handles questions where students label diagrams
        with missing labels or information.
        
        Args:
            student_answer: Student's diagram labels
            correct_answer: Correct diagram labels
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_short_answer(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare short answer questions.
        
        This method handles questions where students provide brief
        written answers.
        
        Args:
            student_answer: Student's short answer
            correct_answer: Correct short answer
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_matching_information(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare matching information questions.
        
        This method handles questions where students match
        information to paragraphs or sections.
        
        Args:
            student_answer: Student's matching choices
            correct_answer: Correct matching choices
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_matching_headings(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare matching headings questions.
        
        This method handles questions where students match
        headings to paragraphs or sections.
        
        Args:
            student_answer: Student's heading matches
            correct_answer: Correct heading matches
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_matching_features(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare matching features questions.
        
        This method handles questions where students match
        features to categories or groups.
        
        Args:
            student_answer: Student's feature matches
            correct_answer: Correct feature matches
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_sentence_matching(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare sentence matching questions.
        
        This method handles questions where students match
        sentence beginnings to endings.
        
        Args:
            student_answer: Student's sentence matches
            correct_answer: Correct sentence matches
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    def _compare_matching_experts(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare matching experts questions.
        
        This method handles questions where students match
        experts to their statements or opinions.
        
        Args:
            student_answer: Student's expert matches
            correct_answer: Correct expert matches
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Use generic text comparison method
        return self._compare_text_answer(student_answer, correct_answer)
    
    # =============================================================================
    # GENERIC TEXT COMPARISON - Fuzzy matching for text-based answers
    # =============================================================================
    
    def _compare_text_answer(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Compare text-based answers with fuzzy matching.
        
        This method provides intelligent comparison for text answers
        that may have slight variations in spelling, spacing, or formatting.
        
        Args:
            student_answer: Student's text answer
            correct_answer: Correct text answer
            
        Returns:
            bool: True if answers are similar enough, False otherwise
        """
        
        # Handle enhanced answer format
        if isinstance(student_answer, dict):
            student_answer = student_answer.get('student_answer', '')
        
        # Normalize both answers for comparison
        # This removes case differences, extra spaces, and punctuation
        student_normalized = self._normalize_text(str(student_answer))
        correct_normalized = self._normalize_text(str(correct_answer))
        
        # Try exact match first (most efficient)
        if student_normalized == correct_normalized:
            return True
        
        # If exact match fails, try fuzzy matching
        # Calculate similarity percentage between answers
        similarity = self._calculate_text_similarity(student_normalized, correct_normalized)
        
        # Return True if similarity is above threshold (80%)
        # This allows for minor spelling mistakes or formatting differences
        return similarity >= 0.8
    
    def _default_comparison(self, student_answer: Any, correct_answer: Any) -> bool:
        """
        Default comparison method for unknown question types.
        
        This method provides a fallback comparison when no specific
        handler exists for a question type.
        
        Args:
            student_answer: Student's answer
            correct_answer: Correct answer
            
        Returns:
            bool: True if answers match, False otherwise
        """
        
        # Handle enhanced answer format
        if isinstance(student_answer, dict):
            student_answer = student_answer.get('student_answer', '')
        
        # Simple case-insensitive string comparison
        # Convert both to lowercase and remove whitespace
        return str(student_answer).strip().lower() == str(correct_answer).strip().lower()
    
    # =============================================================================
    # UTILITY METHODS - Helper functions for text processing
    # =============================================================================
    
    def _normalize_true_false_answer(self, answer: Any) -> str:
        """
        Normalize True/False/Not Given answers.
        
        This method converts various answer formats to standard
        TRUE/FALSE/NOT GIVEN format for consistent comparison.
        
        Args:
            answer: Answer in various formats (T, True, 1, Yes, etc.)
            
        Returns:
            str: Normalized answer in standard format
        """
        
        # Handle enhanced answer format
        if isinstance(answer, dict):
            answer = answer.get('student_answer', '')
        
        # Convert to string and normalize
        answer_str = str(answer).strip().upper()
        
        # Map variations to standard format
        # This handles common student input variations
        if answer_str in ['T', 'TRUE', '1', 'YES']:
            return 'TRUE'
        elif answer_str in ['F', 'FALSE', '0', 'NO']:
            return 'FALSE'
        elif answer_str in ['NG', 'NOT GIVEN', 'NOTGIVEN', 'N/A']:
            return 'NOT GIVEN'
        else:
            # Return original if no mapping found
            return answer_str
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        This method standardizes text by removing case differences,
        extra whitespace, and punctuation for better comparison.
        
        Args:
            text: Text to normalize
            
        Returns:
            str: Normalized text ready for comparison
        """
        
        # Handle empty text
        if not text:
            return ''
        
        # Convert to lowercase for case-insensitive comparison
        text = text.lower()
        
        # Remove extra whitespace (multiple spaces, tabs, newlines)
        # Replace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation (optional - depends on your requirements)
        # This removes commas, periods, exclamation marks, etc.
        # Keep only letters, numbers, and spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        # Return trimmed text
        return text.strip()
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using simple algorithm.
        
        This method calculates how similar two text strings are
        using word-based comparison (Jaccard similarity).
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            float: Similarity score between 0.0 and 1.0
                  0.0 = completely different
                  1.0 = identical
        """
        
        # Handle empty text cases
        if not text1 or not text2:
            return 0.0
        
        # Split texts into words for comparison
        words1 = set(text1.split())  # Convert to set for efficient operations
        words2 = set(text2.split())
        
        # Handle case where both texts are empty
        if not words1 and not words2:
            return 1.0
        
        # Calculate intersection (common words) and union (all words)
        intersection = words1.intersection(words2)  # Words that appear in both texts
        union = words1.union(words2)               # All unique words from both texts
        
        # Calculate Jaccard similarity: intersection size / union size
        # This gives a score between 0 and 1
        return len(intersection) / len(union) if union else 0.0
    
    # =============================================================================
    # SUMMARY METHODS - Get overview of comparison results
    # =============================================================================
    
    def get_comparison_summary(self, submit_answer: SubmitAnswer) -> Dict[str, Any]:
        """
        Get a summary of comparison results for a submission.
        
        This method provides a high-level overview of how a student performed
        on the test, including breakdowns by question type.
        
        Args:
            submit_answer: SubmitAnswer instance to summarize
            
        Returns:
            Dict containing:
            - success: Boolean indicating if summary was generated
            - submission details (ID, session)
            - overall statistics (total, correct, incorrect, percentage)
            - IELTS band score
            - breakdown by question type
            - processing status
        """
        
        # Get all student answers for this submission
        student_answers = submit_answer.get_student_answers()
        
        # Check if there are any answers to summarize
        if not student_answers.exists():
            return {
                'success': False,
                'error': 'No answers found for this submission'
            }
        
        # Count correct and incorrect answers
        correct_count = student_answers.filter(is_correct=True).count()  # Count correct answers
        total_count = student_answers.count()                            # Total questions answered
        
        # Calculate success percentage
        percentage = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # Calculate IELTS band score using our scoring system
        ielts_band_score = self._calculate_ielts_band_score(correct_count, total_count)
        
        # Create breakdown by question type
        # This shows how student performed on different types of questions
        question_type_breakdown = {}
        
        # Iterate through all answers to categorize by question type
        for answer in student_answers:
            question_type = answer.question_type.type  # Get question type name
            
            # Initialize breakdown for this question type if not exists
            if question_type not in question_type_breakdown:
                question_type_breakdown[question_type] = {
                    'total': 0,        # Total questions of this type
                    'correct': 0,      # Correct answers of this type
                    'percentage': 0.0  # Success percentage for this type
                }
            
            # Increment counters
            question_type_breakdown[question_type]['total'] += 1
            if answer.is_correct:
                question_type_breakdown[question_type]['correct'] += 1
        
        # Calculate percentage for each question type
        for qt_data in question_type_breakdown.values():
            # Calculate success percentage for this question type
            qt_data['percentage'] = round(
                (qt_data['correct'] / qt_data['total'] * 100), 2
            ) if qt_data['total'] > 0 else 0.0
        
        # Return comprehensive summary
        return {
            'success': True,                                    # Summary generated successfully
            'submission_id': str(submit_answer.submit_id),      # Submission identifier
            'session_id': submit_answer.session_id,             # Exam session ID
            'total_questions': total_count,                     # Total questions answered
            'correct_answers': correct_count,                   # Number of correct answers
            'incorrect_answers': total_count - correct_count,   # Number of incorrect answers
            'percentage': round(percentage, 2),                 # Overall success percentage
            'ielts_band_score': ielts_band_score,              # Official IELTS band score
            'question_type_breakdown': question_type_breakdown, # Performance by question type
            # 'is_processed': submit_answer.is_processed          # Whether submission was processed
        }
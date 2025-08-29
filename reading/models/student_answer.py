from django.db import models
import uuid
from django.utils import timezone
from .question_type import QuestionType
from .submit_answer import SubmitAnswer

class StudentAnswer(models.Model):
    """
    StudentAnswer: Stores individual student answers for reading exam questions.
    
    This model is used to store student answers when they submit their reading exam.
    It allows for comparison with correct answers and result calculation.
    
    Key Features:
    - Links to QuestionType for question details
    - Stores student's submitted answer (string or JSON array)
    - Tracks submission timestamp
    - Supports all question types (MCQ, T/F/NG, Note Completion, etc.)
    - Global question numbering support
    """
    
    # Unique identifier for the student answer
    answer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Link to the submission (one-to-many relationship)
    submit_answer = models.ForeignKey(
        SubmitAnswer, 
        on_delete=models.CASCADE, 
        related_name='student_answers',
        null=True,  # Allow null for existing records
        blank=True,  # Allow blank in forms
        help_text="Link to the submission this answer belongs to"
    )
    
    # Link to the question type this answer belongs to
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, related_name='student_answers')
    
    # Global question number (1-40 across all passages)
    question_number = models.IntegerField(help_text="Global question number (1-40)")
    
    # Student's submitted answer (can be string or JSON array)
    # Examples: "TRUE", "D", ["B", "D"], "paint", etc.
    student_answer = models.JSONField(help_text="Student's submitted answer (string or array)")
    
    # Session identifier to group answers from same exam session
    session_id = models.CharField(max_length=36, help_text="Session ID from Academiq")
    
    # When the answer was submitted
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="When this answer was submitted")
    
    # When the answer was compared and scored (filled after processing)
    scored_at = models.DateTimeField(null=True, blank=True, help_text="When this answer was compared and scored")
    
    # Whether the answer is correct (filled after comparison)
    is_correct = models.BooleanField(default=False, help_text="Whether student's answer is correct")
    
    # Band score for this question (filled after comparison)
    band_score = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        null=True, 
        blank=True, 
        help_text="Band score for this question"
    )

    class Meta:
        """
        Meta configuration for the StudentAnswer model.
        
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        - unique_together: Ensures one answer per question per session
        - ordering: Order by question number for easy retrieval
        - indexes: Performance optimization for common queries
        """
        db_table = 'reading_student_answers'
        verbose_name = 'Student Answer'
        verbose_name_plural = 'Student Answers'
        unique_together = ['session_id', 'question_number']  # Keep existing constraint for now
        ordering = ['question_number']  # Order by question number
        indexes = [
            models.Index(fields=['submit_answer', 'question_number']),
            models.Index(fields=['question_type', 'question_number']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['session_id']),  # Keep for backward compatibility
        ]

    def __str__(self):
        """
        String representation for admin panel, debugging, and logging.
        
        Returns a human-readable string that includes the session ID,
        question number, and student's answer for easy identification.
        """
        return f"Session {self.session_id} - Q{self.question_number}: {self.student_answer}"

    def mark_as_scored(self, is_correct, band_score=None):
        """
        Mark this answer as scored and update the result fields.
        
        This method is called after the answer has been compared
        with the correct answer and scored.
        
        Args:
            is_correct (bool): Whether the answer is correct
            band_score (decimal, optional): Band score for this question
        """
        self.is_correct = is_correct
        self.band_score = band_score
        self.scored_at = timezone.now()
        self.save(update_fields=['is_correct', 'band_score', 'scored_at'])

    def get_answer_display(self):
        """
        Get a formatted display of the student's answer.
        
        Returns a human-readable string representation of the answer.
        """
        if isinstance(self.student_answer, list):
            return ', '.join(str(ans) for ans in self.student_answer)
        return str(self.student_answer)

    @classmethod
    def get_session_answers(cls, session_id):
        """
        Get all answers for a specific session.
        
        Args:
            session_id (str): The session ID to get answers for
            
        Returns:
            QuerySet: All answers for the session, ordered by question number
        """
        return cls.objects.filter(session_id=session_id).order_by('question_number')

    @classmethod
    def get_session_summary(cls, session_id):
        """
        Get a summary of answers for a specific session.
        
        Args:
            session_id (str): The session ID to get summary for
            
        Returns:
            dict: Summary containing total questions, correct answers, and band score
        """
        answers = cls.get_session_answers(session_id)
        total_questions = answers.count()
        correct_answers = answers.filter(is_correct=True).count()
        
        # Calculate band score (simplified calculation)
        if total_questions > 0:
            percentage = (correct_answers / total_questions) * 100
            # Basic IELTS band score calculation (can be enhanced)
            if percentage >= 90:
                band_score = 9.0
            elif percentage >= 80:
                band_score = 8.0
            elif percentage >= 70:
                band_score = 7.0
            elif percentage >= 60:
                band_score = 6.0
            elif percentage >= 50:
                band_score = 5.0
            else:
                band_score = 4.0
        else:
            band_score = 0.0
        
        return {
            'session_id': session_id,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'incorrect_answers': total_questions - correct_answers,
            'percentage': round((correct_answers / total_questions * 100), 2) if total_questions > 0 else 0,
            'band_score': band_score,
            'submitted_at': answers.first().submitted_at if answers.exists() else None,
        }

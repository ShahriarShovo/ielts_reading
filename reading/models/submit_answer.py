# =============================================================================
# SUBMIT ANSWER MODEL
# =============================================================================
# This model serves as a container for student answer submissions.
# It stores metadata about each submission and links to individual StudentAnswer records.
# =============================================================================

from django.db import models
from django.utils import timezone
import uuid

class SubmitAnswer(models.Model):
    """
    SubmitAnswer: Container model for student answer submissions.
    
    This model acts as a "submission record" that groups all student answers
    for a single exam submission. Think of it as a "folder" that contains
    all the individual answer "files".
    
    Relationship:
    - One SubmitAnswer = One complete submission
    - One SubmitAnswer → Many StudentAnswer (one-to-many)
    - SubmitAnswer → ReadingTest (which test was taken)
    """
    
    # =============================================================================
    # CORE FIELDS - Essential submission information
    # =============================================================================
    
    # Primary identifier - unique UUID for each submission
    submit_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this submission"
    )
    
    # Session ID from Academiq (links to exam session)
    session_id = models.CharField(
        max_length=100,
        help_text="Session ID from Academiq exam session"
    )
    
    # Test ID from ReadingTest (which test was taken)
    test_id = models.UUIDField(
        help_text="UUID of the ReadingTest that was taken"
    )
    
    # Student ID (who took the test)
    student_id = models.IntegerField(
        help_text="ID of the student who took the test"
    )
    
    # Organization ID (for multi-tenant support)
    organization_id = models.IntegerField(
        help_text="Organization ID that owns this submission"
    )
    
    # =============================================================================
    # SUBMISSION METADATA - Information about the submission
    # =============================================================================
    
    # Total number of questions answered by student
    # Student can answer 1-40 questions (not necessarily all 40)
    total_questions = models.IntegerField(
        help_text="Number of questions answered by student (1-40)"
    )
    
    # Whether this submission has been processed for scoring
    is_processed = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        help_text="Whether this submission has been processed for scoring"
    )
    
    # =============================================================================
    # TIMESTAMP FIELDS - Track when submission was made
    # =============================================================================
    
    # When this submission was created
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this submission was created"
    )
    
    # When this submission was last modified
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this submission was last modified"
    )
    
    # =============================================================================
    # META CONFIGURATION - Django model settings
    # =============================================================================
    
    class Meta:
        """
        Meta configuration for the SubmitAnswer model.
        """
        db_table = 'submit_answers'  # Custom table name
        ordering = ['-submitted_at']  # Most recent first
        indexes = [
            # Index on session_id for fast lookup
            models.Index(fields=['session_id']),
            # Index on test_id for fast lookup
            models.Index(fields=['test_id']),
            # Index on student_id for fast lookup
            models.Index(fields=['student_id']),
            # Index on organization_id for multi-tenant queries
            models.Index(fields=['organization_id']),
            # Composite index for common queries
            models.Index(fields=['session_id', 'is_processed']),
        ]
        verbose_name = 'Submit Answer'
        verbose_name_plural = 'Submit Answers'
    
    # =============================================================================
    # STRING REPRESENTATION - How the model appears in admin and logs
    # =============================================================================
    
    def __str__(self):
        """
        String representation of the SubmitAnswer.
        
        Format: "SubmitAnswer (Submit ID) - Student ID - Test ID"
        """
        return f"SubmitAnswer ({self.submit_id}) - Student {self.student_id} - Test {self.test_id}"
    
    # =============================================================================
    # HELPER METHODS - Useful methods for working with submissions
    # =============================================================================
    
    def get_student_answers(self):
        """
        Get all StudentAnswer records for this submission.
        
        Returns:
            QuerySet: All StudentAnswer records linked to this submission
        """
        return self.student_answers.select_related('question_type').order_by('question_number')
    
    def get_correct_answers(self):
        """
        Get correct answers for this test.
        
        This method would need to be implemented based on how
        correct answers are stored in the ReadingTest model.
        
        Returns:
            dict: Correct answers organized by question number
        """
        # TODO: Implement based on ReadingTest structure
        # This would fetch correct answers from the test
        pass
    
    def mark_as_processed(self):
        """
        Mark this submission as processed.
        Uses update_fields for faster partial update.
        """
        self.is_processed = True
        self.save(update_fields=['is_processed'])
    
    def get_submission_summary(self):
        """
        Get a summary of this submission.
        
        Returns:
            dict: Summary information about the submission
        """
        student_answers = self.get_student_answers()
        
        return {
            'submit_id': str(self.submit_id),
            'session_id': self.session_id,
            'test_id': str(self.test_id),
            'student_id': self.student_id,
            'total_questions': self.total_questions,
            'submitted_at': self.submitted_at.isoformat(),
            'is_processed': self.is_processed,
            'answer_count': student_answers.count(),
        }
    
    @classmethod
    def get_submissions_by_session(cls, session_id):
        """
        Get all submissions for a specific session.
        
        Args:
            session_id: Session ID to search for
            
        Returns:
            QuerySet: All submissions for the session
        """
        return cls.objects.filter(session_id=session_id)
    
    @classmethod
    def get_submissions_by_student(cls, student_id):
        """
        Get all submissions for a specific student.
        
        Args:
            student_id: Student ID to search for
            
        Returns:
            QuerySet: All submissions for the student
        """
        return cls.objects.filter(student_id=student_id)
    
    @classmethod
    def get_submissions_by_test(cls, test_id):
        """
        Get all submissions for a specific test.
        
        Args:
            test_id: Test ID to search for
            
        Returns:
            QuerySet: All submissions for the test
        """
        return cls.objects.filter(test_id=test_id)

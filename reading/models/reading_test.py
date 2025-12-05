from django.db import models
import uuid

class ReadingTest(models.Model):
    """
    Model representing a complete IELTS Reading test.
    
    This is the top-level model in the 4-level hierarchy: Test -> Passage -> Question Type -> Individual Questions.
    Each reading test contains multiple passages, each passage contains multiple question types,
    and each question type contains multiple individual questions.
    
    Key Features:
    - Unique test identifier for easy reference
    - Organization-based data isolation for multi-tenant support
    - Source tracking for test origin (Cambridge, Custom, etc.)
    - Timestamp tracking for creation and updates
    - Hierarchical relationship with passages
    - UUID-based primary key for security and scalability
    """
    
    # Unique identifier for the test - using UUID for security and scalability
    # This replaces the auto-incrementing ID and provides a more secure identifier
    test_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Human-readable name for the reading test (e.g., "Cambridge IELTS 18 Academic")
    # This is what users will see and identify the test by
    test_name = models.CharField(max_length=255, default='IELTS Academic Reading Test')
    
    # Source of the test (e.g., "Cambridge IELTS 18", "Custom Test", "Official Practice Test")
    # This helps track where the test content came from and maintain proper attribution
    source = models.CharField(max_length=255, default='Custom Test')
    
    # Links this test to a specific organization for data isolation and multi-tenant support
    # Each organization can only access their own tests
    organization_id = models.CharField(max_length=100)
    
    # Timestamp when this test was created - automatically set when object is first saved
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Timestamp when this test was last updated - automatically updated on each save
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta configuration for the ReadingTest model.
        
        - ordering: Most recent tests appear first in queries
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        """
        ordering = ['-created_at']  # Most recent tests first
        db_table = 'reading_test'
        verbose_name = 'Reading Test'
        verbose_name_plural = 'Reading Tests'

    def __str__(self):
        """
        String representation for admin panel, debugging, and logging.
        
        Returns a human-readable string that includes the test name and organization
        for easy identification in admin panels and logs.
        """
        return f"{self.test_name} (Source: {self.source}, Org: {self.organization_id})"
    
    def get_passage_count(self):
        """
        Helper method to get the number of passages in this test.
        
        This is useful for displaying test information and validation.
        Returns the count of related Passage objects.
        """
        return self.passages.count()
    
    def get_total_question_count(self):
        """
        Helper method to get the total number of questions across all passages.
        
        This method counts only questions numbered 1-40 (actual IELTS questions),
        excluding any context or helper questions outside this range.
        
        This is useful for test statistics and validation.
        Returns the count of actual questions (1-40) across all passages in this test.
        """
        all_questions = []
        
        # Loop through all passages
        for passage in self.passages.all():
            # Loop through all question types in this passage
            for question_type in passage.questions.all():
                if not question_type.questions_data:
                    continue
                
                # Extract all questions from questions_data
                for question in question_type.questions_data:
                    # Get question number (could be 'number', 'question_number', or in the question object)
                    question_number = None
                    if isinstance(question, dict):
                        question_number = question.get('number') or question.get('question_number')
                    
                    # Only count questions numbered 1-40 (actual IELTS questions)
                    if question_number is not None:
                        try:
                            q_num = int(question_number)
                            if 1 <= q_num <= 40:
                                all_questions.append(q_num)
                        except (ValueError, TypeError):
                            # If number is not a valid integer, skip
                            pass
        
        # Return unique count (in case of duplicates)
        return len(set(all_questions))
    
    def can_add_passage(self):
        """
        Check if a new passage can be added to this test.
        
        Returns True if the test has fewer than 3 passages.
        """
        return self.get_passage_count() < 3
    
    def can_add_questions(self, additional_questions=1):
        """
        Check if additional questions can be added to this test.
        
        Args:
            additional_questions (int): Number of questions to be added
            
        Returns True if adding the specified number of questions won't exceed 40 total.
        """
        current_total = self.get_total_question_count()
        return (current_total + additional_questions) <= 40
    
    def get_remaining_question_slots(self):
        """
        Get the number of remaining question slots available.
        
        Returns the number of questions that can still be added before reaching the 40 limit.
        """
        current_total = self.get_total_question_count()
        return max(0, 40 - current_total)
    
    def get_remaining_passage_slots(self):
        """
        Get the number of remaining passage slots available.
        
        Returns the number of passages that can still be added before reaching the 3 limit.
        """
        current_count = self.get_passage_count()
        return max(0, 3 - current_count)

from django.db import models
import uuid
from .reading_test import ReadingTest

class Passage(models.Model):
    """
    Model representing a reading passage within a test.
    
    This is the second-level model in the 4-level hierarchy: Test -> Passage -> Question Type -> Individual Questions.
    Each passage belongs to a specific test and contains multiple question types.
    
    Key Features:
    - Unique passage identifier for easy reference
    - Belongs to a specific reading test
    - Contains passage text and metadata
    - Supports paragraph labeling for structured passages
    - UUID-based primary key for security and scalability
    - Automatic order assignment to prevent duplicates
    """
    
    # Unique identifier for the passage - using UUID for security and scalability
    # This replaces the auto-incrementing ID and provides a more secure identifier
    passage_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key relationship to the parent test
    # CASCADE delete means if the test is deleted, all its passages are also deleted
    # This maintains referential integrity in the database
    test = models.ForeignKey(ReadingTest, on_delete=models.CASCADE, related_name='passages')
    
    # Title of the passage (optional)
    # This provides a brief description or title for the passage
    title = models.CharField(max_length=255, blank=True, null=True)
    
    # Subtitle of the passage (optional)
    # This provides additional context or subtitle for the passage
    subtitle = models.CharField(max_length=255, blank=True, null=True, help_text="Optional subtitle for the passage (e.g., 'The Impact on Global Ecosystems')")
    
    # The main text content of the passage
    # This is the actual reading material that students will read
    text = models.TextField()
    
    # Order of this passage within the test
    # This determines the sequence in which passages appear in the test
    # Automatically assigned to prevent duplicates
    order = models.PositiveIntegerField()
    
    # Whether this passage has paragraph labels (A, B, C, etc.)
    # This indicates if the passage is structured with labeled paragraphs
    has_paragraphs = models.BooleanField(default=False)
    
    # Number of paragraphs in the passage
    # This is used for passages with structured paragraphs
    paragraph_count = models.PositiveIntegerField(default=0, blank=True, null=True)
    
    # Labels for paragraphs (e.g., "A-C", "A-D")
    # This specifies the range of paragraph labels used
    paragraph_labels = models.CharField(max_length=50, blank=True, default='')
    
    # Timestamp when this passage was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Timestamp when this passage was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta configuration for the Passage model.
        
        - ordering: Passages are ordered by their sequence number within the test
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        - unique_together: Ensures passage orders are unique within a test
        """
        ordering = ['order']  # Order passages by their sequence number
        db_table = 'reading_passage'
        verbose_name = 'Reading Passage'
        verbose_name_plural = 'Reading Passages'
        unique_together = ['test', 'order']  # Ensure unique passage orders within a test

    def __str__(self):
        """
        String representation for admin panel, debugging, and logging.
        
        Returns a human-readable string that includes the passage title,
        order, and test name for easy identification.
        """
        test_name = self.test.test_name if self.test.test_name else f"Test {self.test.test_id}"
        title = self.title if self.title else f"Passage {self.order}"
        return f"{title} (Order: {self.order}, Test: {test_name})"
    
    def save(self, *args, **kwargs):
        """
        Override save method to automatically assign order if not provided.
        
        This ensures that passages always have a proper order within their test.
        """
        if not self.order:
            # Get the highest order number for this test and add 1
            max_order = Passage.objects.filter(test=self.test).aggregate(
                models.Max('order')
            )['order__max'] or 0
            self.order = max_order + 1
        
        super().save(*args, **kwargs)
    
    def get_question_count(self):
        """
        Get the total number of questions in this passage.
        
        This method calculates the total number of questions across all
        question types in this passage using the new question counting logic.
        
        Returns:
            int: Total number of questions in the passage
        """
        from .question_type import QuestionType
        import logging
        logger = logging.getLogger('reading')
        
        question_types = QuestionType.objects.filter(passage=self)
        total_count = 0
        
        for qt in question_types:
            # Use the new calculate_question_count method
            count = qt.calculate_question_count()
            logger.info(f"  Question Type '{qt.type}': {count} questions (questions_data length: {len(qt.questions_data)})")
            total_count += count
        
        return total_count
    
    def get_question_type_count(self):
        """
        Get the number of question types in this passage.
        
        This method calculates and returns the count of related QuestionType objects.
        It's used for display purposes in the API response.
        
        Returns:
            int: Number of question types in the passage
        """
        from .question_type import QuestionType
        return QuestionType.objects.filter(passage=self).count()
    
    def get_total_question_count(self):
        """
        Get the total number of questions across all question types in this passage.
        
        This method calculates and returns the sum of all questions across all question types.
        It's used for display purposes in the API response.
        
        Returns:
            int: Total number of questions in the passage
        """
        return self.get_question_count()
    
    def get_question_range(self):
        """
        Get the question range for this passage.
        
        This method calculates and returns the start and end question numbers for this passage.
        It's used for display purposes in the API response.
        
        Returns:
            tuple: (start_number, end_number)
        """
        # Get all passages in order up to this one
        previous_passages = Passage.objects.filter(
            test=self.test,
            order__lt=self.order
        ).order_by('order')
        
        # Calculate start number based on previous passages
        start_number = 1
        for prev_passage in previous_passages:
            start_number += prev_passage.get_total_question_count()
        
        # Calculate end number based on this passage's questions
        end_number = start_number + self.get_total_question_count() - 1
        
        return (start_number, end_number)
    
    def get_next_question_number(self):
        """
        Get the next available question number for this passage.
        
        This method calculates the starting question number for the next question type
        to be added to this passage. It's used by the serializer for dynamic numbering.
        
        Returns:
            int: Next available question number
        """
        # Get the global question count across all passages in the test
        # This ensures sequential numbering across the entire test
        test = self.test
        total_questions = 0
        
        # Count questions from all passages up to this one
        for passage in test.passages.all().order_by('order'):
            if passage.order < self.order:
                total_questions += passage.get_question_count()
            elif passage.order == self.order:
                # Add questions from this passage
                total_questions += passage.get_question_count()
                break
        
        return total_questions + 1
    
    def get_question_range_for_type(self, question_type):
        """
        Get the question range for a specific question type within this passage.
        
        This method calculates the start and end question numbers for a specific
        question type based on its position within the passage.
        
        Args:
            question_type: QuestionType instance
            
        Returns:
            tuple: (start_number, end_number)
        """
        # Get all question types in this passage ordered by their sequence
        question_types = self.get_question_types()
        
        # Calculate start number based on previous question types
        start_number = 1
        for qt in question_types:
            if qt.order < question_type.order:
                start_number += qt.calculate_question_count()
            else:
                break
        
        # Calculate end number based on this question type's count
        end_number = start_number + question_type.calculate_question_count() - 1
        
        return (start_number, end_number)
    
    def get_question_types(self):
        """
        Get all question types in this passage ordered by their sequence.
        
        Returns:
            QuerySet: Question types in this passage ordered by order
        """
        from .question_type import QuestionType
        return QuestionType.objects.filter(passage=self).order_by('order')
    
    def can_add_questions(self, additional_questions=1):
        """
        Check if additional questions can be added to this passage.
        
        This checks both the passage-level and test-level limits.
        
        Args:
            additional_questions (int): Number of questions to be added
            
        Returns True if adding the specified number of questions won't exceed limits.
        """
        current_questions = self.get_question_count()
        test_total_questions = self.test.get_total_question_count()
        
        # Check test-level limit (40 questions max)
        if test_total_questions + additional_questions > 40:
            return False
        
        # Check passage-level limit (if any specific limits are set)
        # For now, we'll use a reasonable limit of 20 questions per passage
        if current_questions + additional_questions > 20:
            return False
        
        return True
    
    def get_remaining_question_slots(self):
        """
        Get the number of remaining question slots available for this passage.
        
        Returns the number of questions that can still be added.
        """
        current_questions = self.get_question_count()
        test_total_questions = self.test.get_total_question_count()
        
        # Calculate remaining slots based on test limit (40) and passage limit (20)
        test_remaining = 40 - test_total_questions
        passage_remaining = 20 - current_questions
        
        return min(test_remaining, passage_remaining)
    
    def reorder_question_types(self):
        """
        Reorder question types within this passage to ensure sequential ordering.
        
        This method updates the order of all question types in this passage
        to be sequential (1, 2, 3, ...) and updates their student ranges.
        """
        from .question_type import QuestionType
        question_types = QuestionType.objects.filter(passage=self).order_by('expected_range')
        
        for i, qt in enumerate(question_types, 1):
            qt.order = i
            qt.save()
            qt.update_student_range()
    
    def update_all_student_ranges(self):
        """
        Update student ranges for all question types in this passage.
        
        This method ensures that all question types in this passage have
        correct student ranges based on their current order and position.
        """
        from .question_type import QuestionType
        question_types = QuestionType.objects.filter(passage=self).order_by('order')
        
        for qt in question_types:
            qt.update_student_range()

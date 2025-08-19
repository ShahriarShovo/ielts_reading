from django.db import models
import uuid
from .reading_test import ReadingTest

class Passage(models.Model):
    """
    Model representing a reading passage within an IELTS Reading test.
    
    This is the second-level model in the 4-level hierarchy: Test -> Passage -> Question Type -> Individual Questions.
    Each passage belongs to a specific reading test and contains multiple question types,
    and each question type contains multiple individual questions.
    
    Key Features:
    - Unique passage identifier for easy reference
    - Belongs to a specific reading test
    - Contains the actual reading text for students
    - IELTS-style instruction text for students
    - Ordered sequence within the test
    - Multiple question types per passage
    - UUID-based primary key for security and scalability
    """
    
    # Unique identifier for the passage - using UUID for security and scalability
    # This replaces the auto-incrementing ID and provides a more secure identifier
    passage_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key relationship to the parent reading test
    # CASCADE delete means if the test is deleted, all its passages are also deleted
    # This maintains referential integrity in the database
    test = models.ForeignKey(ReadingTest, on_delete=models.CASCADE, related_name='passages')
    
    # Human-readable title for the passage (optional - can be blank)
    # This helps identify the passage content (e.g., "The History of Coffee")
    title = models.CharField(max_length=255, blank=True, null=True)
    
    # IELTS-style instruction text for students (optional - instructions come from question types)
    # This tells students how much time to spend and which questions to answer
    # Example: "You should spend about 20 minutes on Questions 1-13, which are based on Reading Passage 1 below."
    instruction = models.TextField(blank=True, null=True)
    
    # The actual reading text content that students will read
    # This is the main content that students need to read and understand
    text = models.TextField()
    
    # Order of this passage within the test (1, 2, 3, etc.)
    # This determines the sequence in which passages appear in the test
    order = models.PositiveIntegerField(default=1)

    # Paragraph structure fields for matching question types
    # Indicates whether this passage has paragraph structure (A, B, C, D, E, F, G)
    has_paragraphs = models.BooleanField(default=False, help_text="Whether this passage has paragraph structure for matching questions")
    
    # Number of paragraphs in the passage (e.g., 7 for A-G)
    paragraph_count = models.PositiveIntegerField(null=True, blank=True, help_text="Number of paragraphs (e.g., 7 for A-G)")
    
    # Paragraph labels (e.g., "A-G" or "1-7")
    paragraph_labels = models.CharField(max_length=50, blank=True, help_text="Paragraph labels (e.g., 'A-G' or '1-7')")

    # Organization and timestamps for security and tracking
    organization_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        """
        Meta configuration for the Passage model.
        
        - ordering: Passages are ordered by their sequence number within the test
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        """
        ordering = ['order']  # Order passages by their sequence number
        db_table = 'reading_passage'
        verbose_name = 'Reading Passage'
        verbose_name_plural = 'Reading Passages'

    def __str__(self):
        """
        String representation for admin panel, debugging, and logging.
        
        Returns a human-readable string that includes the passage title (if available),
        order number, and test name for easy identification.
        """
        title_display = self.title if self.title else f"Passage {self.order}"
        return f"{title_display} (Order: {self.order}, Test: {self.test.test_name})"
    
    def get_question_type_count(self):
        """
        Helper method to get the number of question types in this passage.
        
        This is useful for displaying passage information and validation.
        Returns the count of related QuestionType objects.
        """
        return self.questions.count()
    
    def get_total_question_count(self):
        """
        Helper method to get the total number of individual questions across all question types.
        
        This is useful for passage statistics and validation.
        Returns the sum of actual_count from all question types in this passage.
        """
        total_questions = 0
        for question_type in self.questions.all():
            total_questions += question_type.actual_count
        return total_questions
    
    def get_question_range(self):
        """
        Helper method to get the question range for this passage.
        
        This calculates the start and end question numbers for this passage
        based on the order of passages and questions within the test.
        Returns a tuple of (start_number, end_number).
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
    
    def can_add_questions(self, additional_questions=1):
        """
        Check if additional questions can be added to this passage.
        
        This checks both the test-level question limit (40) and ensures
        the passage doesn't exceed reasonable limits.
        
        Args:
            additional_questions (int): Number of questions to be added
            
        Returns True if adding the specified number of questions won't exceed limits.
        """
        # Check if the test can accommodate more questions
        if not self.test.can_add_questions(additional_questions):
            return False
        
        # Additional check: ensure passage doesn't have too many questions
        # A reasonable limit per passage would be 20 questions
        current_passage_questions = self.get_total_question_count()
        return (current_passage_questions + additional_questions) <= 20
    
    def get_remaining_question_slots(self):
        """
        Get the number of remaining question slots available for this passage.
        
        This considers both the test-level limit (40) and passage-level limits.
        Returns the number of questions that can still be added.
        """
        # Get test-level remaining slots
        test_remaining = self.test.get_remaining_question_slots()
        
        # Get passage-level remaining slots (max 20 per passage)
        current_passage_questions = self.get_total_question_count()
        passage_remaining = max(0, 20 - current_passage_questions)
        
        # Return the smaller of the two limits
        return min(test_remaining, passage_remaining)

    def get_paragraph_options(self):
        """
        Get the available paragraph options for matching questions.
        
        This generates the list of paragraph labels (A, B, C, D, E, F, G) 
        based on the paragraph_count and paragraph_labels.
        
        Returns a list of paragraph labels or empty list if no paragraphs.
        """
        if not self.has_paragraphs or not self.paragraph_count:
            return []
        
        # If paragraph_labels is specified, parse it
        if self.paragraph_labels:
            # Handle common formats like "A-G", "1-7", etc.
            if '-' in self.paragraph_labels:
                start, end = self.paragraph_labels.split('-')
                if start.isalpha() and end.isalpha():
                    # Handle alphabetic labels (A-G)
                    start_ord = ord(start.upper())
                    end_ord = ord(end.upper())
                    return [chr(i) for i in range(start_ord, end_ord + 1)]
                elif start.isdigit() and end.isdigit():
                    # Handle numeric labels (1-7)
                    start_num = int(start)
                    end_num = int(end)
                    return [str(i) for i in range(start_num, end_num + 1)]
        
        # Default to alphabetic labels (A, B, C, D, E, F, G)
        return [chr(65 + i) for i in range(self.paragraph_count)]  # 65 is ASCII for 'A'
    
    def get_paragraph_display_text(self):
        """
        Get the display text for paragraph information.
        
        Returns a formatted string showing paragraph information for instructions.
        Example: "Reading passage 2 has seven paragraphs, A-G"
        """
        if not self.has_paragraphs or not self.paragraph_count:
            return ""
        
        passage_number = self.order
        paragraph_count = self.paragraph_count
        
        if self.paragraph_labels:
            return f"Reading passage {passage_number} has {paragraph_count} paragraphs, {self.paragraph_labels}"
        else:
            # Generate default labels
            labels = self.get_paragraph_options()
            if labels:
                return f"Reading passage {passage_number} has {paragraph_count} paragraphs, {labels[0]}-{labels[-1]}"
        
        return f"Reading passage {passage_number} has {paragraph_count} paragraphs"

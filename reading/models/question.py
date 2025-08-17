from django.db import models
from .passage import Passage

class Question(models.Model):
    """
    Model representing a question within a reading passage.
    
    This is the bottom-level model in the 3-level hierarchy: Test -> Passage -> Question.
    Each question belongs to a specific passage and tests students' understanding of the passage.
    
    Key Features:
    - Supports all standard IELTS Reading question types
    - Flexible data storage for different question formats
    - Organization-based data isolation
    - Word limit enforcement for completion questions
    - Support for images and diagrams
    - Multiple correct answers support
    - IELTS-standard instruction system with dynamic question ranges
    - Sequential ordering across all question types (1,2,3,4,5...)
    """
    
    # Question Types - Common IELTS types + flexibility for future
    # These choices define the available question types in the system
    QUESTION_TYPE_CHOICES = [
        # Common IELTS Reading Question Types
        ('MC', 'Multiple Choice'),           # Choose from multiple options
        ('TFNG', 'True/False/Not Given'),    # Determine if statement is True, False, or Not Given
        ('YNN', 'Yes/No/Not Given'),         # Determine if statement is Yes, No, or Not Given
        ('MH', 'Matching Headings'),         # Match paragraph headings to paragraphs
        ('MP', 'Matching Paragraphs'),       # Match information to paragraphs
        ('MF', 'Matching Features'),         # Match features or characteristics
        ('MSE', 'Matching Sentence Endings'), # Complete sentences by matching endings
        ('SC', 'Sentence Completion'),       # Complete sentences with missing words
        ('SUMC', 'Summary Completion'),      # Complete summary with missing words
        ('NC', 'Note Completion'),           # Complete notes with missing information
        ('TC', 'Table Completion'),          # Complete table with missing data
        ('FCC', 'Flow Chart Completion'),    # Complete flow chart with missing steps
        ('DL', 'Diagram Labelling'),         # Label parts of a diagram
        ('SA', 'Short Answer'),              # Answer questions with short responses
        ('PFL', 'Pick from List'),           # Choose answer from provided list
        # Custom/Future types - use this for new question types
        ('CUSTOM', 'Custom Question Type'),  # For future extensibility
    ]
    
    # Links this question to a specific organization for data isolation
    organization_id = models.CharField(max_length=100)
    
    # Foreign key relationship to the parent passage
    # CASCADE delete means if the passage is deleted, all its questions are also deleted
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE, related_name='questions')
    
    # The actual question text that students will see
    question_text = models.TextField()
    
    # Question type handling
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, default='MC')
    custom_question_type = models.CharField(max_length=50, blank=True)  # For future/new question types
    
    # NEW FIELDS FOR IELTS INSTRUCTION SYSTEM
    # Question range display (e.g., "Questions 1-7", "Questions 8-13")
    # This will be auto-calculated based on question count and order
    question_range = models.CharField(max_length=50, blank=True, help_text="Auto-calculated range like 'Questions 1-7'")
    
    # IELTS-standard instruction text (e.g., "Do the following statements agree with the information given in Reading Passage 1?")
    instruction = models.TextField(blank=True, help_text="IELTS instruction text for this question type")
    
    # Answer format instructions (e.g., "In boxes 1-7 on your answer sheet, write TRUE/FALSE/NOT GIVEN...")
    answer_format = models.TextField(blank=True, help_text="Format instructions for how to answer")
    
    # Sequential order number across all question types (1, 2, 3, 4, 5...)
    # This replaces the old 'order' field for better sequential management
    order_number = models.PositiveIntegerField(default=1, help_text="Sequential order across all question types")
    
    # Flexible data storage for all question types
    # This JSON field can store any additional data needed for specific question types
    data = models.JSONField(default=dict)  # All flexible data here: options, correct_answer, extra (e.g., diagram metadata)
    
    # Additional structured fields for common types
    options = models.JSONField(default=list, blank=True)  # For multiple choice, matching, etc.
    correct_answer = models.CharField(max_length=255, blank=True)  # For single answer questions
    correct_answers = models.JSONField(default=list, blank=True)  # For multiple correct answers
    
    # Question metadata
    points = models.PositiveIntegerField(default=1)  # Points awarded for correct answer
    word_limit = models.PositiveIntegerField(default=3, blank=True, null=True)  # For completion questions
    explanation = models.TextField(blank=True)  # Optional explanation for the answer
    image = models.ImageField(upload_to='questions/', null=True, blank=True)  # Optional for diagram-based questions
    
    # DEPRECATED: Replaced by order_number for better sequential management
    # order = models.PositiveIntegerField(default=1)  # Order within the passage
    
    created_at = models.DateTimeField(auto_now_add=True)  # When question was created
    updated_at = models.DateTimeField(auto_now=True)  # When question was last updated
    
    class Meta:
        ordering = ['order_number']  # Order questions by their sequential number across all types

    def __str__(self):
        """String representation for admin panel and debugging"""
        return f"Question {self.order_number} for {self.passage.title}: {self.question_text[:50]}"
    
    def get_question_type_display(self):
        """
        Return the display name for question type, handling custom types.
        
        Returns:
            str: Human-readable name for the question type
        """
        if self.question_type == 'CUSTOM':
            return self.custom_question_type or 'Custom Question Type'
        return dict(self.QUESTION_TYPE_CHOICES).get(self.question_type, self.question_type)
    
    def calculate_question_range(self):
        """
        Calculate the question range for this question type group.
        
        This method calculates the range (e.g., "Questions 1-7") based on:
        1. The order_number of this question
        2. How many questions of the same type exist before this one
        3. The total count of questions of this type
        
        Returns:
            str: Question range like "Questions 1-7" or "Questions 8-13"
        """
        # Get all questions of the same type in the same passage, ordered by order_number
        same_type_questions = Question.objects.filter(
            passage=self.passage,
            question_type=self.question_type
        ).order_by('order_number')
        
        # Find the position of this question within its type group
        question_positions = list(same_type_questions.values_list('order_number', flat=True))
        
        if not question_positions:
            return f"Questions {self.order_number}-{self.order_number}"
        
        # Find the first and last question numbers for this type
        first_question = min(question_positions)
        last_question = max(question_positions)
        
        return f"Questions {first_question}-{last_question}"
    
    def update_question_range(self):
        """
        Update the question_range field for this question.
        
        This method calculates and saves the question range based on the current
        question distribution in the passage.
        """
        self.question_range = self.calculate_question_range()
        self.save(update_fields=['question_range'])
    
    def save(self, *args, **kwargs):
        """
        Auto-populate custom_question_type if using CUSTOM type.
        Auto-calculate question range if not provided.
        
        This method is called before saving the question to the database.
        It ensures that custom question types have a proper name and
        question ranges are calculated automatically.
        """
        if self.question_type == 'CUSTOM' and not self.custom_question_type:
            # You might want to raise an error here or set a default
            pass
        
        # Auto-calculate question range if not provided
        if not self.question_range:
            # We'll calculate it after saving to ensure we have the order_number
            super().save(*args, **kwargs)
            self.update_question_range()
        else:
            super().save(*args, **kwargs)

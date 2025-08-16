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
    order = models.PositiveIntegerField(default=1)  # Order within the passage
    created_at = models.DateTimeField(auto_now_add=True)  # When question was created
    updated_at = models.DateTimeField(auto_now=True)  # When question was last updated
    
    class Meta:
        ordering = ['order']  # Order questions by their sequence number

    def __str__(self):
        """String representation for admin panel and debugging"""
        return f"Question for {self.passage.title}: {self.question_text[:50]}"
    
    def get_question_type_display(self):
        """
        Return the display name for question type, handling custom types.
        
        Returns:
            str: Human-readable name for the question type
        """
        if self.question_type == 'CUSTOM':
            return self.custom_question_type or 'Custom Question Type'
        return dict(self.QUESTION_TYPE_CHOICES).get(self.question_type, self.question_type)
    
    def save(self, *args, **kwargs):
        """
        Auto-populate custom_question_type if using CUSTOM type.
        
        This method is called before saving the question to the database.
        It ensures that custom question types have a proper name.
        """
        if self.question_type == 'CUSTOM' and not self.custom_question_type:
            # You might want to raise an error here or set a default
            pass
        super().save(*args, **kwargs)

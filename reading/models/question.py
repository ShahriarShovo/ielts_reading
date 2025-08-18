from django.db import models
import uuid
from .passage import Passage
from .question_type import QuestionType

class Question(models.Model):
    """
    Model representing an individual question within a question type.
    
    This is the bottom-level model in the 4-level hierarchy: Test -> Passage -> Question Type -> Individual Questions.
    Each individual question belongs to a specific question type and contains the actual question content.
    
    Note: In the new hierarchical structure, individual questions are primarily stored as JSON data
    within the QuestionType model. This model serves as a helper for complex querying and
    individual question management when needed.
    
    Key Features:
    - Unique question identifier for easy reference
    - Belongs to a specific question type
    - Contains individual question content (text, options, answer)
    - Supports all standard IELTS Reading question types
    - UUID-based primary key for security and scalability
    - Flexible data storage for different question formats
    """
    
    # Unique identifier for the individual question - using UUID for security and scalability
    # This replaces the auto-incrementing ID and provides a more secure identifier
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key relationship to the parent question type
    # CASCADE delete means if the question type is deleted, all its individual questions are also deleted
    # This maintains referential integrity in the database
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, related_name='individual_questions')
    
    # The actual question text that students will see
    # This is the specific question content (e.g., "Where was coffee first discovered?")
    question_text = models.TextField()
    
    # Question number within the question type (1, 2, 3, etc.)
    # This determines the order of questions within a specific question type
    number = models.PositiveIntegerField()
    
    # The correct answer for this question
    # This can be a string (e.g., "True", "B", "Ethiopia") or a list for multiple answers
    answer = models.CharField(max_length=255)
    
    # Options for multiple choice questions (stored as JSON)
    # This field is used for MCQ, matching, and other question types that require options
    # Example: ["A. Brazil", "B. Ethiopia", "C. Yemen", "D. India"]
    options = models.JSONField(default=list, blank=True)
    
    # Word limit for completion questions
    # This specifies how many words students can use in their answer
    word_limit = models.PositiveIntegerField(default=1, blank=True, null=True)
    
    # Points awarded for correct answer
    # This allows for different weighting of questions
    points = models.PositiveIntegerField(default=1)
    
    # Optional explanation for the answer
    # This can be used to explain why an answer is correct
    explanation = models.TextField(blank=True)
    
    # Optional image for diagram-based questions
    # This field stores the path to an image file for questions that require visual content
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    
    # Timestamp when this question was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Timestamp when this question was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta configuration for the Question model.
        
        - ordering: Questions are ordered by their number within the question type
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        - unique_together: Ensures question numbers are unique within a question type
        """
        ordering = ['number']  # Order questions by their number within the question type
        db_table = 'reading_question'
        verbose_name = 'Individual Question'
        verbose_name_plural = 'Individual Questions'
        unique_together = ['question_type', 'number']  # Ensure unique question numbers within a type

    def __str__(self):
        """
        String representation for admin panel, debugging, and logging.
        
        Returns a human-readable string that includes the question number,
        question type, and a preview of the question text.
        """
        question_preview = self.question_text[:50] + "..." if len(self.question_text) > 50 else self.question_text
        return f"Question {self.number} ({self.question_type.type}): {question_preview}"
    
    def get_full_question_number(self):
        """
        Get the full question number within the entire test.
        
        This method calculates the absolute question number across all passages
        and question types in the test.
        
        Returns:
            int: The absolute question number in the test
        """
        # Get the question range for this question type
        start_number, _ = self.question_type.get_question_range()
        
        # Calculate the position within this question type
        position_in_type = self.number - 1
        
        # Return the absolute question number
        return start_number + position_in_type
    
    def to_json_format(self):
        """
        Convert this question to the JSON format used in QuestionType.questions_data.
        
        This method creates a dictionary representation that matches the structure
        used in the QuestionType model's JSON field.
        
        Returns:
            dict: Question data in JSON format
        """
        question_data = {
            'number': self.number,
            'text': self.question_text,
            'answer': self.answer
        }
        
        # Add options if they exist
        if self.options:
            question_data['options'] = self.options
        
        # Add word limit if specified
        if self.word_limit:
            question_data['word_limit'] = self.word_limit
        
        # Add points if different from default
        if self.points != 1:
            question_data['points'] = self.points
        
        # Add explanation if provided
        if self.explanation:
            question_data['explanation'] = self.explanation
        
        return question_data
    
    @classmethod
    def from_json_format(cls, question_type, question_data):
        """
        Create a Question instance from JSON format data.
        
        This class method creates a Question object from the JSON data structure
        used in QuestionType.questions_data.
        
        Args:
            question_type (QuestionType): The parent question type
            question_data (dict): Question data in JSON format
            
        Returns:
            Question: New Question instance
        """
        return cls(
            question_type=question_type,
            question_text=question_data.get('text', ''),
            number=question_data.get('number', 1),
            answer=question_data.get('answer', ''),
            options=question_data.get('options', []),
            word_limit=question_data.get('word_limit', 1),
            points=question_data.get('points', 1),
            explanation=question_data.get('explanation', '')
        )
    
    def validate_answer_format(self):
        """
        Validate that the answer format matches the question type requirements.
        
        This method checks if the answer format is appropriate for the question type.
        For example, MCQ questions should have answers that match one of the options.
        
        Returns:
            bool: True if answer format is valid, False otherwise
        """
        question_type = self.question_type.type.lower()
        
        # Validate MCQ answers
        if 'multiple choice' in question_type or 'mcq' in question_type:
            if self.options and self.answer not in [opt.split('. ')[1] if '. ' in opt else opt for opt in self.options]:
                return False
        
        # Validate True/False/Not Given answers
        elif 'true/false' in question_type or 'tfng' in question_type:
            valid_answers = ['true', 'false', 'not given']
            if self.answer.lower() not in valid_answers:
                return False
        
        # Validate Yes/No/Not Given answers
        elif 'yes/no' in question_type or 'ynn' in question_type:
            valid_answers = ['yes', 'no', 'not given']
            if self.answer.lower() not in valid_answers:
                return False
        
        return True

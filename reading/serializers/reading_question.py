from rest_framework import serializers
from reading.models import Question

class ReadingQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Reading Question model.
    
    This serializer handles the conversion between Question model instances
    and JSON data for API communication. It includes comprehensive validation
    to ensure data integrity and proper question configuration.
    
    Key Features:
    - Full CRUD operations support
    - Question type validation
    - Organization-based data isolation
    - Passage relationship validation
    - Flexible data storage for different question types
    - Word limit enforcement for completion questions
    - Cross-field validation for question type requirements
    """
    
    class Meta:
        model = Question
        fields = [
            'id',                    # Primary key
            'organization_id',       # Organization identifier for data isolation
            'passage',               # Foreign key to Passage
            'question_text',         # The actual question text
            'question_type',         # Type of question (MC, TFNG, etc.)
            'custom_question_type',  # For custom question types
            'data',                  # Flexible JSON data storage
            'options',               # Multiple choice options
            'correct_answer',        # Single correct answer
            'correct_answers',       # Multiple correct answers
            'points',                # Points awarded for correct answer
            'word_limit',            # Word limit for completion questions
            'explanation',           # Optional explanation
            'image',                 # Optional image for diagram questions
            'order',                 # Sequence order within passage
            'created_at',            # When question was created
            'updated_at'             # When question was last updated
        ]

    def validate_question_text(self, value):
        """
        Validate question text is not empty and has minimum length.
        
        This ensures that questions have meaningful content that is
        at least 10 characters long for better user experience.
        
        Args:
            value (str): The question text to validate
            
        Returns:
            str: The validated question text
            
        Raises:
            ValidationError: If validation fails
        """
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Question text must be at least 10 characters long")
        return value

    def validate_question_type(self, value):
        """
        Validate question type is valid.
        
        This ensures that only valid question types from the predefined
        choices are used.
        
        Args:
            value (str): The question type to validate
            
        Returns:
            str: The validated question type
            
        Raises:
            ValidationError: If validation fails
        """
        valid_types = [choice[0] for choice in Question.QUESTION_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid question type. Must be one of: {valid_types}")
        return value

    def validate_points(self, value):
        """
        Validate points are positive.
        
        This ensures that questions have valid point values
        (greater than 0) for proper scoring.
        
        Args:
            value (int): The points value to validate
            
        Returns:
            int: The validated points value
            
        Raises:
            ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError("Points must be greater than 0")
        return value

    def validate_word_limit(self, value):
        """
        Validate word limit is reasonable.
        
        This ensures that word limits are within a reasonable range
        (1-50 words) for completion questions.
        
        Args:
            value (int): The word limit value to validate
            
        Returns:
            int: The validated word limit value
            
        Raises:
            ValidationError: If validation fails
        """
        if value and (value < 1 or value > 50):
            raise serializers.ValidationError("Word limit must be between 1 and 50")
        return value

    def validate_organization_id(self, value):
        """
        Validate organization_id is provided.
        
        This ensures that every question is properly associated with
        an organization for data isolation and security.
        
        Args:
            value (str): The organization ID to validate
            
        Returns:
            str: The validated organization ID
            
        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise serializers.ValidationError("Organization ID is required")
        return value

    def validate(self, data):
        """
        Cross-field validation to ensure data integrity.
        
        This method performs additional validation that involves
        multiple fields or question type requirements.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If validation fails
        """
        question_type = data.get('question_type')
        
        # For multiple choice questions, options are required
        if question_type == 'MC' and not data.get('options'):
            raise serializers.ValidationError("Options are required for multiple choice questions")
        
        # For custom question type, custom_question_type is required
        if question_type == 'CUSTOM' and not data.get('custom_question_type'):
            raise serializers.ValidationError("Custom question type name is required when question_type is CUSTOM")
        
        # For completion questions, word_limit is recommended
        completion_types = ['SC', 'SUMC', 'NC', 'TC', 'FCC', 'DL', 'SA']
        if question_type in completion_types and not data.get('word_limit'):
            raise serializers.ValidationError("Word limit is recommended for completion questions")
        
        return data

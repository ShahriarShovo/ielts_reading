from rest_framework import serializers
from reading.models import Question
from django.db import models

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
    - IELTS instruction system with dynamic question ranges
    - Sequential ordering across all question types
    - Template integration support
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
            'question_range',        # NEW: Auto-calculated question range (e.g., "Questions 1-7")
            'instruction',           # NEW: IELTS instruction text
            'answer_format',         # NEW: Answer format instructions
            'order_number',          # NEW: Sequential order across all question types
            'data',                  # Flexible JSON data storage
            'options',               # Multiple choice options
            'correct_answer',        # Single correct answer
            'correct_answers',       # Multiple correct answers
            'points',                # Points awarded for correct answer
            'word_limit',            # Word limit for completion questions
            'explanation',           # Optional explanation
            'image',                 # Optional image for diagram questions
            'created_at',            # When question was created
            'updated_at'             # When question was last updated
        ]
        # Note: 'order' field is deprecated and replaced by 'order_number'

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

    def validate_order_number(self, value):
        """
        Validate order_number is positive.
        
        This ensures that questions have valid sequential order numbers
        (greater than 0) for proper ordering across all question types.
        
        Args:
            value (int): The order number to validate
            
        Returns:
            int: The validated order number
            
        Raises:
            ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError("Order number must be greater than 0")
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

    def create(self, validated_data):
        """
        Create a new question with automatic order_number assignment.
        
        This method ensures that new questions get the next available
        order_number in the passage, maintaining sequential ordering.
        
        Args:
            validated_data (dict): The validated data for creating the question
            
        Returns:
            Question: The created question instance
        """
        # Auto-assign order_number if not provided
        if 'order_number' not in validated_data:
            passage = validated_data.get('passage')
            if passage:
                # Get the highest order_number in this passage and add 1
                max_order = Question.objects.filter(passage=passage).aggregate(
                    max_order=models.Max('order_number')
                )['max_order'] or 0
                validated_data['order_number'] = max_order + 1
        
        # Create the question
        question = super().create(validated_data)
        
        # Auto-calculate question range after creation
        question.update_question_range()
        
        return question

    def update(self, instance, validated_data):
        """
        Update an existing question with automatic range recalculation.
        
        This method ensures that when a question is updated, its
        question_range is recalculated to reflect any changes.
        
        Args:
            instance (Question): The existing question instance
            validated_data (dict): The validated data for updating
            
        Returns:
            Question: The updated question instance
        """
        # Update the question
        question = super().update(instance, validated_data)
        
        # Recalculate question range after update
        question.update_question_range()
        
        return question

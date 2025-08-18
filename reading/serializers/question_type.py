from rest_framework import serializers
from reading.models import QuestionType

class QuestionTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for QuestionType model.
    
    This serializer handles the conversion of QuestionType model instances to and from JSON.
    It includes validation for required fields and proper data formatting.
    
    Key Features:
    - Full CRUD operations (Create, Read, Update, Delete)
    - Field validation and error handling
    - Passage-based data isolation
    - UUID field handling
    - JSON question data handling
    - Dynamic instruction processing
    - Question range calculation
    """
    
    # Custom field to include processed instruction for display purposes
    processed_instruction = serializers.SerializerMethodField()
    
    # Custom field to include question range for display purposes
    question_range = serializers.SerializerMethodField()
    
    # Custom field to include question count for display purposes
    question_count = serializers.SerializerMethodField()
    
    # Custom field to show remaining question slots
    remaining_question_slots = serializers.SerializerMethodField()

    class Meta:
        """
        Meta configuration for the QuestionType serializer.
        
        - model: The Django model this serializer is based on
        - fields: List of fields to include in serialization
        - read_only_fields: Fields that cannot be modified via API
        """
        model = QuestionType
        fields = [
            'question_type_id',      # Unique identifier for the question type
            'passage',               # Foreign key to the parent passage
            'type',                  # Type of question (e.g., "Multiple Choice Questions (MCQ)")
            'instruction_template',  # Instruction template with placeholders
            'expected_range',        # Expected range of questions (e.g., "1-7")
            'actual_count',          # Actual number of questions present
            'questions_data',        # Individual questions data stored as JSON
            'order',                 # Order of this question type within the passage
            'processed_instruction', # Processed instruction with placeholders replaced
            'question_range',        # Calculated question range for this type
            'question_count',        # Number of questions in this type
            'remaining_question_slots' # Remaining question slots available
        ]
        read_only_fields = ['question_type_id', 'processed_instruction', 'question_range', 'question_count', 'remaining_question_slots']

    def get_processed_instruction(self, obj):
        """
        Get the processed instruction with placeholders replaced.
        
        This method calls the model's get_processed_instruction method to replace
        placeholders like {start}, {end}, {passage_number} with actual values.
        
        Args:
            obj (QuestionType): The QuestionType instance
            
        Returns:
            str: Processed instruction text ready for display
        """
        return obj.get_processed_instruction()
    
    def get_question_range(self, obj):
        """
        Get the question range for this question type.
        
        This method calculates and returns the start and end question numbers for this question type.
        It's used for display purposes in the API response.
        
        Args:
            obj (QuestionType): The QuestionType instance
            
        Returns:
            str: Question range like "1-7" or "8-13"
        """
        start_number, end_number = obj.get_question_range()
        return f"{start_number}-{end_number}"
    
    def get_question_count(self, obj):
        """
        Get the number of questions in this question type.
        
        This method returns the actual count of questions in this question type.
        It's used for display purposes in the API response.
        
        Args:
            obj (QuestionType): The QuestionType instance
            
        Returns:
            int: Number of questions in this type
        """
        return obj.actual_count

    def get_remaining_question_slots(self, obj):
        """
        Get the remaining question slots for this question type.
        
        This method calculates and returns the number of remaining slots available for this question type.
        It's used for display purposes in the API response.
        
        Args:
            obj (QuestionType): The QuestionType instance
            
        Returns:
            int: Number of remaining slots
        """
        return obj.get_remaining_question_slots()

    def validate_type(self, value):
        """
        Validate the type field.
        
        This method ensures that the question type is not empty and has a reasonable length.
        It also checks for any invalid characters or formatting.
        
        Args:
            value (str): The type value to validate
            
        Returns:
            str: The validated type
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if type is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Question type cannot be empty.")
        
        # Check if type is not too long
        if len(value) > 100:
            raise serializers.ValidationError("Question type cannot exceed 100 characters.")
        
        return value.strip()
    
    def validate_instruction_template(self, value):
        """
        Validate the instruction_template field.
        
        This method ensures that the instruction template is not empty and has a reasonable length.
        It also checks for required placeholders.
        
        Args:
            value (str): The instruction_template value to validate
            
        Returns:
            str: The validated instruction_template
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if instruction_template is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Instruction template cannot be empty.")
        
        # Check if instruction_template is not too long
        if len(value) > 2000:
            raise serializers.ValidationError("Instruction template cannot exceed 2000 characters.")
        
        # Check for required placeholders
        if '{start}' not in value or '{end}' not in value:
            raise serializers.ValidationError("Instruction template must contain {start} and {end} placeholders.")
        
        return value.strip()
    
    def validate_expected_range(self, value):
        """
        Validate the expected_range field.
        
        This method ensures that the expected range is in the correct format (e.g., "1-7").
        
        Args:
            value (str): The expected_range value to validate
            
        Returns:
            str: The validated expected_range
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if expected_range is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Expected range cannot be empty.")
        
        # Check if expected_range is not too long
        if len(value) > 20:
            raise serializers.ValidationError("Expected range cannot exceed 20 characters.")
        
        # Check format (should be like "1-7" or "14-20")
        if '-' not in value:
            raise serializers.ValidationError("Expected range must be in format 'start-end' (e.g., '1-7').")
        
        try:
            start, end = value.split('-')
            start_num = int(start.strip())
            end_num = int(end.strip())
            
            if start_num <= 0 or end_num <= 0:
                raise serializers.ValidationError("Range numbers must be positive integers.")
            
            if start_num >= end_num:
                raise serializers.ValidationError("Start number must be less than end number.")
                
        except ValueError:
            raise serializers.ValidationError("Expected range must contain valid numbers.")
        
        return value.strip()
    
    def validate_actual_count(self, value):
        """
        Validate the actual_count field.
        
        This method ensures that the actual count is a positive integer.
        
        Args:
            value (int): The actual_count value to validate
            
        Returns:
            int: The validated actual_count
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if actual_count is positive
        if value < 0:
            raise serializers.ValidationError("Actual count cannot be negative.")
        
        return value
    
    def validate_questions_data(self, value):
        """
        Validate the questions_data field.
        
        This method ensures that the questions_data is a valid list of question objects.
        It checks the structure and content of each question.
        It also validates that adding these questions won't exceed the test limit (40 questions).
        
        Args:
            value (list): The questions_data value to validate
            
        Returns:
            list: The validated questions_data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if questions_data is a list
        if not isinstance(value, list):
            raise serializers.ValidationError("Questions data must be a list.")
        
        # Get the passage from the context to check limits
        passage = self.context.get('passage')
        if passage:
            # Check if adding these questions would exceed the test limit
            current_test_questions = passage.test.get_total_question_count()
            # Calculate existing questions in this question type (if updating)
            existing_questions = 0
            if self.instance:
                existing_questions = self.instance.actual_count
            
            # Calculate new total if we add these questions
            new_questions = len(value)
            total_after_addition = current_test_questions - existing_questions + new_questions
            
            if total_after_addition > 40:
                raise serializers.ValidationError(
                    f"Cannot add {new_questions} questions. This would result in {total_after_addition} total questions. "
                    f"Maximum allowed is 40 questions per test. "
                    f"Current test has {current_test_questions} questions."
                )
        
        # Validate each question in the list
        for i, question in enumerate(value):
            if not isinstance(question, dict):
                raise serializers.ValidationError(f"Question {i+1} must be an object.")
            
            # Check required fields
            if 'number' not in question:
                raise serializers.ValidationError(f"Question {i+1} must have a 'number' field.")
            
            if 'text' not in question:
                raise serializers.ValidationError(f"Question {i+1} must have a 'text' field.")
            
            if 'answer' not in question:
                raise serializers.ValidationError(f"Question {i+1} must have an 'answer' field.")
            
            # Validate question number
            if not isinstance(question['number'], int) or question['number'] <= 0:
                raise serializers.ValidationError(f"Question {i+1} number must be a positive integer.")
            
            # Validate question text
            if not question['text'] or not question['text'].strip():
                raise serializers.ValidationError(f"Question {i+1} text cannot be empty.")
            
            # Validate answer
            if not question['answer'] or not str(question['answer']).strip():
                raise serializers.ValidationError(f"Question {i+1} answer cannot be empty.")
            
            # Validate options if present
            if 'options' in question:
                if not isinstance(question['options'], list):
                    raise serializers.ValidationError(f"Question {i+1} options must be a list.")
                
                for j, option in enumerate(question['options']):
                    if not option or not str(option).strip():
                        raise serializers.ValidationError(f"Question {i+1} option {j+1} cannot be empty.")
        
        return value
    
    def validate_order(self, value):
        """
        Validate the order field.
        
        This method ensures that the order is a positive integer.
        
        Args:
            value (int): The order value to validate
            
        Returns:
            int: The validated order
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if order is positive
        if value <= 0:
            raise serializers.ValidationError("Order must be a positive integer.")
        
        return value
    
    def validate_passage(self, value):
        """
        Validate the passage field.
        
        This method ensures that the passage exists and is valid.
        It also checks if the passage can accommodate more questions (max 40 per test).
        
        Args:
            value (Passage): The passage value to validate
            
        Returns:
            Passage: The validated passage
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if passage exists
        if not value:
            raise serializers.ValidationError("Passage is required.")
        
        # Check if passage can accommodate more questions
        if not value.can_add_questions():
            current_total = value.test.get_total_question_count()
            raise serializers.ValidationError(
                f"Cannot add more questions. Test already has {current_total} questions. "
                f"Maximum allowed is 40 questions per test."
            )
        
        return value
    
    def create(self, validated_data):
        """
        Create a new QuestionType instance.
        
        This method creates a new QuestionType object with the validated data.
        It ensures that all required fields are properly set and updates the actual_count.
        
        Args:
            validated_data (dict): The validated data for creating the question type
            
        Returns:
            QuestionType: The newly created QuestionType instance
        """
        # Update actual_count based on questions_data length
        questions_data = validated_data.get('questions_data', [])
        validated_data['actual_count'] = len(questions_data)
        
        # Create the QuestionType instance with validated data
        question_type = QuestionType.objects.create(**validated_data)
        return question_type
    
    def update(self, instance, validated_data):
        """
        Update an existing QuestionType instance.
        
        This method updates an existing QuestionType object with the validated data.
        It ensures that all fields are properly updated and updates the actual_count.
        
        Args:
            instance (QuestionType): The existing QuestionType instance to update
            validated_data (dict): The validated data for updating the question type
            
        Returns:
            QuestionType: The updated QuestionType instance
        """
        # Update actual_count based on questions_data length if questions_data is being updated
        if 'questions_data' in validated_data:
            validated_data['actual_count'] = len(validated_data['questions_data'])
        
        # Update the QuestionType instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the updated instance
        instance.save()
        return instance

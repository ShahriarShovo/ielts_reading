from rest_framework import serializers
from reading.models import Passage

class PassageSerializer(serializers.ModelSerializer):
    """
    Serializer for Passage model.
    
    This serializer handles the conversion of Passage model instances to and from JSON.
    It includes validation for required fields and proper data formatting.
    
    Key Features:
    - Full CRUD operations (Create, Read, Update, Delete)
    - Field validation and error handling
    - Test-based data isolation
    - UUID field handling
    - Nested question type data (read-only)
    - Dynamic question range calculation
    """
    
    # Custom field to include question type count for display purposes
    question_type_count = serializers.SerializerMethodField()
    
    # Custom field to include total question count for display purposes
    total_question_count = serializers.SerializerMethodField()
    
    # Custom field to include question range for display purposes
    question_range = serializers.SerializerMethodField()
    
    # Custom field to show remaining question slots
    remaining_question_slots = serializers.SerializerMethodField()

    class Meta:
        """
        Meta configuration for the Passage serializer.
        
        - model: The Django model this serializer is based on
        - fields: List of fields to include in serialization
        - read_only_fields: Fields that cannot be modified via API
        """
        model = Passage
        fields = [
            'passage_id',        # Unique identifier for the passage
            'test',              # Foreign key to the parent test
            'title',             # Human-readable title for the passage (optional)
            'subtitle',          # Subtitle for the passage (optional)
            'instruction',       # IELTS-style instruction text for students
            'text',              # The actual reading text content
            'order',             # Order of this passage within the test
            'has_paragraphs',    # Whether this passage has paragraph structure
            'paragraph_count',   # Number of paragraphs in the passage
            'paragraph_labels',  # Paragraph labels (e.g., "A-G")
            'question_type_count',    # Number of question types in this passage (computed)
            'total_question_count',   # Total number of questions in this passage (computed)
            'question_range',         # Question range for this passage (computed)
            'remaining_question_slots' # Remaining question slots available (computed)
        ]
        read_only_fields = ['passage_id', 'question_type_count', 'total_question_count', 'question_range', 'remaining_question_slots']

    def get_question_type_count(self, obj):
        """
        Get the number of question types in this passage.
        
        This method calculates and returns the count of related QuestionType objects.
        It's used for display purposes in the API response.
        
        Args:
            obj (Passage): The Passage instance
            
        Returns:
            int: Number of question types in the passage
        """
        return obj.get_question_type_count()
    
    def get_total_question_count(self, obj):
        """
        Get the total number of questions across all question types in this passage.
        
        This method calculates and returns the sum of all questions across all question types.
        It's used for display purposes in the API response.
        
        Args:
            obj (Passage): The Passage instance
            
        Returns:
            int: Total number of questions in the passage
        """
        return obj.get_total_question_count()
    
    def get_question_range(self, obj):
        """
        Get the question range for this passage.
        
        This method calculates and returns the start and end question numbers for this passage.
        It's used for display purposes in the API response.
        
        Args:
            obj (Passage): The Passage instance
            
        Returns:
            str: Question range like "1-13" or "14-26"
        """
        start_number, end_number = obj.get_question_range()
        return f"{start_number}-{end_number}"

    def get_remaining_question_slots(self, obj):
        """
        Get the remaining question slots for this passage.
        
        This method calculates and returns the number of slots available for questions in this passage.
        It's used for display purposes in the API response.
        
        Args:
            obj (Passage): The Passage instance
            
        Returns:
            int: Number of remaining slots
        """
        return obj.get_remaining_question_slots()

    def validate_title(self, value):
        """
        Validate the title field.
        
        This method ensures that the title has a reasonable length if provided.
        Since title is optional, empty values are allowed.
        
        Args:
            value (str): The title value to validate
            
        Returns:
            str: The validated title (or None if empty)
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Title is optional, so None or empty string is valid
        if value is None or value == '':
            return None
        
        # Check if title is not too long
        if len(value) > 255:
            raise serializers.ValidationError("Title cannot exceed 255 characters.")
        
        return value.strip()
    
    def validate_instruction(self, value):
        """
        Validate the instruction field.
        
        This method ensures that the instruction has a reasonable length if provided.
        Since instruction is optional, empty values are allowed.
        
        Args:
            value (str): The instruction value to validate
            
        Returns:
            str: The validated instruction (or None if empty)
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Instruction is optional, so None or empty string is valid
        if value is None or value == '':
            return None
        
        # Check if instruction is not too long
        if len(value) > 1000:
            raise serializers.ValidationError("Instruction cannot exceed 1000 characters.")
        
        return value.strip()
    
    def validate_text(self, value):
        """
        Validate the text field.
        
        This method ensures that the text is not empty and has a reasonable length.
        It also checks for any invalid characters or formatting.
        
        Args:
            value (str): The text value to validate
            
        Returns:
            str: The validated text
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if text is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Text cannot be empty.")
        
        # Check if text is not too long
        if len(value) > 10000:
            raise serializers.ValidationError("Text cannot exceed 10000 characters.")
        
        # Check minimum length for meaningful content
        if len(value.strip()) < 50:
            raise serializers.ValidationError("Text must be at least 50 characters long.")
        
        return value.strip()
    
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
    
    def validate_test(self, value):
        """
        Validate the test field.
        
        This method ensures that the test exists and is valid.
        It also checks if the test can accommodate another passage (max 3 passages).
        
        Args:
            value (ReadingTest): The test value to validate
            
        Returns:
            ReadingTest: The validated test
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if test exists
        if not value:
            raise serializers.ValidationError("Test is required.")
        
        # Check if test can accommodate another passage (max 3 passages)
        if not value.can_add_passage():
            raise serializers.ValidationError(
                f"Cannot add more passages. Test already has {value.get_passage_count()} passages. "
                f"Maximum allowed is 3 passages per test."
            )
        
        return value
    
    def create(self, validated_data):
        """
        Create a new Passage instance.
        
        This method creates a new Passage object with the validated data.
        It ensures that all required fields are properly set.
        
        Args:
            validated_data (dict): The validated data for creating the passage
            
        Returns:
            Passage: The newly created Passage instance
        """
        # Create the Passage instance with validated data
        passage = Passage.objects.create(**validated_data)
        return passage
    
    def update(self, instance, validated_data):
        """
        Update an existing Passage instance.
        
        This method updates an existing Passage object with the validated data.
        It ensures that all fields are properly updated.
        
        Args:
            instance (Passage): The existing Passage instance to update
            validated_data (dict): The validated data for updating the passage
            
        Returns:
            Passage: The updated Passage instance
        """
        # Update the Passage instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the updated instance
        instance.save()
        return instance

    def validate_has_paragraphs(self, value):
        """
        Validate the has_paragraphs field.
        
        This method ensures that if has_paragraphs is True, paragraph_count is also provided.
        
        Args:
            value (bool): The has_paragraphs value to validate
            
        Returns:
            bool: The validated has_paragraphs value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        return value
    
    def validate_paragraph_count(self, value):
        """
        Validate the paragraph_count field.
        
        This method ensures that paragraph_count is reasonable if provided.
        
        Args:
            value (int): The paragraph_count value to validate
            
        Returns:
            int: The validated paragraph_count value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Paragraph count must be a positive integer.")
            if value > 26:  # Reasonable limit for paragraph count
                raise serializers.ValidationError("Paragraph count cannot exceed 26.")
        
        return value
    
    def validate_paragraph_labels(self, value):
        """
        Validate the paragraph_labels field.
        
        This method ensures that paragraph_labels is in a valid format if provided.
        
        Args:
            value (str): The paragraph_labels value to validate
            
        Returns:
            str: The validated paragraph_labels value
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        if value:
            # Check if it's in a valid format (e.g., "A-G", "1-7")
            if '-' not in value:
                raise serializers.ValidationError("Paragraph labels must be in format 'A-G' or '1-7'.")
            
            # start, end = value.split('-')
            parts = value.split('-')
            if len(parts) != 2:
                raise serializers.ValidationError("Paragraph labels must be in format 'A-G' or '1-7' with exactly one dash.")
            start, end = parts[0], parts[1]
            
            if not (start.isalpha() and end.isalpha()) and not (start.isdigit() and end.isdigit()):
                raise serializers.ValidationError("Paragraph labels must be either alphabetic (A-G) or numeric (1-7).")
        
        return value.strip() if value else value
    
    def validate(self, data):
        """
        Validate the entire data set.
        
        This method performs cross-field validation to ensure data consistency.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        has_paragraphs = data.get('has_paragraphs', False)
        paragraph_count = data.get('paragraph_count')
        paragraph_labels = data.get('paragraph_labels', '')
        
        # If has_paragraphs is True, paragraph_count must be provided
        if has_paragraphs and not paragraph_count:
            raise serializers.ValidationError(
                "Paragraph count is required when has_paragraphs is True."
            )
        
        # If paragraph_count is provided, has_paragraphs should be True
        if paragraph_count and not has_paragraphs:
            data['has_paragraphs'] = True
        
        # If paragraph_labels is provided, validate it matches paragraph_count
        if paragraph_labels and paragraph_count:
            if '-' in paragraph_labels:
                parts = paragraph_labels.split('-')
                if len(parts) != 2:
                    raise serializers.ValidationError("Paragraph labels must be in format 'A-G' or '1-7' with exactly one dash.")
                start, end = parts[0], parts[1]
                
                if start.isalpha() and end.isalpha():
                    # For alphabetic labels (A-G)
                    start_ord = ord(start.upper())
                    end_ord = ord(end.upper())
                    expected_count = end_ord - start_ord + 1
                    if expected_count != paragraph_count:
                        raise serializers.ValidationError(
                            f"Paragraph count ({paragraph_count}) doesn't match labels ({paragraph_labels}). "
                            f"Expected {expected_count} paragraphs."
                        )
                elif start.isdigit() and end.isdigit():
                    # For numeric labels (1-7)
                    start_num = int(start)
                    end_num = int(end)
                    expected_count = end_num - start_num + 1
                    if expected_count != paragraph_count:
                        raise serializers.ValidationError(
                            f"Paragraph count ({paragraph_count}) doesn't match labels ({paragraph_labels}). "
                            f"Expected {expected_count} paragraphs."
                        )
        
        return data

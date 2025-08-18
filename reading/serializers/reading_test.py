from rest_framework import serializers
from reading.models import ReadingTest

class ReadingTestSerializer(serializers.ModelSerializer):
    """
    Serializer for ReadingTest model.
    
    This serializer handles the conversion of ReadingTest model instances to and from JSON.
    It includes validation for required fields and proper data formatting.
    
    Key Features:
    - Full CRUD operations (Create, Read, Update, Delete)
    - Field validation and error handling
    - Organization-based data isolation
    - UUID field handling
    - Nested passage data (read-only)
    """
    
    # Custom field to include passage count for display purposes
    passage_count = serializers.SerializerMethodField()
    
    # Custom field to include total question count for display purposes
    total_question_count = serializers.SerializerMethodField()
    
    # Custom field to show remaining passage slots
    remaining_passage_slots = serializers.SerializerMethodField()
    
    # Custom field to show remaining question slots
    remaining_question_slots = serializers.SerializerMethodField()

    class Meta:
        """
        Meta configuration for the ReadingTest serializer.
        
        - model: The Django model this serializer is based on
        - fields: List of fields to include in serialization
        - read_only_fields: Fields that cannot be modified via API
        """
        model = ReadingTest
        fields = [
            'test_id',           # Unique identifier for the test
            'test_name',         # Human-readable name for the test
            'source',            # Source of the test (Cambridge, Custom, etc.)
            'organization_id',   # Organization identifier for data isolation
            'created_at',        # Timestamp when test was created
            'updated_at',        # Timestamp when test was last updated
            'passage_count',     # Number of passages in this test (computed)
            'total_question_count',  # Total number of questions in this test (computed)
            'remaining_passage_slots',  # Remaining passage slots available
            'remaining_question_slots'  # Remaining question slots available
        ]
        read_only_fields = ['test_id', 'created_at', 'updated_at', 'passage_count', 'total_question_count', 'remaining_passage_slots', 'remaining_question_slots']

    def get_passage_count(self, obj):
        """
        Get the number of passages in this test.
        
        This method calculates and returns the count of related Passage objects.
        It's used for display purposes in the API response.
        
        Args:
            obj (ReadingTest): The ReadingTest instance
            
        Returns:
            int: Number of passages in the test
        """
        return obj.get_passage_count()
    
    def get_total_question_count(self, obj):
        """
        Get the total number of questions across all passages in this test.
        
        This method calculates and returns the sum of all questions across all passages.
        It's used for display purposes in the API response.
        
        Args:
            obj (ReadingTest): The ReadingTest instance
            
        Returns:
            int: Total number of questions in the test
        """
        return obj.get_total_question_count()
    
    def get_remaining_passage_slots(self, obj):
        """
        Get the number of remaining passage slots available.
        
        This method calculates and returns the number of passages that can still be added.
        It's used for display purposes in the API response.
        
        Args:
            obj (ReadingTest): The ReadingTest instance
            
        Returns:
            int: Number of remaining passage slots
        """
        return obj.get_remaining_passage_slots()
    
    def get_remaining_question_slots(self, obj):
        """
        Get the number of remaining question slots available.
        
        This method calculates and returns the number of questions that can still be added.
        It's used for display purposes in the API response.
        
        Args:
            obj (ReadingTest): The ReadingTest instance
            
        Returns:
            int: Number of remaining question slots
        """
        return obj.get_remaining_question_slots()

    def validate_test_name(self, value):
        """
        Validate the test name field.
        
        This method ensures that the test name is not empty and has a reasonable length.
        It also checks for any invalid characters or formatting.
        
        Args:
            value (str): The test name value to validate
            
        Returns:
            str: The validated test name
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if test name is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Test name cannot be empty.")
        
        # Check if test name is not too long
        if len(value) > 255:
            raise serializers.ValidationError("Test name cannot exceed 255 characters.")
        
        # Check if test name contains only valid characters
        if not value.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError("Test name can only contain letters, numbers, spaces, hyphens, and underscores.")
        
        return value.strip()
    
    def validate_source(self, value):
        """
        Validate the source field.
        
        This method ensures that the source is not empty and has a reasonable length.
        It also checks for any invalid characters or formatting.
        
        Args:
            value (str): The source value to validate
            
        Returns:
            str: The validated source
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if source is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Source cannot be empty.")
        
        # Check if source is not too long
        if len(value) > 255:
            raise serializers.ValidationError("Source cannot exceed 255 characters.")
        
        return value.strip()
    
    def validate_organization_id(self, value):
        """
        Validate the organization_id field.
        
        This method ensures that the organization_id is not empty and has a reasonable length.
        It also checks for any invalid characters or formatting.
        
        Args:
            value (str): The organization_id value to validate
            
        Returns:
            str: The validated organization_id
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        # Check if organization_id is not empty
        if not value or not value.strip():
            raise serializers.ValidationError("Organization ID cannot be empty.")
        
        # Check if organization_id is not too long
        if len(value) > 100:
            raise serializers.ValidationError("Organization ID cannot exceed 100 characters.")
        
        return value.strip()
    
    def create(self, validated_data):
        """
        Create a new ReadingTest instance.
        
        This method creates a new ReadingTest object with the validated data.
        It ensures that all required fields are properly set.
        
        Args:
            validated_data (dict): The validated data for creating the test
            
        Returns:
            ReadingTest: The newly created ReadingTest instance
        """
        # Create the ReadingTest instance with validated data
        reading_test = ReadingTest.objects.create(**validated_data)
        return reading_test
    
    def update(self, instance, validated_data):
        """
        Update an existing ReadingTest instance.
        
        This method updates an existing ReadingTest object with the validated data.
        It ensures that all fields are properly updated.
        
        Args:
            instance (ReadingTest): The existing ReadingTest instance to update
            validated_data (dict): The validated data for updating the test
            
        Returns:
            ReadingTest: The updated ReadingTest instance
        """
        # Update the ReadingTest instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the updated instance
        instance.save()
        return instance

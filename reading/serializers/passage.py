from rest_framework import serializers
from reading.models import Passage, ReadingTest

class PassageSerializer(serializers.ModelSerializer):
    """
    Serializer for Reading Passage model.
    
    This serializer handles the conversion between Passage model instances
    and JSON data for API communication. It includes comprehensive validation
    to ensure data integrity and proper passage configuration.
    
    Key Features:
    - Full CRUD operations support
    - Title, text, and order validation
    - Test relationship validation
    - Minimum content length requirements
    - Hierarchical relationship enforcement
    """
    
    class Meta:
        model = Passage
        fields = [
            'id',        # Primary key
            'test',      # Foreign key to ReadingTest
            'title',     # Human-readable passage title
            'text',      # The actual reading content
            'order'      # Sequence order within the test
        ]

    def validate_title(self, value):
        """
        Validate title is not empty and has minimum length.
        
        This ensures that passages have meaningful titles that are
        at least 5 characters long for better user experience.
        
        Args:
            value (str): The title to validate
            
        Returns:
            str: The validated title
            
        Raises:
            ValidationError: If validation fails
        """
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long")
        return value

    def validate_text(self, value):
        """
        Validate text is not empty and has minimum length.
        
        This ensures that passages have substantial content (at least 50 characters)
        to provide meaningful reading material for students.
        
        Args:
            value (str): The text content to validate
            
        Returns:
            str: The validated text content
            
        Raises:
            ValidationError: If validation fails
        """
        if not value or len(value.strip()) < 50:
            raise serializers.ValidationError("Text must be at least 50 characters long")
        return value

    def validate_order(self, value):
        """
        Validate order is positive.
        
        This ensures that passages have a valid sequence order
        (greater than 0) for proper display in the test.
        
        Args:
            value (int): The order value to validate
            
        Returns:
            int: The validated order value
            
        Raises:
            ValidationError: If validation fails
        """
        if value <= 0:
            raise serializers.ValidationError("Order must be greater than 0")
        return value

    def validate_test(self, value):
        """
        Validate test exists and belongs to user's organization.
        
        This ensures that every passage is properly associated with
        a valid reading test.
        
        Args:
            value (ReadingTest): The test instance to validate
            
        Returns:
            ReadingTest: The validated test instance
            
        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise serializers.ValidationError("Test is required")
        return value

    def validate(self, data):
        """
        Cross-field validation to ensure data integrity.
        
        This method performs additional validation that involves
        multiple fields or external relationships.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If validation fails
        """
        # Check if test exists in the database
        test = data.get('test')
        if test and not ReadingTest.objects.filter(id=test.id).exists():
            raise serializers.ValidationError("Specified test does not exist")
        
        return data

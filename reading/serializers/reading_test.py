from rest_framework import serializers
from reading.models import ReadingTest

class ReadingTestSerializer(serializers.ModelSerializer):
    """
    Serializer for Reading Test model.
    
    This serializer handles the conversion between ReadingTest model instances
    and JSON data for API communication. It includes validation to ensure
    data integrity and proper test configuration.
    
    Key Features:
    - Full CRUD operations support
    - Title and organization_id validation
    - Automatic timestamp handling
    - Organization-based data isolation
    """
    
    class Meta:
        model = ReadingTest
        fields = [
            'id',                # Primary key
            'organization_id',   # Organization identifier for data isolation
            'title',             # Human-readable test title
            'created_at',        # When test was created
            'updated_at'         # When test was last updated
        ]

    def validate_title(self, value):
        """
        Validate title is not empty and has minimum length.
        
        This ensures that reading tests have meaningful titles that are
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

    def validate_organization_id(self, value):
        """
        Validate organization_id is provided.
        
        This ensures that every reading test is properly associated with
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

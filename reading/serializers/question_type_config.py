from rest_framework import serializers
from reading.models import QuestionTypeConfig

class QuestionTypeConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for QuestionTypeConfig model.
    
    This serializer handles the conversion between QuestionTypeConfig model instances
    and JSON data for API communication. It includes comprehensive validation to ensure
    data integrity and proper configuration of question types.
    
    Key Features:
    - Full CRUD operations support
    - Comprehensive field validation
    - Unique type_code enforcement
    - Cross-field validation for requirements
    - Automatic type_code normalization (uppercase)
    """
    
    class Meta:
        model = QuestionTypeConfig
        fields = [
            'id',                    # Primary key
            'type_code',             # Unique identifier (e.g., 'MC', 'TFNG')
            'display_name',          # Human-readable name
            'description',           # Detailed description
            'is_active',             # Whether this type is available
            'requires_options',      # Whether this type needs options
            'requires_multiple_answers', # Whether this type supports multiple answers
            'requires_word_limit',   # Whether this type needs word limit
            'requires_image',        # Whether this type needs images
            'created_at'             # When this config was created
        ]

    def validate_type_code(self, value):
        """
        Validate type_code is unique and follows naming convention.
        
        This method ensures that:
        - Type code is at least 2 characters long
        - Type code is unique across all configurations
        - Type code is converted to uppercase for consistency
        
        Args:
            value (str): The type code to validate
            
        Returns:
            str: The validated and normalized type code
            
        Raises:
            ValidationError: If validation fails
        """
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Type code must be at least 2 characters long")
        
        # Check if type_code already exists (for updates, exclude current instance)
        instance = getattr(self, 'instance', None)
        if QuestionTypeConfig.objects.filter(type_code=value).exclude(id=instance.id if instance else None).exists():
            raise serializers.ValidationError("Type code already exists")
        
        return value.upper()  # Normalize to uppercase

    def validate_display_name(self, value):
        """
        Validate display_name is not empty and has minimum length.
        
        Args:
            value (str): The display name to validate
            
        Returns:
            str: The validated display name
            
        Raises:
            ValidationError: If validation fails
        """
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Display name must be at least 3 characters long")
        return value

    def validate(self, data):
        """
        Cross-field validation to ensure proper configuration.
        
        This method ensures that at least one requirement flag is set,
        preventing creation of question types with no defined behavior.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If validation fails
        """
        # Ensure at least one requirement is set
        requires_options = data.get('requires_options', False)
        requires_multiple_answers = data.get('requires_multiple_answers', False)
        requires_word_limit = data.get('requires_word_limit', False)
        requires_image = data.get('requires_image', False)
        
        if not any([requires_options, requires_multiple_answers, requires_word_limit, requires_image]):
            raise serializers.ValidationError("At least one requirement must be set")
        
        return data

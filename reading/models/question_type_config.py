from django.db import models

class QuestionTypeConfig(models.Model):
    """
    Configuration model for question types - makes it easy to add new types dynamically.
    
    This model stores the configuration for different question types used in IELTS Reading tests.
    Instead of hardcoding question types in the Question model, this allows for dynamic
    management of question types through the admin panel or API.
    
    Key Features:
    - Dynamic question type management
    - Configuration-driven approach
    - Easy to add new question types without code changes
    - Support for enabling/disabling question types
    """
    
    # Unique identifier for the question type (e.g., 'MC', 'TFNG', 'SA')
    type_code = models.CharField(max_length=10, unique=True)
    
    # Human-readable name for the question type (e.g., 'Multiple Choice', 'True/False/Not Given')
    display_name = models.CharField(max_length=100)
    
    # Detailed description of what this question type does
    description = models.TextField(blank=True)
    
    # Whether this question type is currently active/available for use
    is_active = models.BooleanField(default=True)
    
    # Configuration flags that determine what fields are required for this question type
    requires_options = models.BooleanField(default=False)  # For MC, MH, MF, MSE, PFL
    requires_multiple_answers = models.BooleanField(default=False)  # For questions with multiple correct answers
    requires_word_limit = models.BooleanField(default=False)  # For SA, SC, SUMC, NC, TC, FCC, DL, MSE
    requires_image = models.BooleanField(default=False)  # For DL (Diagram Labelling)
    
    # Timestamp when this configuration was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_name']  # Order by display name for easy browsing
    
    def __str__(self):
        """String representation for admin panel and debugging"""
        return f"{self.display_name} ({self.type_code})"
    
    @classmethod
    def get_active_types(cls):
        """
        Get all active question types.
        
        Returns:
            QuerySet: All question type configurations where is_active=True
        """
        return cls.objects.filter(is_active=True)
    
    @classmethod
    def add_new_type(cls, type_code, display_name, **kwargs):
        """
        Helper method to add new question types dynamically.
        
        Args:
            type_code (str): Unique identifier for the question type
            display_name (str): Human-readable name
            **kwargs: Additional configuration parameters
            
        Returns:
            QuestionTypeConfig: The created configuration object
        """
        return cls.objects.create(
            type_code=type_code,
            display_name=display_name,
            **kwargs
        )

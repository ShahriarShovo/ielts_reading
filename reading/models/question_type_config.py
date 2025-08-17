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
    - IELTS-standard instruction templates
    - Default answer formats for each question type
    - Template examples for frontend integration
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
    
    # NEW FIELDS FOR IELTS INSTRUCTION TEMPLATES
    # Default instruction text for this question type (e.g., "Do the following statements agree with the information given in Reading Passage 1?")
    default_instruction = models.TextField(blank=True, help_text="Default IELTS instruction text for this question type")
    
    # Default answer format instructions (e.g., "In boxes 1-7 on your answer sheet, write TRUE/FALSE/NOT GIVEN...")
    default_answer_format = models.TextField(blank=True, help_text="Default format instructions for how to answer this question type")
    
    # Template examples in JSON format for frontend integration
    # This stores multiple template examples for each question type
    template_examples = models.JSONField(default=list, blank=True, help_text="JSON array of template examples for this question type")
    
    # Word limit rules and configurations for this question type
    # Stores rules like "ONE WORD ONLY", "NO MORE THAN THREE WORDS", etc.
    word_limit_rules = models.JSONField(default=dict, blank=True, help_text="Word limit rules and configurations for this question type")
    
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
    
    def get_default_instruction(self, question_range="Questions 1-7"):
        """
        Get the default instruction text with dynamic question range.
        
        Args:
            question_range (str): The question range to insert (e.g., "Questions 1-7")
            
        Returns:
            str: Instruction text with the question range inserted
        """
        if not self.default_instruction:
            return ""
        
        # Replace placeholder with actual question range
        instruction = self.default_instruction.replace("{question_range}", question_range)
        return instruction
    
    def get_default_answer_format(self, question_range="Questions 1-7"):
        """
        Get the default answer format with dynamic question range.
        
        Args:
            question_range (str): The question range to insert (e.g., "Questions 1-7")
            
        Returns:
            str: Answer format text with the question range inserted
        """
        if not self.default_answer_format:
            return ""
        
        # Replace placeholder with actual question range
        answer_format = self.default_answer_format.replace("{question_range}", question_range)
        return answer_format
    
    def get_template_examples(self):
        """
        Get template examples for this question type.
        
        Returns:
            list: List of template examples for frontend integration
        """
        return self.template_examples if self.template_examples else []
    
    def get_word_limit_rules(self):
        """
        Get word limit rules for this question type.
        
        Returns:
            dict: Word limit rules and configurations
        """
        return self.word_limit_rules if self.word_limit_rules else {}

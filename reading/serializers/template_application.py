from rest_framework import serializers
from reading.models import Question, QuestionTypeConfig

class TemplateApplicationSerializer(serializers.Serializer):
    """
    Serializer for applying templates to questions.
    
    This serializer handles the logic for applying IELTS instruction templates
    to questions, automatically populating instruction text, answer formats,
    and other template-related fields.
    
    Key Features:
    - Apply question type templates to questions
    - Auto-populate instruction and answer format fields
    - Support for custom template modifications
    - Dynamic question range integration
    - Template validation and error handling
    """
    
    question_id = serializers.IntegerField(help_text="ID of the question to apply template to")
    template_name = serializers.CharField(help_text="Name of the template to apply")
    custom_instruction = serializers.CharField(required=False, allow_blank=True, help_text="Custom instruction text (optional)")
    custom_answer_format = serializers.CharField(required=False, allow_blank=True, help_text="Custom answer format (optional)")
    
    def validate_question_id(self, value):
        """
        Validate that the question exists.
        
        Args:
            value (int): The question ID to validate
            
        Returns:
            int: The validated question ID
            
        Raises:
            ValidationError: If question doesn't exist
        """
        try:
            Question.objects.get(id=value)
        except Question.DoesNotExist:
            raise serializers.ValidationError("Question does not exist")
        return value
    
    def validate_template_name(self, value):
        """
        Validate that the template name is valid.
        
        Args:
            value (str): The template name to validate
            
        Returns:
            str: The validated template name
            
        Raises:
            ValidationError: If template name is invalid
        """
        valid_templates = [
            'standard_tfng',
            'standard_mc',
            'standard_completion',
            'standard_matching',
            'custom'
        ]
        
        if value not in valid_templates:
            raise serializers.ValidationError(f"Invalid template name. Must be one of: {valid_templates}")
        
        return value
    
    def apply_template(self, question_id, template_name, custom_instruction=None, custom_answer_format=None):
        """
        Apply a template to a question.
        
        This method applies the specified template to the question,
        populating instruction and answer format fields with appropriate content.
        
        Args:
            question_id (int): The ID of the question
            template_name (str): The name of the template to apply
            custom_instruction (str, optional): Custom instruction text
            custom_answer_format (str, optional): Custom answer format
            
        Returns:
            dict: Summary of the template application
        """
        # Get the question
        question = Question.objects.get(id=question_id)
        
        # Get the question type configuration
        try:
            type_config = QuestionTypeConfig.objects.get(type_code=question.question_type)
        except QuestionTypeConfig.DoesNotExist:
            raise serializers.ValidationError(f"No configuration found for question type: {question.question_type}")
        
        # Calculate the question range for this question type
        question_range = question.calculate_question_range()
        
        # Apply template based on template name
        if template_name == 'standard_tfng' and question.question_type == 'TFNG':
            instruction = self._get_tfng_instruction(question_range)
            answer_format = self._get_tfng_answer_format(question_range)
        elif template_name == 'standard_mc' and question.question_type == 'MC':
            instruction = self._get_mc_instruction(question_range)
            answer_format = self._get_mc_answer_format(question_range)
        elif template_name == 'standard_completion' and question.question_type in ['SC', 'SUMC', 'NC', 'TC', 'FCC']:
            instruction = self._get_completion_instruction(question_range, question.question_type)
            answer_format = self._get_completion_answer_format(question_range, question.question_type)
        elif template_name == 'standard_matching' and question.question_type in ['MH', 'MP', 'MF', 'MSE']:
            instruction = self._get_matching_instruction(question_range, question.question_type)
            answer_format = self._get_matching_answer_format(question_range, question.question_type)
        elif template_name == 'custom':
            # Use custom instruction and answer format if provided
            instruction = custom_instruction or type_config.get_default_instruction(question_range)
            answer_format = custom_answer_format or type_config.get_default_answer_format(question_range)
        else:
            # Use default from question type configuration
            instruction = type_config.get_default_instruction(question_range)
            answer_format = type_config.get_default_answer_format(question_range)
        
        # Update the question with template data
        question.instruction = instruction
        question.answer_format = answer_format
        question.save(update_fields=['instruction', 'answer_format'])
        
        return {
            'question_id': question_id,
            'template_name': template_name,
            'instruction': instruction,
            'answer_format': answer_format,
            'question_range': question_range,
            'message': f"Successfully applied {template_name} template to question"
        }
    
    def _get_tfng_instruction(self, question_range):
        """
        Get True/False/Not Given instruction text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 1-7")
            
        Returns:
            str: The instruction text
        """
        return f"{question_range}\nDo the following statements agree with the information given in Reading Passage 1?"
    
    def _get_tfng_answer_format(self, question_range):
        """
        Get True/False/Not Given answer format text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 1-7")
            
        Returns:
            str: The answer format text
        """
        return f"In boxes {question_range.replace('Questions ', '')} on your answer sheet, write\nTRUE if the statement agrees with the information\nFALSE if the statement contradicts the information\nNOT GIVEN if there is no information on this"
    
    def _get_mc_instruction(self, question_range):
        """
        Get Multiple Choice instruction text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 8-13")
            
        Returns:
            str: The instruction text
        """
        return f"{question_range}\nChoose the correct letter, A, B, C or D."
    
    def _get_mc_answer_format(self, question_range):
        """
        Get Multiple Choice answer format text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 8-13")
            
        Returns:
            str: The answer format text
        """
        return f"Write the correct letter in boxes {question_range.replace('Questions ', '')} on your answer sheet."
    
    def _get_completion_instruction(self, question_range, question_type):
        """
        Get completion question instruction text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 14-18")
            question_type (str): The type of completion question
            
        Returns:
            str: The instruction text
        """
        type_descriptions = {
            'SC': 'Complete the sentences below.',
            'SUMC': 'Complete the summary below.',
            'NC': 'Complete the notes below.',
            'TC': 'Complete the table below.',
            'FCC': 'Complete the flow chart below.'
        }
        
        description = type_descriptions.get(question_type, 'Complete the following.')
        return f"{question_range}\n{description}\nChoose ONE WORD ONLY from the passage for each answer."
    
    def _get_completion_answer_format(self, question_range, question_type):
        """
        Get completion question answer format text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 14-18")
            question_type (str): The type of completion question
            
        Returns:
            str: The answer format text
        """
        return f"Write your answers in boxes {question_range.replace('Questions ', '')} on your answer sheet."
    
    def _get_matching_instruction(self, question_range, question_type):
        """
        Get matching question instruction text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 19-25")
            question_type (str): The type of matching question
            
        Returns:
            str: The instruction text
        """
        type_descriptions = {
            'MH': 'Match each paragraph with the correct heading.',
            'MP': 'Match each statement with the correct paragraph.',
            'MF': 'Match each feature with the correct option.',
            'MSE': 'Match each sentence ending with the correct beginning.'
        }
        
        description = type_descriptions.get(question_type, 'Match the following.')
        return f"{question_range}\n{description}"
    
    def _get_matching_answer_format(self, question_range, question_type):
        """
        Get matching question answer format text.
        
        Args:
            question_range (str): The question range (e.g., "Questions 19-25")
            question_type (str): The type of matching question
            
        Returns:
            str: The answer format text
        """
        return f"Write the correct letter in boxes {question_range.replace('Questions ', '')} on your answer sheet."


class TemplateInfoSerializer(serializers.Serializer):
    """
    Serializer for providing template information to the frontend.
    
    This serializer provides information about available templates
    for each question type.
    """
    
    template_name = serializers.CharField(help_text="Name of the template")
    display_name = serializers.CharField(help_text="Human-readable name for the template")
    description = serializers.CharField(help_text="Description of the template")
    instruction_preview = serializers.CharField(help_text="Preview of the instruction text")
    answer_format_preview = serializers.CharField(help_text="Preview of the answer format")
    
    def to_representation(self, instance):
        """
        Convert the data to a representation suitable for API response.
        
        Args:
            instance: The template data to convert
            
        Returns:
            dict: The formatted representation
        """
        return {
            'template_name': instance['name'],
            'display_name': instance['display_name'],
            'description': instance['description'],
            'instruction_preview': instance['instruction_preview'],
            'answer_format_preview': instance['answer_format_preview'],
            'question_type': instance.get('question_type', ''),
            'is_customizable': instance.get('is_customizable', False)
        }

from rest_framework import serializers
from reading.models import Question
from django.db import transaction

class QuestionReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering questions within a passage.
    
    This serializer handles the logic for reordering questions,
    updating order numbers, and recalculating question ranges.
    It ensures that the sequential ordering (1,2,3,4,5...) is maintained
    across all question types.
    
    Key Features:
    - Reorder questions by changing their order_number
    - Auto-update all affected order numbers
    - Recalculate question ranges after reordering
    - Maintain data integrity during reordering operations
    - Support for bulk reordering operations
    """
    
    passage_id = serializers.IntegerField(help_text="ID of the passage containing the questions")
    question_orders = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of question IDs and their new order numbers"
    )
    
    def validate_passage_id(self, value):
        """
        Validate that the passage exists.
        
        Args:
            value (int): The passage ID to validate
            
        Returns:
            int: The validated passage ID
            
        Raises:
            ValidationError: If passage doesn't exist
        """
        from reading.models import Passage
        try:
            Passage.objects.get(id=value)
        except Passage.DoesNotExist:
            raise serializers.ValidationError("Passage does not exist")
        return value
    
    def validate_question_orders(self, value):
        """
        Validate the question orders data structure.
        
        Args:
            value (list): List of question order dictionaries
            
        Returns:
            list: The validated question orders
            
        Raises:
            ValidationError: If validation fails
        """
        if not value:
            raise serializers.ValidationError("Question orders list cannot be empty")
        
        # Validate each question order entry
        for order_entry in value:
            if 'question_id' not in order_entry:
                raise serializers.ValidationError("Each order entry must contain 'question_id'")
            if 'new_order' not in order_entry:
                raise serializers.ValidationError("Each order entry must contain 'new_order'")
            
            # Validate question_id is integer
            try:
                int(order_entry['question_id'])
            except (ValueError, TypeError):
                raise serializers.ValidationError("question_id must be an integer")
            
            # Validate new_order is positive integer
            try:
                new_order = int(order_entry['new_order'])
                if new_order <= 0:
                    raise serializers.ValidationError("new_order must be greater than 0")
            except (ValueError, TypeError):
                raise serializers.ValidationError("new_order must be a positive integer")
        
        return value
    
    def validate(self, data):
        """
        Cross-field validation for reordering operation.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: The validated data
            
        Raises:
            ValidationError: If validation fails
        """
        passage_id = data.get('passage_id')
        question_orders = data.get('question_orders')
        
        # Validate that all questions belong to the specified passage
        question_ids = [entry['question_id'] for entry in question_orders]
        questions = Question.objects.filter(
            id__in=question_ids,
            passage_id=passage_id
        )
        
        if len(questions) != len(question_ids):
            raise serializers.ValidationError("Some questions do not belong to the specified passage")
        
        # Validate that new order numbers are unique
        new_orders = [entry['new_order'] for entry in question_orders]
        if len(new_orders) != len(set(new_orders)):
            raise serializers.ValidationError("New order numbers must be unique")
        
        return data
    
    @transaction.atomic
    def reorder_questions(self, passage_id, question_orders):
        """
        Reorder questions and update all related data.
        
        This method performs the actual reordering operation in a database
        transaction to ensure data consistency.
        
        Args:
            passage_id (int): The ID of the passage
            question_orders (list): List of question order dictionaries
            
        Returns:
            dict: Summary of the reordering operation
        """
        # Get all questions in the passage
        all_questions = Question.objects.filter(passage_id=passage_id).order_by('order_number')
        
        # Create a mapping of question_id to new_order
        order_mapping = {entry['question_id']: entry['new_order'] for entry in question_orders}
        
        # Update order numbers for specified questions
        updated_count = 0
        for question in all_questions:
            if question.id in order_mapping:
                question.order_number = order_mapping[question.id]
                question.save(update_fields=['order_number'])
                updated_count += 1
        
        # Reorder all questions to ensure sequential ordering
        self._reorder_all_questions(passage_id)
        
        # Update question ranges for all questions
        self._update_all_ranges(passage_id)
        
        return {
            'passage_id': passage_id,
            'updated_questions': updated_count,
            'message': f"Successfully reordered {updated_count} questions"
        }
    
    def _reorder_all_questions(self, passage_id):
        """
        Reorder all questions in a passage to ensure sequential ordering.
        
        This method ensures that all questions have sequential order numbers
        (1, 2, 3, 4, 5...) regardless of their previous order.
        
        Args:
            passage_id (int): The ID of the passage
        """
        questions = Question.objects.filter(passage_id=passage_id).order_by('order_number')
        
        # Assign sequential order numbers
        for index, question in enumerate(questions, 1):
            if question.order_number != index:
                question.order_number = index
                question.save(update_fields=['order_number'])
    
    def _update_all_ranges(self, passage_id):
        """
        Update question ranges for all questions in a passage.
        
        Args:
            passage_id (int): The ID of the passage
        """
        questions = Question.objects.filter(passage_id=passage_id)
        for question in questions:
            question.update_question_range()


class QuestionReorderInfoSerializer(serializers.Serializer):
    """
    Serializer for providing reordering information to the frontend.
    
    This serializer provides information about the current order of questions
    and allows the frontend to display reordering options.
    """
    
    question_id = serializers.IntegerField(help_text="ID of the question")
    question_text = serializers.CharField(help_text="Text of the question")
    question_type = serializers.CharField(help_text="Type of the question")
    current_order = serializers.IntegerField(help_text="Current order number")
    question_range = serializers.CharField(help_text="Current question range")
    
    def to_representation(self, instance):
        """
        Convert the data to a representation suitable for API response.
        
        Args:
            instance: The question instance to convert
            
        Returns:
            dict: The formatted representation
        """
        return {
            'question_id': instance.id,
            'question_text': instance.question_text[:100] + "..." if len(instance.question_text) > 100 else instance.question_text,
            'question_type': instance.question_type,
            'question_type_display': instance.get_question_type_display(),
            'current_order': instance.order_number,
            'question_range': instance.question_range,
            'instruction': instance.instruction,
            'answer_format': instance.answer_format
        }

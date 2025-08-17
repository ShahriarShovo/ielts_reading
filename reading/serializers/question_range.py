from rest_framework import serializers
from reading.models import Question

class QuestionRangeSerializer(serializers.Serializer):
    """
    Serializer for calculating and updating question ranges.
    
    This serializer handles the logic for calculating question ranges
    (e.g., "Questions 1-7", "Questions 8-13") across all questions
    in a passage, ensuring proper sequential ordering and range display.
    
    Key Features:
    - Calculate question ranges for all question types
    - Update ranges when questions are added/deleted/reordered
    - Maintain sequential ordering across all question types
    - Provide range information for frontend display
    """
    
    passage_id = serializers.IntegerField(help_text="ID of the passage to calculate ranges for")
    
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
    
    def calculate_ranges_for_passage(self, passage_id):
        """
        Calculate question ranges for all questions in a passage.
        
        This method analyzes all questions in a passage and calculates
        the appropriate ranges for each question type group.
        
        Args:
            passage_id (int): The ID of the passage
            
        Returns:
            dict: Dictionary containing range information for each question type
        """
        # Get all questions in the passage, ordered by order_number
        questions = Question.objects.filter(passage_id=passage_id).order_by('order_number')
        
        # Group questions by type
        questions_by_type = {}
        for question in questions:
            if question.question_type not in questions_by_type:
                questions_by_type[question.question_type] = []
            questions_by_type[question.question_type].append(question)
        
        # Calculate ranges for each question type
        ranges = {}
        current_order = 1
        
        for question_type, type_questions in questions_by_type.items():
            if type_questions:
                # Get the order numbers for this question type
                order_numbers = [q.order_number for q in type_questions]
                first_order = min(order_numbers)
                last_order = max(order_numbers)
                
                # Create range string
                range_str = f"Questions {first_order}-{last_order}"
                
                ranges[question_type] = {
                    'range': range_str,
                    'first_order': first_order,
                    'last_order': last_order,
                    'count': len(type_questions),
                    'questions': type_questions
                }
        
        return ranges
    
    def update_all_ranges(self, passage_id):
        """
        Update question ranges for all questions in a passage.
        
        This method recalculates and updates the question_range field
        for all questions in the specified passage.
        
        Args:
            passage_id (int): The ID of the passage
            
        Returns:
            dict: Summary of the update operation
        """
        # Get all questions in the passage
        questions = Question.objects.filter(passage_id=passage_id)
        
        # Update ranges for each question
        updated_count = 0
        for question in questions:
            question.update_question_range()
            updated_count += 1
        
        return {
            'passage_id': passage_id,
            'updated_questions': updated_count,
            'message': f"Updated question ranges for {updated_count} questions"
        }


class QuestionRangeInfoSerializer(serializers.Serializer):
    """
    Serializer for providing question range information to the frontend.
    
    This serializer provides structured information about question ranges
    and counts for display in the frontend interface.
    """
    
    question_type = serializers.CharField(help_text="Type of question (e.g., 'TFNG', 'MC')")
    display_name = serializers.CharField(help_text="Human-readable name for the question type")
    range_display = serializers.CharField(help_text="Question range (e.g., 'Questions 1-7')")
    question_count = serializers.IntegerField(help_text="Number of questions of this type")
    first_order = serializers.IntegerField(help_text="First question order number")
    last_order = serializers.IntegerField(help_text="Last question order number")
    
    def to_representation(self, instance):
        """
        Convert the data to a representation suitable for API response.
        
        Args:
            instance: The data to convert
            
        Returns:
            dict: The formatted representation
        """
        return {
            'question_type': instance['question_type'],
            'display_name': instance['display_name'],
            'range_display': instance['range'],
            'question_count': instance['count'],
            'first_order': instance['first_order'],
            'last_order': instance['last_order'],
            'progress_text': f"{instance['count']} {instance['display_name']} questions added"
        }

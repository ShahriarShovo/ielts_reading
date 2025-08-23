from rest_framework import serializers
from reading.models.question_type import QuestionType

class QuestionTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for QuestionType model.
    
    This serializer converts QuestionType model instances to JSON format
    for API responses, including all necessary fields for frontend display.
    """
    
    # Custom fields for better API response
    question_range = serializers.SerializerMethodField()
    student_range = serializers.SerializerMethodField()
    processed_instruction = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    remaining_question_slots = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionType
        fields = [
            'question_type_id',
            'passage',
            'type',
            'instruction_template',
            'expected_range',
            'student_range',
            'actual_count',
            'questions_data',
            'order',
            'image',
            'question_range',
            'processed_instruction',
            'question_count',
            'remaining_question_slots'
        ]
    
    def get_question_range(self, obj):
        """
        Get the question range within the passage.
        
        Returns the range of question numbers for this question type
        within its passage (e.g., "1-7", "8-11").
        """
        start, end = obj.get_question_range()
        return f"{start}-{end}"
    
    def get_student_range(self, obj):
        """
        Get the global sequential question range for students.
        
        Returns the range of question numbers that students will see
        across all passages (e.g., "1-7", "8-11", "12-15").
        """
        # Update student range if not set
        if not obj.student_range:
            obj.update_student_range()
        
        return obj.student_range
    
    def get_processed_instruction(self, obj):
        """
        Get the processed instruction with actual question numbers.
        
        Returns the instruction template with placeholders replaced
        with actual question numbers and passage information.
        """
        return obj.get_processed_instruction()
    
    def get_question_count(self, obj):
        """
        Get the number of questions in this question type.
        
        Returns the actual count of questions present.
        """
        return obj.actual_count
    
    def get_remaining_question_slots(self, obj):
        """
        Get the number of remaining question slots.
        
        Returns how many more questions can be added to this question type.
        """
        return obj.get_remaining_question_slots()

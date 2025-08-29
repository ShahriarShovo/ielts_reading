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
            'title',
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
    
    def validate_questions_data(self, value):
        """
        Validate and process questions_data field.
        Ensures options are properly formatted and converts answer to correct_answer.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("questions_data must be a list")
        
        processed_questions = []
        for i, question in enumerate(value):
            if not isinstance(question, dict):
                raise serializers.ValidationError(f"Question {i+1} must be a dictionary")
            
            # Ensure required fields exist - handle different field names for different question types
            if 'question_text' in question:
                # Standard format - already has question_text
                pass
            elif 'text' in question:
                # Note Completion format - convert text to question_text
                question['question_text'] = question.pop('text')
            else:
                raise serializers.ValidationError(f"Question {i+1} missing required field: question_text or text")
            
            # Handle answer fields - support both old format (answer/answers) and new format (correct_answer)
            if 'correct_answer' in question:
                # New format - already using correct_answer
                pass
            elif 'answer' in question:
                # Old format - convert to correct_answer
                question['correct_answer'] = question.pop('answer')
            elif 'answers' in question:
                # Old format - convert to correct_answer
                question['correct_answer'] = question.pop('answers')
            else:
                raise serializers.ValidationError(f"Question {i+1} missing answer/answers/correct_answer field")
            
            # Process options field if present
            if 'options' in question:
                options = question['options']
                if isinstance(options, list):
                    # Filter out empty strings and ensure proper formatting
                    processed_options = []
                    for option in options:
                        if option and str(option).strip():  # Check if option is not empty
                            processed_options.append(str(option).strip())
                    
                    # If no valid options found, generate default options for matching questions
                    if not processed_options and 'correct_answer' in question:
                        # Generate A, B, C, D, E, F, G based on the correct_answer
                        correct_answer = question['correct_answer']
                        if isinstance(correct_answer, str) and correct_answer.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
                            # Generate all possible options for matching information
                            processed_options = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
                    
                    # Update the question with processed options
                    question['options'] = processed_options
                else:
                    question['options'] = []
            else:
                question['options'] = []
            
            # Handle question_number field - support different field names
            if 'question_number' in question:
                # Standard format - already has question_number
                pass
            elif 'number' in question:
                # Note Completion format - convert number to question_number
                question['question_number'] = question.pop('number')
            else:
                # Default to index + 1
                question['question_number'] = i + 1
            
            processed_questions.append(question)
        
        return processed_questions

    def create(self, validated_data):
        """
        Create a new QuestionType instance with proper questions_data processing.
        """
        # Process questions_data before saving
        if 'questions_data' in validated_data:
            validated_data['questions_data'] = self.validate_questions_data(validated_data['questions_data'])
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing QuestionType instance with proper questions_data processing.
        """
        # Process questions_data before saving
        if 'questions_data' in validated_data:
            validated_data['questions_data'] = self.validate_questions_data(validated_data['questions_data'])
        
        return super().update(instance, validated_data)
    
    

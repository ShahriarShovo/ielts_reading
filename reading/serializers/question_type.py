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
    
    # Custom fields for Matching Headings
    headings = serializers.ListField(required=False, write_only=True)
    questions = serializers.ListField(required=False, write_only=True)
    
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
            'remaining_question_slots',
            'headings',
            'questions'
        ]
    
    def get_question_range(self, obj):
        """
        Get the question range within the passage.
        
        Returns the range of question numbers for this question type
        within its passage (e.g., "1-7", "8-11").
        """
        # Use the new dynamic question range calculation
        start, end = obj.get_dynamic_question_range()
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
        For MCMA questions, splits multiple answers into separate questions.
        For Matching Headings, processes special input format.
        """
        # Check if this is a Matching Headings question type
        # If so, use special processing for the input format
        if self.context.get('question_type') in ['Matching Headings', 'matching-headings']:
            # For Matching Headings, the input comes as a dict with 'headings' and 'questions'
            # instead of a list of questions
            if isinstance(value, dict):
                return self._process_matching_headings_input(value)
            else:
                raise serializers.ValidationError("Matching Headings requires headings and questions structure")
        
        # For all other question types, use standard validation
        if not isinstance(value, list):
            raise serializers.ValidationError("questions_data must be a list")
        
        processed_questions = []
        
        # Get the starting question number based on existing questions in the passage
        # This will be calculated dynamically based on the passage's current question count
        question_index = 0  # Will be updated when we have access to the passage
        
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
                    # Check if options are already in letter format (A, B, C, D, E)
                    if options and all(len(opt) == 1 and opt.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] for opt in options):
                        # Already in letter format - keep as is
                        processed_options = options
                        # Create option_texts mapping if not present
                        if 'option_texts' not in question:
                            question['option_texts'] = {}
                    else:
                        # Convert text options to letter format (A, B, C, D, E...)
                        processed_options = []
                        option_texts = {}
                        for i, option in enumerate(options):
                            if option and str(option).strip():  # Check if option is not empty
                                # Convert to letter format
                                letter = chr(65 + i)  # 65 = 'A', 66 = 'B', etc.
                                processed_options.append(letter)
                                option_texts[letter] = str(option).strip()
                        
                        # Add option_texts to question
                        question['option_texts'] = option_texts
                    
                    # Update the question with processed options
                    question['options'] = processed_options
                else:
                    question['options'] = []
                    question['option_texts'] = {}
            else:
                # Only add default options for question types that need them
                question_type = self.context.get('question_type', '') if hasattr(self, 'context') else ''
                
                # Question types that need options
                question_types_with_options = [
                    'Multiple Choice Questions (MCQ)',
                    'Multiple Choice Questions (Multiple Answer)',
                    'Matching Information',
                    'Matching Headings',  # Uncommented to enable options processing for Matching Headings
                    'Matching Experts',
                    'Sentence Matching'
                ]
                
                if question_type in question_types_with_options:
                    # Generate default options A, B, C, D, E for MCQ types
                    question['options'] = ['A', 'B', 'C', 'D', 'E']
                    question['option_texts'] = {}
                else:
                    # No options for completion/fill-in-the-blank types
                    question['options'] = []
                    question['option_texts'] = {}
            
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
            
            # Check if this is a MCMA question that needs splitting
            correct_answer = question.get('correct_answer', '')
            
            # Handle both string format (e.g., "A,C") and array format (e.g., ["A", "C"])
            if isinstance(correct_answer, str) and ',' in correct_answer:
                # String format with commas - split into separate questions
                answers = [ans.strip() for ans in correct_answer.split(',') if ans.strip()]
            elif isinstance(correct_answer, list) and len(correct_answer) > 1:
                # Array format with multiple answers - split into separate questions
                answers = correct_answer
            else:
                # Single answer - no splitting needed
                answers = None
            
            if answers:
                # Split into separate questions
                for answer_index, answer in enumerate(answers):
                    # Create a separate question for each answer
                    split_question = question.copy()
                    split_question['correct_answer'] = answer
                    split_question['question_number'] = question_index + 1
                    processed_questions.append(split_question)
                    question_index += 1
            else:
                # Regular question - no splitting needed
                question['question_number'] = question_index + 1
                processed_questions.append(question)
                question_index += 1
        
        return processed_questions

    def _process_matching_headings_input(self, data):
        """
        Process matching-headings input data structure.
        
        This method transforms the special matching-headings input format from teacher
        into the standard database format that can be stored in questions_data field.
        
        Input format:
        {
            "headings": [
                {"number": "i", "text": "heading 1", "is_used": true},
                {"number": "ii", "text": "heading 2", "is_used": true}
            ],
            "questions": [
                {"paragraph": "A", "correct_heading": "i"},
                {"paragraph": "B", "correct_heading": "ii"}
            ]
        }
        
        Output format:
        [
            {
                "question_text": "i. heading 1",
                "correct_answer": "i",
                "question_number": 1
            }
        ]
        
        Args:
            data (dict): The input data containing headings and questions
            
        Returns:
            list: Processed questions in database format
        """
        # Extract headings and questions from input data
        headings = data.get('headings', [])
        questions = data.get('questions', [])
        
        
        # Validate that we have the required data
        if not headings:
            raise serializers.ValidationError("Headings list is required for Matching Headings")
        if not questions:
            raise serializers.ValidationError("Questions list is required for Matching Headings")
        
        # Initialize the processed questions list
        processed_questions = []
        
        # Create options array with all heading numbers (i, ii, iii, iv, v...)
        heading_options = [h['number'] for h in headings]
        
        # Create option_texts mapping: Roman numeral -> heading text
        heading_option_texts = {}
        for heading in headings:
            if not isinstance(heading, dict):
                raise serializers.ValidationError("Each heading must be a dictionary")
            
            # Check required fields in heading
            if 'number' not in heading or 'text' not in heading:
                raise serializers.ValidationError("Each heading must have 'number' and 'text' fields")
            
            heading_option_texts[heading['number']] = heading['text']
        
        
        # Process each paragraph question (A, B, C, D, E...)
        for question in questions:
            if not isinstance(question, dict):
                raise serializers.ValidationError("Each question must be a dictionary")
            
            if 'paragraph' not in question or 'correct_heading' not in question:
                raise serializers.ValidationError("Each question must have 'paragraph' and 'correct_heading' fields")
            
            # Validate that the correct_heading exists in headings list
            valid_heading_numbers = [h['number'] for h in headings]
            if question['correct_heading'] not in valid_heading_numbers:
                raise serializers.ValidationError(f"Question for paragraph {question['paragraph']} references invalid heading: {question['correct_heading']}")
            
            # Create question text as "Paragraph A", "Paragraph B", etc.
            question_text = f"Paragraph {question['paragraph']}"
            
            # Set correct answer as the heading number (i, ii, iii, etc.)
            correct_answer = question['correct_heading']
            
            # Add to processed questions list
            processed_questions.append({
                'question_text': question_text,
                'correct_answer': correct_answer,
                'question_number': len(processed_questions) + 1,  # Will be updated with global numbering later
                'options': heading_options,  # All heading numbers as options
                'option_texts': heading_option_texts  # Roman numeral -> heading text mapping
            })
        
        return processed_questions

    def _process_questions_with_numbering(self, value, starting_number=1):
        """
        Process questions_data with dynamic question numbering starting from a specific number.
        This method is similar to validate_questions_data but with custom starting number.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("questions_data must be a list")
        
        processed_questions = []
        question_index = starting_number - 1  # Convert to 0-based index
        
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
                    # Check if options are already in letter format (A, B, C, D, E)
                    if options and all(len(opt) == 1 and opt.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] for opt in options):
                        # Already in letter format - keep as is
                        processed_options = options
                        # Create option_texts mapping if not present
                        if 'option_texts' not in question:
                            question['option_texts'] = {}
                    else:
                        # Convert text options to letter format (A, B, C, D, E...)
                        processed_options = []
                        option_texts = {}
                        for j, option in enumerate(options):
                            if option and str(option).strip():  # Check if option is not empty
                                # Convert to letter format
                                letter = chr(65 + j)  # 65 = 'A', 66 = 'B', etc.
                                processed_options.append(letter)
                                option_texts[letter] = str(option).strip()
                        
                        # Add option_texts to question
                        question['option_texts'] = option_texts
                    
                    # Update the question with processed options
                    question['options'] = processed_options
                else:
                    question['options'] = []
                    question['option_texts'] = {}
            else:
                # Only add default options for question types that need them
                question_type = self.context.get('question_type', '') if hasattr(self, 'context') else ''
                
                # Question types that need options
                question_types_with_options = [
                    'Multiple Choice Questions (MCQ)',
                    'Multiple Choice Questions (Multiple Answer)',
                    'Matching Information',
                    'Matching Headings', 
                    'Matching Experts',
                    'Sentence Matching'
                ]
                
                if question_type in question_types_with_options:
                    # Generate default options A, B, C, D, E for MCQ types
                    question['options'] = ['A', 'B', 'C', 'D', 'E']
                    question['option_texts'] = {}
                else:
                    # No options for completion/fill-in-the-blank types
                    question['options'] = []
                    question['option_texts'] = {}
            
            # Handle question_number field - support different field names
            if 'question_number' in question:
                # Standard format - already has question_number
                pass
            elif 'number' in question:
                # Note Completion format - convert number to question_number
                question['question_number'] = question.pop('number')
            else:
                # Use the dynamic starting number instead of index + 1
                question['question_number'] = question_index + 1
            
            # Check if this is a MCMA question that needs splitting
            correct_answer = question.get('correct_answer', '')
            
            # Handle both string format (e.g., "A,C") and array format (e.g., ["A", "C"])
            if isinstance(correct_answer, str) and ',' in correct_answer:
                # String format with commas - split into separate questions
                answers = [ans.strip() for ans in correct_answer.split(',') if ans.strip()]
            elif isinstance(correct_answer, list) and len(correct_answer) > 1:
                # Array format with multiple answers - split into separate questions
                answers = correct_answer
            else:
                # Single answer - no splitting needed
                answers = None
            
            if answers:
                # Split into separate questions
                for answer_index, answer in enumerate(answers):
                    # Create a separate question for each answer
                    split_question = question.copy()
                    split_question['correct_answer'] = answer
                    split_question['question_number'] = question_index + 1
                    processed_questions.append(split_question)
                    question_index += 1
            else:
                # Regular question - no splitting needed
                question['question_number'] = question_index + 1
                processed_questions.append(question)
                question_index += 1
        
        return processed_questions

    def create(self, validated_data):
        """
        Create a new QuestionType instance with proper questions_data processing.
        """
        # Special processing for Matching Headings question type
        if 'type' in validated_data and validated_data['type'] in ['Matching Headings', 'matching-headings']:
            # Set the question type context for validation
            self.context['question_type'] = 'Matching Headings'
            
            # For Matching Headings, we expect the input to have 'headings' and 'questions' fields
            # instead of 'questions_data' field
            if 'headings' in validated_data and 'questions' in validated_data:
                # Transform the special input format to standard questions_data format
                # This will be processed by the _process_matching_headings_input method
                matching_headings_data = {
                    'headings': validated_data.pop('headings'),  # Remove from validated_data
                    'questions': validated_data.pop('questions')  # Remove from validated_data
                }
                
                # Set the transformed data as questions_data
                validated_data['questions_data'] = matching_headings_data
                
                # Process the matching headings data immediately
                processed_data = self._process_matching_headings_input(validated_data['questions_data'])
                validated_data['questions_data'] = processed_data
        
        # Remove any remaining custom fields that are not part of the model
        # These fields are only used for processing and should not be passed to the model
        validated_data.pop('headings', None)
        validated_data.pop('questions', None)
        
        # Process questions_data before saving (for all question types)
        if 'questions_data' in validated_data:
            # Get the starting question number based on existing questions in the passage
            passage = validated_data.get('passage')
            if passage:
                # Calculate starting question number based on existing questions
                starting_number = passage.get_next_question_number()
                
                # Debug logging
                import logging
                logger = logging.getLogger('reading')
                logger.info(f"=== SERIALIZER CREATE DEBUG ===")
                logger.info(f"Passage: {passage.title} (Order: {passage.order})")
                logger.info(f"Passage question count: {passage.get_question_count()}")
                logger.info(f"Calculated starting number: {starting_number}")
                logger.info(f"Questions to process: {len(validated_data['questions_data'])}")
                
                # Special handling for Matching Headings - skip _process_questions_with_numbering
                # to preserve the correct options and option_texts
                if validated_data.get('type') in ['Matching Headings', 'matching-headings']:
                    # For Matching Headings, just update the question numbers
                    for i, question in enumerate(validated_data['questions_data']):
                        question['question_number'] = starting_number + i
                else:
                    # For other question types, use the standard processing
                    # Pass question type context for proper options handling
                    question_type = validated_data.get('type', '')
                    self.context['question_type'] = question_type
                    
                    validated_data['questions_data'] = self._process_questions_with_numbering(
                        validated_data['questions_data'], 
                        starting_number=starting_number
                    )
            else:
                validated_data['questions_data'] = self.validate_questions_data(validated_data['questions_data'])
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing QuestionType instance with proper questions_data processing.
        """
        # Special processing for Matching Headings question type
        if instance.type in ['Matching Headings', 'matching-headings']:
            # Set the question type context for validation
            self.context['question_type'] = 'Matching Headings'
            
            # For Matching Headings, we expect the input to have 'headings' and 'questions' fields
            # instead of 'questions_data' field
            if 'headings' in validated_data and 'questions' in validated_data:
                # Transform the special input format to standard questions_data format
                # This will be processed by the _process_matching_headings_input method
                matching_headings_data = {
                    'headings': validated_data.pop('headings'),  # Remove from validated_data
                    'questions': validated_data.pop('questions')  # Remove from validated_data
                }
                # Set the transformed data as questions_data
                validated_data['questions_data'] = matching_headings_data
                
                # Process the matching headings data immediately
                processed_data = self._process_matching_headings_input(validated_data['questions_data'])
                validated_data['questions_data'] = processed_data
        
        # Remove any remaining custom fields that are not part of the model
        # These fields are only used for processing and should not be passed to the model
        validated_data.pop('headings', None)
        validated_data.pop('questions', None)
        
        # Process questions_data before saving (for all question types)
        if 'questions_data' in validated_data:
            # Get the starting question number based on existing questions in the passage
            passage = instance.passage
            if passage:
                # Calculate starting question number based on existing questions
                starting_number = passage.get_next_question_number()
                
                # Debug logging
                import logging
                logger = logging.getLogger('reading')
                logger.info(f"=== SERIALIZER UPDATE DEBUG ===")
                logger.info(f"Question Type: {instance.type}")
                logger.info(f"Passage: {passage.title} (Order: {passage.order})")
                logger.info(f"Calculated starting number: {starting_number}")
                logger.info(f"Questions to process: {len(validated_data['questions_data'])}")
                
                # Pass question type context for proper options handling
                question_type = instance.type
                self.context['question_type'] = question_type
                
                validated_data['questions_data'] = self._process_questions_with_numbering(
                    validated_data['questions_data'], 
                    starting_number=starting_number
                )
            else:
                validated_data['questions_data'] = self.validate_questions_data(validated_data['questions_data'])
        
        return super().update(instance, validated_data)
    
    

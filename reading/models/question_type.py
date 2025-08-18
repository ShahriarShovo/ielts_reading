from django.db import models
import uuid
import json
from .passage import Passage

class QuestionType(models.Model):
    """
    Model representing a question type within a reading passage.
    
    This is the third-level model in the 4-level hierarchy: Test -> Passage -> Question Type -> Individual Questions.
    Each question type belongs to a specific passage and contains multiple individual questions of the same type.
    
    Key Features:
    - Unique question type identifier for easy reference
    - Belongs to a specific passage
    - Contains instruction template with dynamic placeholders
    - Expected vs actual question count for flexibility
    - Multiple individual questions per question type
    - UUID-based primary key for security and scalability
    - JSON storage for individual questions data
    """
    
    # Unique identifier for the question type - using UUID for security and scalability
    # This replaces the auto-incrementing ID and provides a more secure identifier
    question_type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key relationship to the parent passage
    # CASCADE delete means if the passage is deleted, all its question types are also deleted
    # This maintains referential integrity in the database
    passage = models.ForeignKey(Passage, on_delete=models.CASCADE, related_name='questions')
    
    # Type of question (e.g., "Multiple Choice Questions (MCQ)", "True/False/Not Given")
    # This identifies the specific IELTS question type
    type = models.CharField(max_length=100)
    
    # Instruction template with placeholders for dynamic content
    # This template contains placeholders like {start}, {end}, {passage_number} that get replaced
    # Example: "Questions {start}-{end}\nDo the following statements agree with the information given in Reading Passage {passage_number}?"
    instruction_template = models.TextField()
    
    # Expected range of questions (e.g., "1-7", "14-20")
    # This is the planned range, but actual count may differ
    expected_range = models.CharField(max_length=20)
    
    # Actual number of questions present in this question type
    # This allows flexibility - examiner can have 3, 4, 5, 6, or 7 questions for same type
    actual_count = models.PositiveIntegerField(default=0)
    
    # Individual questions data stored as JSON
    # This contains an array of question objects with number, text, options, answer
    # Example: [{"number": 1, "text": "Question text", "options": ["A", "B", "C", "D"], "answer": "B"}]
    questions_data = models.JSONField(default=list)
    
    # Order of this question type within the passage
    # This determines the sequence in which question types appear in the passage
    order = models.PositiveIntegerField(default=1)

    class Meta:
        """
        Meta configuration for the QuestionType model.
        
        - ordering: Question types are ordered by their sequence number within the passage
        - db_table: Custom table name for database organization
        - verbose_name: Human-readable name for admin panel
        """
        ordering = ['order']  # Order question types by their sequence number
        db_table = 'reading_question_type'
        verbose_name = 'Question Type'
        verbose_name_plural = 'Question Types'

    def __str__(self):
        """
        String representation for admin panel, debugging, and logging.
        
        Returns a human-readable string that includes the question type, order,
        and passage title for easy identification.
        """
        passage_title = self.passage.title if self.passage.title else f"Passage {self.passage.order}"
        return f"{self.type} (Order: {self.order}, Passage: {passage_title})"
    
    def get_processed_instruction(self):
        """
        Process the instruction template by replacing placeholders with actual values.
        
        This method calculates the actual start and end question numbers and replaces
        placeholders in the instruction template with real values.
        
        Returns the processed instruction text ready for display to students.
        """
        # Calculate start and end question numbers for this question type
        start_number, end_number = self.get_question_range()
        
        # Get the passage number (order within the test)
        passage_number = self.passage.order
        
        # Replace placeholders in the instruction template
        processed_instruction = self.instruction_template
        processed_instruction = processed_instruction.replace('{start}', str(start_number))
        processed_instruction = processed_instruction.replace('{end}', str(end_number))
        processed_instruction = processed_instruction.replace('{passage_number}', str(passage_number))
        
        return processed_instruction
    
    def get_question_range(self):
        """
        Calculate the start and end question numbers for this question type.
        
        This method determines the actual question numbers based on the order
        of question types within the passage and the number of questions in each type.
        
        Returns a tuple of (start_number, end_number).
        """
        # Get all question types in order up to this one within the same passage
        previous_question_types = QuestionType.objects.filter(
            passage=self.passage,
            order__lt=self.order
        ).order_by('order')
        
        # Calculate start number based on previous question types
        start_number = 1
        for prev_question_type in previous_question_types:
            start_number += prev_question_type.actual_count
        
        # Calculate end number based on this question type's actual count
        end_number = start_number + self.actual_count - 1
        
        return (start_number, end_number)
    
    def add_question(self, question_text, answer, options=None, number=None):
        """
        Add a new individual question to this question type.
        
        This method adds a question to the questions_data JSON field and updates
        the actual_count field.
        
        Args:
            question_text (str): The question text
            answer (str): The correct answer
            options (list, optional): List of options for multiple choice questions
            number (int, optional): Question number (auto-assigned if not provided)
        """
        # Auto-assign question number if not provided
        if number is None:
            number = len(self.questions_data) + 1
        
        # Create question object
        question_obj = {
            'number': number,
            'text': question_text,
            'answer': answer
        }
        
        # Add options if provided (for multiple choice questions)
        if options:
            question_obj['options'] = options
        
        # Add to questions_data
        self.questions_data.append(question_obj)
        
        # Update actual count
        self.actual_count = len(self.questions_data)
        self.save()
    
    def remove_question(self, question_number):
        """
        Remove a question from this question type.
        
        This method removes a question from the questions_data JSON field and updates
        the actual_count field.
        
        Args:
            question_number (int): The number of the question to remove
        """
        # Find and remove the question
        self.questions_data = [q for q in self.questions_data if q.get('number') != question_number]
        
        # Update actual count
        self.actual_count = len(self.questions_data)
        self.save()
    
    def update_question(self, question_number, question_text=None, answer=None, options=None):
        """
        Update an existing question in this question type.
        
        This method updates the specified fields of an existing question.
        
        Args:
            question_number (int): The number of the question to update
            question_text (str, optional): New question text
            answer (str, optional): New correct answer
            options (list, optional): New options list
        """
        for question in self.questions_data:
            if question.get('number') == question_number:
                if question_text is not None:
                    question['text'] = question_text
                if answer is not None:
                    question['answer'] = answer
                if options is not None:
                    question['options'] = options
                break
        
        self.save()
    
    def reorder_questions(self):
        """
        Reorder question numbers to ensure they are sequential.
        
        This method updates the question numbers to be sequential (1, 2, 3, ...)
        after questions have been added or removed.
        """
        for i, question in enumerate(self.questions_data, 1):
            question['number'] = i
        
        self.save()
    
    def can_add_questions(self, additional_questions=1):
        """
        Check if additional questions can be added to this question type.
        
        This checks both the passage-level and test-level limits.
        
        Args:
            additional_questions (int): Number of questions to be added
            
        Returns True if adding the specified number of questions won't exceed limits.
        """
        return self.passage.can_add_questions(additional_questions)
    
    def get_remaining_question_slots(self):
        """
        Get the number of remaining question slots available for this question type.
        
        Returns the number of questions that can still be added.
        """
        return self.passage.get_remaining_question_slots()

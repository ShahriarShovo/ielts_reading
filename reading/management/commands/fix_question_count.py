from django.core.management.base import BaseCommand
from reading.models import ReadingTest, Passage, QuestionType
import json


class Command(BaseCommand):
    help = 'Add missing questions to reach 40 questions per test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-id',
            type=str,
            help='Specific test ID to fix (optional)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Fixing question counts to reach 40 questions...')
        
        tests_to_fix = ReadingTest.objects.all()
        if options['test_id']:
            tests_to_fix = tests_to_fix.filter(test_id=options['test_id'])
        
        for test in tests_to_fix:
            self.stdout.write(f'\nProcessing Test: {test.test_name}')
            
            total_questions = 0
            passages = Passage.objects.filter(test=test).order_by('order')
            
            # Calculate current total
            for passage in passages:
                for qt in QuestionType.objects.filter(passage=passage):
                    total_questions += qt.actual_count
            
            missing_questions = 40 - total_questions
            
            if missing_questions <= 0:
                self.stdout.write(f'  ✅ Already has {total_questions} questions (no action needed)')
                continue
            
            self.stdout.write(f'  Current: {total_questions} questions, Missing: {missing_questions} questions')
            
            # Add missing questions to the last passage
            last_passage = passages.last()
            if not last_passage:
                self.stdout.write(f'  ❌ No passages found for test {test.test_name}')
                continue
            
            # Get the last question type in the last passage
            last_question_type = QuestionType.objects.filter(passage=last_passage).order_by('order').last()
            if not last_question_type:
                self.stdout.write(f'  ❌ No question types found in last passage')
                continue
            
            # Add missing questions to the last question type
            current_count = last_question_type.actual_count
            new_count = current_count + missing_questions
            
            # Update the question type
            last_question_type.actual_count = new_count
            
            # Add dummy questions to questions_data
            current_questions = last_question_type.questions_data or []
            for i in range(current_count + 1, new_count + 1):
                dummy_question = {
                    "number": i,
                    "text": f"Question {i} (Auto-generated)",
                    "answer": "A"
                }
                
                # Add options for MCQ types
                if "Multiple Choice" in last_question_type.type:
                    dummy_question["options"] = ["A", "B", "C", "D"]
                    dummy_question["option_texts"] = {
                        "A": "Option A",
                        "B": "Option B", 
                        "C": "Option C",
                        "D": "Option D"
                    }
                
                current_questions.append(dummy_question)
            
            last_question_type.questions_data = current_questions
            last_question_type.save()
            
            # Update student ranges
            last_question_type.update_student_range()
            
            self.stdout.write(f'  ✅ Added {missing_questions} questions to {last_question_type.type}')
            self.stdout.write(f'  ✅ Updated total: {new_count} questions in {last_question_type.type}')
        
        self.stdout.write(self.style.SUCCESS('\nQuestion count fix completed!'))

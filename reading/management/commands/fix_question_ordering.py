from django.core.management.base import BaseCommand
from reading.models import Passage, QuestionType, ReadingTest


class Command(BaseCommand):
    help = 'Fix existing passage and question type ordering issues'

    def handle(self, *args, **options):
        self.stdout.write('Starting to fix question ordering...')
        
        # Fix all tests
        for test in ReadingTest.objects.all():
            self.stdout.write(f'Processing test: {test.test_name}')
            
            # Fix passage orders
            passages = Passage.objects.filter(test=test)
            for i, passage in enumerate(passages, 1):
                old_order = passage.order
                passage.order = i
                passage.save()
                self.stdout.write(f'  Updated Passage: {passage.title} -> Order {old_order} -> {i}')
            
            # Fix question type orders within each passage
            for passage in passages:
                self.stdout.write(f'  Processing passage: {passage.title}')
                
                question_types = QuestionType.objects.filter(passage=passage).order_by('expected_range')
                for i, qt in enumerate(question_types, 1):
                    old_order = qt.order
                    qt.order = i
                    qt.save()
                    self.stdout.write(f'    Updated {qt.type}: Order {old_order} -> {i}')
                
                # Update student ranges for this passage
                passage.update_all_student_ranges()
                self.stdout.write(f'    Updated student ranges for passage {passage.title}')
        
        # Final verification
        self.stdout.write('\nFinal verification:')
        for test in ReadingTest.objects.all():
            self.stdout.write(f'\nTest: {test.test_name}')
            for passage in Passage.objects.filter(test=test).order_by('order'):
                self.stdout.write(f'  Passage {passage.order}: {passage.title}')
                for qt in QuestionType.objects.filter(passage=passage).order_by('order'):
                    self.stdout.write(f'    {qt.type}: Order {qt.order}, Expected={qt.expected_range}, Student={qt.student_range}')
        
        self.stdout.write(self.style.SUCCESS('Successfully fixed all question ordering issues!'))

from django.core.management.base import BaseCommand
from reading.models import Passage, QuestionType, ReadingTest


class Command(BaseCommand):
    help = 'Fix duplicate passage orders before migration'

    def handle(self, *args, **options):
        self.stdout.write('Starting to fix duplicate passage orders...')
        
        # Fix all tests
        for test in ReadingTest.objects.all():
            self.stdout.write(f'Processing test: {test.test_name}')
            
            # Get all passages for this test and fix their orders
            passages = Passage.objects.filter(test=test)
            
            # First, set all orders to None to avoid conflicts
            for passage in passages:
                passage.order = None
                passage.save()
                self.stdout.write(f'  Reset order for: {passage.title}')
            
            # Now assign sequential orders
            for i, passage in enumerate(passages, 1):
                passage.order = i
                passage.save()
                self.stdout.write(f'  Updated Passage: {passage.title} -> Order {i}')
            
            # Fix question type orders within each passage
            for passage in passages:
                self.stdout.write(f'  Processing passage: {passage.title}')
                
                question_types = QuestionType.objects.filter(passage=passage)
                
                # Instead of setting to None, assign temporary high numbers
                for i, qt in enumerate(question_types, 1000):
                    qt.order = i
                    qt.save()
                
                # Now assign proper sequential orders based on expected_range
                question_types = QuestionType.objects.filter(passage=passage).order_by('expected_range')
                for i, qt in enumerate(question_types, 1):
                    qt.order = i
                    qt.save()
                    self.stdout.write(f'    Updated {qt.type}: Order {i}')
        
        self.stdout.write(self.style.SUCCESS('Successfully fixed all duplicate orders!'))

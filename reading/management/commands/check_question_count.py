from django.core.management.base import BaseCommand
from reading.models import ReadingTest, Passage, QuestionType


class Command(BaseCommand):
    help = 'Check and fix question counts to ensure 40 questions per test'

    def handle(self, *args, **options):
        self.stdout.write('Checking question counts...')
        
        for test in ReadingTest.objects.all():
            self.stdout.write(f'\nTest: {test.test_name}')
            
            total_questions = 0
            for passage in Passage.objects.filter(test=test).order_by('order'):
                passage_questions = 0
                self.stdout.write(f'  Passage {passage.order}: {passage.title}')
                
                for qt in QuestionType.objects.filter(passage=passage).order_by('order'):
                    self.stdout.write(f'    {qt.type}: {qt.actual_count} questions (Expected: {qt.expected_range}, Student: {qt.student_range})')
                    passage_questions += qt.actual_count
                
                self.stdout.write(f'    Passage Total: {passage_questions} questions')
                total_questions += passage_questions
            
            self.stdout.write(f'  Test Total: {total_questions}/40 questions')
            
            if total_questions < 40:
                self.stdout.write(f'  ⚠️  Missing {40 - total_questions} questions!')
            elif total_questions > 40:
                self.stdout.write(f'  ⚠️  Too many questions: {total_questions} > 40!')
            else:
                self.stdout.write(f'  ✅ Perfect: {total_questions} questions')
        
        self.stdout.write(self.style.SUCCESS('\nQuestion count check completed!'))

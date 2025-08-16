from django.core.management.base import BaseCommand
from reading.models import QuestionTypeConfig

class Command(BaseCommand):
    help = 'Initialize standard IELTS question types in QuestionTypeConfig'

    def handle(self, *args, **options):
        """Initialize all standard IELTS question types"""
        
        # Define all standard IELTS question types with their configurations
        question_types = [
            {
                'type_code': 'MC',
                'display_name': 'Multiple Choice',
                'description': 'Choose the correct answer from multiple options',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'TFNG',
                'display_name': 'True/False/Not Given',
                'description': 'Determine if statement is True, False, or Not Given',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'YNN',
                'display_name': 'Yes/No/Not Given',
                'description': 'Determine if statement is Yes, No, or Not Given',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'SA',
                'display_name': 'Short Answer',
                'description': 'Answer questions with short responses',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'SC',
                'display_name': 'Sentence Completion',
                'description': 'Complete sentences with missing words',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'MH',
                'display_name': 'Matching Headings',
                'description': 'Match paragraph headings to paragraphs',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'MP',
                'display_name': 'Matching Paragraphs',
                'description': 'Match information to paragraphs',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'MF',
                'display_name': 'Matching Features',
                'description': 'Match features or characteristics',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'MSE',
                'display_name': 'Matching Sentence Endings',
                'description': 'Complete sentences by matching endings',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'SUMC',
                'display_name': 'Summary Completion',
                'description': 'Complete summary with missing words',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'NC',
                'display_name': 'Note Completion',
                'description': 'Complete notes with missing information',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'TC',
                'display_name': 'Table Completion',
                'description': 'Complete table with missing data',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'FCC',
                'display_name': 'Flow Chart Completion',
                'description': 'Complete flow chart with missing steps',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
            },
            {
                'type_code': 'DL',
                'display_name': 'Diagram Labelling',
                'description': 'Label parts of a diagram',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': True,
            },
            {
                'type_code': 'PFL',
                'display_name': 'Pick from List',
                'description': 'Choose answer from provided list',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
            {
                'type_code': 'CUSTOM',
                'display_name': 'Custom Question Type',
                'description': 'Custom question type for future use',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for question_type in question_types:
            config, created = QuestionTypeConfig.objects.get_or_create(
                type_code=question_type['type_code'],
                defaults=question_type
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {config.display_name} ({config.type_code})')
                )
            else:
                # Update existing config
                for key, value in question_type.items():
                    setattr(config, key, value)
                config.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated: {config.display_name} ({config.type_code})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nQuestion types initialization completed!\n'
                f'Created: {created_count}\n'
                f'Updated: {updated_count}\n'
                f'Total: {QuestionTypeConfig.objects.count()}'
            )
        )

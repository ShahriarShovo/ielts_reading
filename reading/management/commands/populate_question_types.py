from django.core.management.base import BaseCommand
from reading.models import QuestionTypeConfig

class Command(BaseCommand):
    help = 'Populate the database with default IELTS question types'

    def handle(self, *args, **options):
        self.stdout.write('Creating default IELTS question types...')
        
        # Define the standard IELTS question types
        question_types = [
            {
                'type_code': 'MC',
                'display_name': 'Multiple Choice Questions',
                'description': 'Choose the correct letter A, B, C or D',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Choose the correct letter A, B, C or D.',
                'default_answer_format': 'Write the correct letter A, B, C or D in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'What is the main purpose of the passage?',
                        'options': ['A. To describe a new technology', 'B. To explain a historical event', 'C. To present research findings', 'D. To compare different methods']
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'TFNG',
                'display_name': 'True/False/Not Given',
                'description': 'Do the following statements agree with the information given in the passage?',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Do the following statements agree with the information given in Reading Passage {passage_number}?',
                'default_answer_format': 'In boxes {question_range} on your answer sheet, write TRUE if the statement agrees with the information, FALSE if the statement contradicts the information, or NOT GIVEN if there is no information on this.',
                'template_examples': [
                    {
                        'question': 'The research was conducted over a period of five years.',
                        'answer': 'TRUE'
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'YNNG',
                'display_name': 'Yes/No/Not Given',
                'description': 'Do the following statements agree with the views of the writer?',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Do the following statements agree with the views of the writer in Reading Passage {passage_number}?',
                'default_answer_format': 'In boxes {question_range} on your answer sheet, write YES if the statement agrees with the views of the writer, NO if the statement contradicts the views of the writer, or NOT GIVEN if it is impossible to say what the writer thinks about this.',
                'template_examples': [
                    {
                        'question': 'The writer believes that technology will solve all environmental problems.',
                        'answer': 'NO'
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'MI',
                'display_name': 'Matching Information',
                'description': 'Which paragraph contains the following information?',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Which paragraph contains the following information?',
                'default_answer_format': 'Write the correct letter A-G in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'A description of how the research was conducted',
                        'answer': 'C'
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'MH',
                'display_name': 'Matching Headings',
                'description': 'Choose the correct heading for each paragraph',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Choose the correct heading for each paragraph from the list of headings below.',
                'default_answer_format': 'Write the correct number i-x in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'Paragraph A',
                        'options': ['i. Introduction to the topic', 'ii. Historical background', 'iii. Current developments', 'iv. Future implications']
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'MF',
                'display_name': 'Matching Features',
                'description': 'Match each statement with the correct person, place, or thing',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Match each statement with the correct person, place, or thing.',
                'default_answer_format': 'Write the correct letter A-F in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'Was the first to discover this phenomenon',
                        'options': ['A. Dr. Smith', 'B. Professor Johnson', 'C. The research team', 'D. The university', 'E. The laboratory', 'F. The government']
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'MSE',
                'display_name': 'Matching Sentence Endings',
                'description': 'Complete each sentence with the correct ending',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'default_instruction': 'Complete each sentence with the correct ending.',
                'default_answer_format': 'Write the correct letter A-G in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'The research showed that',
                        'options': ['A. the results were inconclusive', 'B. further study was needed', 'C. the hypothesis was confirmed', 'D. the method was flawed']
                    }
                ],
                'word_limit_rules': {}
            },
            {
                'type_code': 'SC',
                'display_name': 'Sentence Completion',
                'description': 'Complete the sentences with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'default_instruction': 'Complete the sentences below with words from the passage.',
                'default_answer_format': 'Use NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'The main cause of the problem was __________.',
                        'answer': 'climate change',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS', 'NO MORE THAN FOUR WORDS']
                }
            },
            {
                'type_code': 'SUMC',
                'display_name': 'Summary Completion',
                'description': 'Complete the summary with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'default_instruction': 'Complete the summary using the list of words, A-G, below.',
                'default_answer_format': 'Write the correct letter A-G in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'The research focused on the __________ of the phenomenon.',
                        'answer': 'A',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS']
                }
            },
            {
                'type_code': 'NC',
                'display_name': 'Note Completion',
                'description': 'Complete the notes with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'default_instruction': 'Complete the notes below with words from the passage.',
                'default_answer_format': 'Choose NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'Research method: __________',
                        'answer': 'survey',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS']
                }
            },
            {
                'type_code': 'TC',
                'display_name': 'Table Completion',
                'description': 'Complete the table with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'default_instruction': 'Complete the table below with words from the passage.',
                'default_answer_format': 'Choose NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'Year: __________',
                        'answer': '2020',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS']
                }
            },
            {
                'type_code': 'FCC',
                'display_name': 'Flow-chart Completion',
                'description': 'Complete the flow-chart with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'default_instruction': 'Complete the flow-chart below with words from the passage.',
                'default_answer_format': 'Choose NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'Step 1: __________',
                        'answer': 'collect data',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS']
                }
            },
            {
                'type_code': 'DL',
                'display_name': 'Diagram Labelling',
                'description': 'Label the diagram with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': True,
                'default_instruction': 'Label the diagram below with words from the passage.',
                'default_answer_format': 'Choose NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'Part A: __________',
                        'answer': 'nucleus',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS']
                }
            },
            {
                'type_code': 'SA',
                'display_name': 'Short Answer',
                'description': 'Answer the questions with words from the passage',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'default_instruction': 'Answer the questions below with words from the passage.',
                'default_answer_format': 'Choose NO MORE THAN THREE WORDS from the passage for each answer. Write your answers in boxes {question_range} on your answer sheet.',
                'template_examples': [
                    {
                        'question': 'What is the main topic of the passage?',
                        'answer': 'climate change',
                        'word_limit': 'NO MORE THAN THREE WORDS'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 'NO MORE THAN THREE WORDS',
                    'options': ['ONE WORD ONLY', 'NO MORE THAN TWO WORDS', 'NO MORE THAN THREE WORDS', 'NO MORE THAN FOUR WORDS']
                }
            }
        ]
        
        # Create each question type
        created_count = 0
        for question_type_data in question_types:
            # Check if it already exists
            if not QuestionTypeConfig.objects.filter(type_code=question_type_data['type_code']).exists():
                QuestionTypeConfig.objects.create(**question_type_data)
                created_count += 1
                self.stdout.write(f"Created: {question_type_data['display_name']}")
            else:
                self.stdout.write(f"Already exists: {question_type_data['display_name']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} question types!')
        )

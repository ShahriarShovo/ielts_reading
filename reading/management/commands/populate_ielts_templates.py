from django.core.management.base import BaseCommand
from reading.models import QuestionTypeConfig

class Command(BaseCommand):
    """
    Management command to populate QuestionTypeConfig with IELTS instruction templates.
    
    This command creates or updates QuestionTypeConfig entries with:
    - Default instruction text for each question type
    - Default answer format instructions
    - Template examples for frontend integration
    - Word limit rules and configurations
    
    Usage:
        python manage.py populate_ielts_templates
    """
    
    help = 'Populate QuestionTypeConfig with IELTS instruction templates'

    def handle(self, *args, **options):
        """
        Execute the command to populate IELTS templates.
        """
        self.stdout.write(self.style.SUCCESS('Starting IELTS template population...'))
        
        # Define IELTS templates for each question type
        templates = {
            'TFNG': {
                'display_name': 'True/False/Not Given',
                'description': 'Determine if statements are True, False, or Not Given based on the passage',
                'default_instruction': '{question_range}\nDo the following statements agree with the information given in Reading Passage 1?',
                'default_answer_format': 'In boxes {question_range} on your answer sheet, write\nTRUE if the statement agrees with the information\nFALSE if the statement contradicts the information\nNOT GIVEN if there is no information on this',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_tfng',
                        'display_name': 'Standard True/False/Not Given',
                        'description': 'Standard IELTS True/False/Not Given template',
                        'instruction_preview': 'Questions 1-7\nDo the following statements agree with the information given in Reading Passage 1?',
                        'answer_format_preview': 'In boxes 1-7 on your answer sheet, write\nTRUE if the statement agrees with the information\nFALSE if the statement contradicts the information\nNOT GIVEN if there is no information on this'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for True/False/Not Given questions'
                }
            },
            'MC': {
                'display_name': 'Multiple Choice',
                'description': 'Choose the correct answer from multiple options (A, B, C, D)',
                'default_instruction': '{question_range}\nChoose the correct letter, A, B, C or D.',
                'default_answer_format': 'Write the correct letter in boxes {question_range} on your answer sheet.',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_mc',
                        'display_name': 'Standard Multiple Choice',
                        'description': 'Standard IELTS Multiple Choice template',
                        'instruction_preview': 'Questions 8-13\nChoose the correct letter, A, B, C or D.',
                        'answer_format_preview': 'Write the correct letter in boxes 8-13 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for Multiple Choice questions'
                }
            },
            'SC': {
                'display_name': 'Sentence Completion',
                'description': 'Complete sentences with missing words from the passage',
                'default_instruction': '{question_range}\nComplete the sentences below.\nChoose ONE WORD ONLY from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Sentence Completion',
                        'description': 'Standard IELTS Sentence Completion template',
                        'instruction_preview': 'Questions 14-18\nComplete the sentences below.\nChoose ONE WORD ONLY from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 1,
                    'allowed_limits': [1, 2, 3],
                    'description': 'Typically ONE WORD ONLY for sentence completion'
                }
            },
            'SUMC': {
                'display_name': 'Summary Completion',
                'description': 'Complete a summary with missing words from the passage',
                'default_instruction': '{question_range}\nComplete the summary below.\nChoose ONE WORD ONLY from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Summary Completion',
                        'description': 'Standard IELTS Summary Completion template',
                        'instruction_preview': 'Questions 14-18\nComplete the summary below.\nChoose ONE WORD ONLY from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 1,
                    'allowed_limits': [1, 2, 3],
                    'description': 'Typically ONE WORD ONLY for summary completion'
                }
            },
            'NC': {
                'display_name': 'Note Completion',
                'description': 'Complete notes with missing information from the passage',
                'default_instruction': '{question_range}\nComplete the notes below.\nChoose ONE WORD ONLY from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Note Completion',
                        'description': 'Standard IELTS Note Completion template',
                        'instruction_preview': 'Questions 14-18\nComplete the notes below.\nChoose ONE WORD ONLY from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 1,
                    'allowed_limits': [1, 2, 3],
                    'description': 'Typically ONE WORD ONLY for note completion'
                }
            },
            'MH': {
                'display_name': 'Matching Headings',
                'description': 'Match paragraph headings to paragraphs in the passage',
                'default_instruction': '{question_range}\nMatch each paragraph with the correct heading.',
                'default_answer_format': 'Write the correct letter in boxes {question_range} on your answer sheet.',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_matching',
                        'display_name': 'Standard Matching Headings',
                        'description': 'Standard IELTS Matching Headings template',
                        'instruction_preview': 'Questions 19-25\nMatch each paragraph with the correct heading.',
                        'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for matching headings'
                }
            },
            'MP': {
                'display_name': 'Matching Paragraphs',
                'description': 'Match statements to paragraphs in the passage',
                'default_instruction': '{question_range}\nMatch each statement with the correct paragraph.',
                'default_answer_format': 'Write the correct letter in boxes {question_range} on your answer sheet.',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_matching',
                        'display_name': 'Standard Matching Paragraphs',
                        'description': 'Standard IELTS Matching Paragraphs template',
                        'instruction_preview': 'Questions 19-25\nMatch each statement with the correct paragraph.',
                        'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for matching paragraphs'
                }
            },
            'MF': {
                'display_name': 'Matching Features',
                'description': 'Match features or characteristics to options',
                'default_instruction': '{question_range}\nMatch each feature with the correct option.',
                'default_answer_format': 'Write the correct letter in boxes {question_range} on your answer sheet.',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_matching',
                        'display_name': 'Standard Matching Features',
                        'description': 'Standard IELTS Matching Features template',
                        'instruction_preview': 'Questions 19-25\nMatch each feature with the correct option.',
                        'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for matching features'
                }
            },
            'MSE': {
                'display_name': 'Matching Sentence Endings',
                'description': 'Complete sentences by matching endings to beginnings',
                'default_instruction': '{question_range}\nMatch each sentence ending with the correct beginning.',
                'default_answer_format': 'Write the correct letter in boxes {question_range} on your answer sheet.',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_matching',
                        'display_name': 'Standard Matching Sentence Endings',
                        'description': 'Standard IELTS Matching Sentence Endings template',
                        'instruction_preview': 'Questions 19-25\nMatch each sentence ending with the correct beginning.',
                        'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for matching sentence endings'
                }
            },
            'TC': {
                'display_name': 'Table Completion',
                'description': 'Complete a table with missing information from the passage',
                'default_instruction': '{question_range}\nComplete the table below.\nChoose ONE WORD ONLY from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Table Completion',
                        'description': 'Standard IELTS Table Completion template',
                        'instruction_preview': 'Questions 14-18\nComplete the table below.\nChoose ONE WORD ONLY from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 1,
                    'allowed_limits': [1, 2, 3],
                    'description': 'Typically ONE WORD ONLY for table completion'
                }
            },
            'FCC': {
                'display_name': 'Flow Chart Completion',
                'description': 'Complete a flow chart with missing steps from the passage',
                'default_instruction': '{question_range}\nComplete the flow chart below.\nChoose ONE WORD ONLY from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Flow Chart Completion',
                        'description': 'Standard IELTS Flow Chart Completion template',
                        'instruction_preview': 'Questions 14-18\nComplete the flow chart below.\nChoose ONE WORD ONLY from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 1,
                    'allowed_limits': [1, 2, 3],
                    'description': 'Typically ONE WORD ONLY for flow chart completion'
                }
            },
            'DL': {
                'display_name': 'Diagram Labelling',
                'description': 'Label parts of a diagram using information from the passage',
                'default_instruction': '{question_range}\nLabel the diagram below.\nChoose ONE WORD ONLY from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': True,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Diagram Labelling',
                        'description': 'Standard IELTS Diagram Labelling template',
                        'instruction_preview': 'Questions 14-18\nLabel the diagram below.\nChoose ONE WORD ONLY from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 1,
                    'allowed_limits': [1, 2, 3],
                    'description': 'Typically ONE WORD ONLY for diagram labelling'
                }
            },
            'SA': {
                'display_name': 'Short Answer',
                'description': 'Answer questions with short responses from the passage',
                'default_instruction': '{question_range}\nAnswer the questions below.\nChoose NO MORE THAN THREE WORDS from the passage for each answer.',
                'default_answer_format': 'Write your answers in boxes {question_range} on your answer sheet.',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': True,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_completion',
                        'display_name': 'Standard Short Answer',
                        'description': 'Standard IELTS Short Answer template',
                        'instruction_preview': 'Questions 14-18\nAnswer the questions below.\nChoose NO MORE THAN THREE WORDS from the passage for each answer.',
                        'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': 3,
                    'allowed_limits': [1, 2, 3, 4, 5],
                    'description': 'Typically NO MORE THAN THREE WORDS for short answers'
                }
            },
            'PFL': {
                'display_name': 'Pick from List',
                'description': 'Choose answers from a provided list of options',
                'default_instruction': '{question_range}\nChoose the correct answer from the list below.',
                'default_answer_format': 'Write the correct letter in boxes {question_range} on your answer sheet.',
                'requires_options': True,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_matching',
                        'display_name': 'Standard Pick from List',
                        'description': 'Standard IELTS Pick from List template',
                        'instruction_preview': 'Questions 19-25\nChoose the correct answer from the list below.',
                        'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for pick from list questions'
                }
            },
            'YNN': {
                'display_name': 'Yes/No/Not Given',
                'description': 'Determine if statements are Yes, No, or Not Given based on the passage',
                'default_instruction': '{question_range}\nDo the following statements agree with the information given in Reading Passage 1?',
                'default_answer_format': 'In boxes {question_range} on your answer sheet, write\nYES if the statement agrees with the information\nNO if the statement contradicts the information\nNOT GIVEN if there is no information on this',
                'requires_options': False,
                'requires_multiple_answers': False,
                'requires_word_limit': False,
                'requires_image': False,
                'template_examples': [
                    {
                        'name': 'standard_yng',
                        'display_name': 'Standard Yes/No/Not Given',
                        'description': 'Standard IELTS Yes/No/Not Given template',
                        'instruction_preview': 'Questions 1-7\nDo the following statements agree with the information given in Reading Passage 1?',
                        'answer_format_preview': 'In boxes 1-7 on your answer sheet, write\nYES if the statement agrees with the information\nNO if the statement contradicts the information\nNOT GIVEN if there is no information on this'
                    }
                ],
                'word_limit_rules': {
                    'default_limit': None,
                    'allowed_limits': [],
                    'description': 'No word limit for Yes/No/Not Given questions'
                }
            }
        }
        
        # Create or update QuestionTypeConfig entries
        created_count = 0
        updated_count = 0
        
        for type_code, config in templates.items():
            try:
                # Try to get existing config
                type_config, created = QuestionTypeConfig.objects.get_or_create(
                    type_code=type_code,
                    defaults=config
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"Created: {type_code} - {config['display_name']}")
                else:
                    # Update existing config with new template data
                    for key, value in config.items():
                        setattr(type_config, key, value)
                    type_config.save()
                    updated_count += 1
                    self.stdout.write(f"Updated: {type_code} - {config['display_name']}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error processing {type_code}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'IELTS template population completed!\n'
                f'Created: {created_count} templates\n'
                f'Updated: {updated_count} templates\n'
                f'Total: {created_count + updated_count} templates'
            )
        )

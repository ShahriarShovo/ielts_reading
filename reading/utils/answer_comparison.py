# ielts_reading/core/reading/utils/answer_comparison.py
# Answer comparison logic for IELTS Reading questions
# Handles different question types and answer formats

import logging

logger = logging.getLogger('reading')

def compare_answers(student_answers, correct_answers):
    """
    Compare student answers with correct answers and calculate results.
    
    This function:
    1. Compares each student answer with the correct answer
    2. Handles different answer formats (MCQ, T/F/NG, text, etc.)
    3. Calculates total correct answers
    4. Determines IELTS band score
    
    Args:
        student_answers: Dict of student answers {"1": "A", "2": "True", ...}
        correct_answers: Dict of correct answers from reading service
        
    Returns:
        dict: Results with scores, band, and detailed comparison
    """
    logger.info("=== COMPARING ANSWERS ===")
    
    total_questions = 40
    correct_count = 0
    answers_detail = []
    
    for question_num in range(1, total_questions + 1):
        question_str = str(question_num)
        student_answer = student_answers.get(question_str, '')
        correct_data = correct_answers.get(question_str, {})
        correct_answer = correct_data.get('correct_answer', '').strip()
        
        # Compare answers (handle list conversion inside compare_single_answer)
        is_correct = compare_single_answer(student_answer, correct_answer)
        
        if is_correct:
            correct_count += 1
        
        # Convert student answer to string for logging
        if isinstance(student_answer, list):
            student_answer_str = ','.join(student_answer)
        else:
            student_answer_str = str(student_answer) if student_answer else ''
        
        # Store detailed comparison
        answers_detail.append({
            'question_number': question_num,
            'student_answer': student_answer_str,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
            'question_type': correct_data.get('question_type', 'Unknown')
        })
        
        logger.debug(f"Q{question_num}: Student='{student_answer_str}' vs Correct='{correct_answer}' -> {is_correct}")
    
    # Calculate band score
    band_score = calculate_band_score(correct_count)
    
    logger.info(f"Results: {correct_count}/{total_questions} correct -> Band {band_score}")
    
    return {
        'total_questions': total_questions,
        'correct_answers': correct_count,
        'band_score': band_score,
        'answers_detail': answers_detail
    }

def compare_single_answer(student_answer, correct_answer):
    """
    Compare a single student answer with the correct answer.
    
    This function handles different answer formats:
    - Multiple choice (A, B, C, D)
    - Multiple answers (A,B or A, B or A;B)
    - True/False/Not Given (T/F/NG or True/False/Not Given)
    - Text answers (case-insensitive comparison)
    - List answers (['A', 'B'] for multiple choice)
    
    IMPORTANT: Student can give any answer or leave blank
    - If student answer matches teacher's correct answer = CORRECT
    - If student answer doesn't match teacher's answer = INCORRECT
    - If student leaves blank = INCORRECT
    - All student answers are saved for result review
    
    Args:
        student_answer: Student's submitted answer (can be any text, list, or blank)
        correct_answer: Correct answer from teacher
        
    Returns:
        bool: True if answer is correct, False otherwise
    """
    # Handle list answers (convert to string)
    if isinstance(student_answer, list):
        student_answer = ','.join(student_answer)
    
    # If student left blank, it's incorrect
    if not student_answer or student_answer.strip() == '':
        return False
    
    # If no correct answer available, it's incorrect
    if not correct_answer or correct_answer.strip() == '':
        return False
    
    # Normalize answers (remove extra spaces, convert to uppercase)
    student_normalized = normalize_answer(student_answer)
    correct_normalized = normalize_answer(correct_answer)
    
    # Direct comparison
    if student_normalized == correct_normalized:
        return True
    
    # Handle multiple choice with different separators
    if ',' in correct_normalized or ';' in correct_normalized:
        return compare_multiple_answers(student_normalized, correct_normalized)
    
    # Handle True/False/Not Given variations
    if is_tfng_question(correct_normalized):
        return compare_tfng_answers(student_normalized, correct_normalized)
    
    # Handle case-insensitive text comparison
    return student_normalized.lower() == correct_normalized.lower()

def normalize_answer(answer):
    """
    Normalize answer for comparison.
    
    Args:
        answer: Raw answer string
        
    Returns:
        str: Normalized answer
    """
    if not answer:
        return ''
    
    # Remove extra spaces and convert to uppercase
    normalized = answer.strip().upper()
    
    # Handle common variations
    normalized = normalized.replace('  ', ' ')  # Double spaces to single
    normalized = normalized.replace(' ,', ',')  # Space before comma
    normalized = normalized.replace(', ', ',')  # Space after comma
    
    return normalized

def compare_multiple_answers(student_answer, correct_answer):
    """
    Compare multiple choice answers with multiple correct options.
    
    Args:
        student_answer: Student's answer (e.g., "A,B" or "A, B")
        correct_answer: Correct answer (e.g., "A,B" or "A, B")
        
    Returns:
        bool: True if answers match, False otherwise
    """
    # Split answers by comma
    student_parts = [part.strip() for part in student_answer.split(',')]
    correct_parts = [part.strip() for part in correct_answer.split(',')]
    
    # Remove empty parts
    student_parts = [part for part in student_parts if part]
    correct_parts = [part for part in correct_parts if part]
    
    # Check if all parts match (order doesn't matter)
    if len(student_parts) != len(correct_parts):
        return False
    
    return sorted(student_parts) == sorted(correct_parts)

def is_tfng_question(answer):
    """
    Check if this is a True/False/Not Given question.
    
    Args:
        answer: Answer string to check
        
    Returns:
        bool: True if it's a T/F/NG question
    """
    tfng_values = ['TRUE', 'FALSE', 'NOT GIVEN', 'T', 'F', 'NG', 'YES', 'NO']
    return answer in tfng_values

def compare_tfng_answers(student_answer, correct_answer):
    """
    Compare True/False/Not Given answers.
    
    Args:
        student_answer: Student's answer
        correct_answer: Correct answer
        
    Returns:
        bool: True if answers match, False otherwise
    """
    # Mapping of variations
    tfng_mapping = {
        'TRUE': 'T',
        'FALSE': 'F', 
        'NOT GIVEN': 'NG',
        'YES': 'T',
        'NO': 'F'
    }
    
    # Normalize student answer
    student_normalized = tfng_mapping.get(student_answer, student_answer)
    
    # Normalize correct answer
    correct_normalized = tfng_mapping.get(correct_answer, correct_answer)
    
    return student_normalized == correct_normalized

def calculate_band_score(correct_count):
    """
    Calculate IELTS band score based on correct answers.
    
    IELTS Reading Band Score Conversion:
    39-40 = 9.0, 37-38 = 8.5, 35-36 = 8.0, 33-34 = 7.5,
    30-32 = 7.0, 27-29 = 6.5, 23-26 = 6.0, 19-22 = 5.5,
    15-18 = 5.0, 13-14 = 4.5, 10-12 = 4.0, 8-9 = 3.5,
    6-7 = 3.0, 5 = 2.5
    
    Args:
        correct_count: Number of correct answers (0-40)
        
    Returns:
        str: IELTS band score (e.g., "8.5", "7.0")
    """
    if correct_count >= 39:
        return "9.0"
    elif correct_count >= 37:
        return "8.5"
    elif correct_count >= 35:
        return "8.0"
    elif correct_count >= 33:
        return "7.5"
    elif correct_count >= 30:
        return "7.0"
    elif correct_count >= 27:
        return "6.5"
    elif correct_count >= 23:
        return "6.0"
    elif correct_count >= 19:
        return "5.5"
    elif correct_count >= 15:
        return "5.0"
    elif correct_count >= 13:
        return "4.5"
    elif correct_count >= 10:
        return "4.0"
    elif correct_count >= 8:
        return "3.5"
    elif correct_count >= 6:
        return "3.0"
    elif correct_count >= 5:
        return "2.5"
    else:
        return "2.0"

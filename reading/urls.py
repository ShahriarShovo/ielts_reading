from django.urls import path
from .views import (
    # REST API Views
    ReadingQuestionView,
    PassageView,
    ReadingTestView,
    QuestionTypeConfigView,
    QuestionTypeView,
    # NEW: IELTS Instruction System Views
    QuestionRangeView,
    QuestionRangeByPassageView,
    QuestionReorderView,
    QuestionReorderByPassageView,
    TemplateApplicationView,
    TemplateInfoView,
)

from .views.test_answers import get_test_answers
from .views.student_answer_views import (
    SubmitStudentAnswersView, 
    get_exam_results, 
    get_student_answers_for_comparison,
    update_student_answer_results
)

from .views.answer_comparison_views import (
    CompareAnswersView,
    BandScoreCalculationView
)

from .views.create_exam import RandomQuestionsView

app_name = 'reading'

urlpatterns = [
    # REST API URLs for Reading Tests (UUID-based)
    path('tests/', ReadingTestView.as_view(), name='api_tests'),
    path('tests/<uuid:test_id>/', ReadingTestView.as_view(), name='api_test_detail'),
    
    # REST API URLs for Reading Passages (UUID-based)
    path('passages/', PassageView.as_view(), name='api_passages'),
    path('passages/<uuid:passage_id>/', PassageView.as_view(), name='api_passage_detail'),
    
    # REST API URLs for Question Types (UUID-based)
    path('question-types/', QuestionTypeView.as_view(), name='api_question_types'),
    path('question-types/<uuid:question_type_id>/', QuestionTypeView.as_view(), name='api_question_type_detail'),
    
    # REST API URLs for Reading Questions (Legacy - for backward compatibility)
    path('questions/', ReadingQuestionView.as_view(), name='api_questions'),
    path('questions/<int:pk>/', ReadingQuestionView.as_view(), name='api_question_detail'),
    
    # REST API URLs for Question Type Configuration
    path('question-type-config/', QuestionTypeConfigView.as_view(), name='api_question_type_config'),
    path('question-type-config/<int:pk>/', QuestionTypeConfigView.as_view(), name='api_question_type_config_detail'),
    
    # NEW: IELTS Instruction System URLs
    
    # Question Range Management
    path('question-ranges/', QuestionRangeView.as_view(), name='api_question_ranges'),
    path('question-ranges/<int:passage_id>/', QuestionRangeByPassageView.as_view(), name='api_question_ranges_by_passage'),
    
    # Question Reordering
    path('question-reorder/', QuestionReorderView.as_view(), name='api_question_reorder'),
    path('question-reorder/<int:passage_id>/', QuestionReorderByPassageView.as_view(), name='api_question_reorder_by_passage'),
    
    # Template Application
    path('templates/apply/', TemplateApplicationView.as_view(), name='api_templates_apply'),
    path('templates/info/', TemplateInfoView.as_view(), name='api_templates_info'),
    
    
    
    path('random-questions/', RandomQuestionsView.as_view(), name='random-questions'),
    
    # Test Answers API (for Academiq integration)
    path('test-answers/<uuid:test_id>/', get_test_answers, name='test-answers'),
    
    # Student Answer Submission API
    path('submit-answers/', SubmitStudentAnswersView.as_view(), name='submit-answers'),
    path('exam-results/<str:session_id>/', get_exam_results, name='exam-results'),
    
    # Student Answer Comparison API (for Academiq)
    path('student-answers/<str:session_id>/', get_student_answers_for_comparison, name='student-answers-for-comparison'),
    path('update-results/<str:session_id>/', update_student_answer_results, name='update-student-results'),
    
    # Answer Comparison and Scoring API
    path('compare-answers/', CompareAnswersView.as_view(), name='compare-answers'),
    path('calculate-band-score/', BandScoreCalculationView.as_view(), name='calculate-band-score'),
]

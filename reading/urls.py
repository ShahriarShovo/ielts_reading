from django.urls import path
from .views import (
    # REST API Views
    ReadingQuestionView,
    PassageView,
    ReadingTestView,
    QuestionTypeConfigView,
    # NEW: IELTS Instruction System Views
    QuestionRangeView,
    QuestionRangeByPassageView,
    QuestionReorderView,
    QuestionReorderByPassageView,
    TemplateApplicationView,
    TemplateInfoView,
)

app_name = 'reading'

urlpatterns = [
    # REST API URLs for Reading Tests
    path('tests/', ReadingTestView.as_view(), name='api_tests'),
    path('tests/<int:pk>/', ReadingTestView.as_view(), name='api_test_detail'),
    
    # REST API URLs for Reading Passages
    path('passages/', PassageView.as_view(), name='api_passages'),
    path('passages/<int:pk>/', PassageView.as_view(), name='api_passage_detail'),
    
    # REST API URLs for Reading Questions
    path('questions/', ReadingQuestionView.as_view(), name='api_questions'),
    path('questions/<int:pk>/', ReadingQuestionView.as_view(), name='api_question_detail'),
    
    # REST API URLs for Question Type Configuration
    path('question-types/', QuestionTypeConfigView.as_view(), name='api_question_types'),
    path('question-types/<int:pk>/', QuestionTypeConfigView.as_view(), name='api_question_type_detail'),
    
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
]

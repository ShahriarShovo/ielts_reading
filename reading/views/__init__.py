# Views package
from .reading_question_view import ReadingQuestionView
from .passage_view import PassageView
from .reading_test_view import ReadingTestView
from .question_type_view import QuestionTypeView
from .question_type_config_view import QuestionTypeConfigView
# NEW: IELTS Instruction System Views
from .question_range_view import QuestionRangeView, QuestionRangeByPassageView
from .question_reorder_view import QuestionReorderView, QuestionReorderByPassageView
from .template_application_view import TemplateApplicationView, TemplateInfoView

__all__ = [
    # REST API Views
    'ReadingQuestionView',
    'PassageView',
    'ReadingTestView',
    'QuestionTypeView',
    'QuestionTypeConfigView',
    # NEW: IELTS Instruction System Views
    'QuestionRangeView',
    'QuestionRangeByPassageView',
    'QuestionReorderView',
    'QuestionReorderByPassageView',
    'TemplateApplicationView',
    'TemplateInfoView',
]

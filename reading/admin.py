from django.contrib import admin
from .models import ReadingTest, Passage, Question, QuestionType, QuestionTypeConfig
from .models.test_registry import TestRegistry
from .models.student_answer import StudentAnswer
from .models.submit_answer import SubmitAnswer

# Register your models here.

@admin.register(ReadingTest)
class ReadingTestAdmin(admin.ModelAdmin):
    list_display = ['test_name', 'source', 'organization_id', 'created_at']
    search_fields = ['test_name', 'source']
    list_filter = ['source', 'created_at']
    readonly_fields = ['test_id', 'created_at', 'updated_at']

@admin.register(Passage)
class PassageAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'test', 'order', 'get_question_type_count', 'get_total_question_count', 'get_question_range']
    list_filter = ['test', 'order']
    search_fields = ['title', 'subtitle', 'text', 'test__test_name']
    ordering = ['test', 'order']
    readonly_fields = ['passage_id', 'get_question_range']
    
    # ADD THIS FIELDSETS SECTION:
    fieldsets = (
        ('Basic Information', {
            'fields': ('test', 'title', 'subtitle', 'order')
        }),
        ('Content', {
            'fields': ('text', 'instruction')
        }),
        ('Question Information', {
            'fields': ('get_question_type_count', 'get_total_question_count', 'get_question_range'),
            'description': 'Automatically calculated question information'
        }),
        ('Paragraph Structure', {
            'fields': ('has_paragraphs', 'paragraph_count', 'paragraph_labels'),
            'classes': ('collapse',)
        }),
    )

    def get_question_type_count(self, obj):
        return obj.get_question_type_count()
    get_question_type_count.short_description = 'Question Types'

    def get_total_question_count(self, obj):
        return obj.get_total_question_count()
    get_total_question_count.short_description = 'Total Questions'

    def get_question_range(self, obj):
        try:
            start, end = obj.get_question_range()
            return f"{start}-{end}"
        except Exception as e:
            return f"Error: {str(e)[:20]}..."
    get_question_range.short_description = 'Question Range'

@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ['type', 'passage', 'order', 'get_dynamic_question_range', 'get_actual_question_count', 'get_question_count']
    list_filter = ['type', 'passage__test', 'order']
    search_fields = ['type', 'passage__title', 'instruction_template']
    ordering = ['passage', 'order']
    readonly_fields = ['question_type_id', 'get_processed_instruction', 'get_question_range', 'get_dynamic_question_range']

    fieldsets = (
        ('Basic Information', {
            'fields': ('passage', 'type', 'title', 'order', 'expected_range', 'actual_count')
        }),
        ('Dynamic Question Range', {
            'fields': ('get_dynamic_question_range', 'get_actual_question_count'),
            'description': 'Automatically calculated question range and count'
        }),
        ('Instruction Template', {
            'fields': ('instruction_template', 'get_processed_instruction'),
            'description': 'Use placeholders: {start}, {end}, {passage_number}'
        }),
        ('Questions Data', {
            'fields': ('questions_data', 'get_question_range'),
            'description': 'JSON array of individual questions'
        }),
    )

    def get_question_count(self, obj):
        return len(obj.questions_data) if obj.questions_data else 0
    get_question_count.short_description = 'Questions in Data'

    def get_actual_question_count(self, obj):
        return obj.calculate_question_count()
    get_actual_question_count.short_description = 'Actual Count'

    def get_processed_instruction(self, obj):
        return obj.get_processed_instruction()
    get_processed_instruction.short_description = 'Processed Instruction'

    def get_question_range(self, obj):
        start, end = obj.get_question_range()
        return f"{start}-{end}"
    get_question_range.short_description = 'Question Range'

    def get_dynamic_question_range(self, obj):
        try:
            start, end = obj.get_dynamic_question_range()
            return f"{start}-{end}"
        except Exception as e:
            return f"Error: {str(e)[:20]}..."
    get_dynamic_question_range.short_description = 'Dynamic Range'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'question_type', 'number', 'answer', 'points', 'get_full_question_number']
    list_filter = ['question_type__type', 'question_type__passage__test']
    search_fields = ['question_text', 'question_type__type', 'answer']
    ordering = ['question_type', 'number']
    readonly_fields = ['question_id', 'created_at', 'updated_at', 'get_full_question_number']

    fieldsets = (
        ('Basic Information', {
            'fields': ('question_type', 'question_text', 'number', 'answer', 'points')
        }),
        ('Options & Configuration', {
            'fields': ('options', 'word_limit'),
            'description': 'Options for MCQ questions, word limit for completion questions'
        }),
        ('Additional Information', {
            'fields': ('explanation', 'image'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('get_full_question_number', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_question_number(self, obj):
        return obj.get_full_question_number()
    get_full_question_number.short_description = 'Full Question Number'

@admin.register(QuestionTypeConfig)
class QuestionTypeConfigAdmin(admin.ModelAdmin):
    list_display = ['type_code', 'display_name', 'is_active', 'requires_options', 'requires_word_limit']
    list_filter = ['is_active', 'requires_options', 'requires_multiple_answers', 'requires_word_limit', 'requires_image']
    search_fields = ['type_code', 'display_name', 'description']
    ordering = ['display_name']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('type_code', 'display_name', 'description', 'is_active')
        }),
        ('Field Requirements', {
            'fields': ('requires_options', 'requires_multiple_answers', 'requires_word_limit', 'requires_image'),
            'description': 'Configuration flags for field requirements'
        }),
        ('IELTS Template System', {
            'fields': ('default_instruction', 'default_answer_format', 'template_examples', 'word_limit_rules'),
            'classes': ('collapse',),
            'description': 'IELTS instruction templates and configuration'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['default_instruction'].help_text = "Default IELTS instruction text with {question_range} placeholder"
        form.base_fields['default_answer_format'].help_text = "Default answer format with {question_range} placeholder"
        form.base_fields['template_examples'].help_text = "JSON array of template examples for frontend integration"
        form.base_fields['word_limit_rules'].help_text = "Word limit rules and configurations in JSON format"
        return form
    
    
admin.site.register(TestRegistry)
admin.site.register(StudentAnswer)
admin.site.register(SubmitAnswer)

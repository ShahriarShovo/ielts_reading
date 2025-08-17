from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from reading.models import Question, QuestionTypeConfig
from reading.serializers.template_application import TemplateApplicationSerializer, TemplateInfoSerializer
from reading.permissions import SharedAuthPermission
import logging

logger = logging.getLogger('reading')

class TemplateApplicationView(APIView):
    """
    TemplateApplicationView: Handles template application to questions.
    
    This view provides endpoints for:
    1. Applying IELTS instruction templates to questions
    2. Auto-populating instruction and answer format fields
    3. Supporting custom template modifications
    4. Getting available templates for question types
    
    Supported Operations:
    - POST: Apply a template to a question
    - GET: Get available templates for a question type
    
    Authentication: Shared Authentication Service (JWT tokens verified via auth project)
    Permission: Users can only access their organization's data
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def post(self, request):
        """
        Apply a template to a question.
        
        This method:
        1. Validates the template application request data
        2. Checks user permissions for the question
        3. Applies the specified template to the question
        4. Auto-populates instruction and answer format fields
        5. Returns the updated question data
        
        Args:
            request: HTTP request object with template application data and JWT token
            
        Returns:
            Response with updated question data (200) or error responses
        """
        logger.info("=== TEMPLATE APPLICATION POST METHOD CALLED ===")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Validate the template application request data
            template_serializer = TemplateApplicationSerializer(data=request.data)
            if template_serializer.is_valid():
                question_id = request.data.get('question_id')
                template_name = request.data.get('template_name')
                custom_instruction = request.data.get('custom_instruction')
                custom_answer_format = request.data.get('custom_answer_format')
                
                # Get the question and validate user permissions
                try:
                    question = Question.objects.get(id=question_id)
                except Question.DoesNotExist:
                    logger.error(f"Question with ID {question_id} not found")
                    return Response(
                        {'error': 'Question not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Check if user has permission to edit this question (same organization)
                user_org_id = getattr(request, 'organization_id', None)
                if question.organization_id != str(user_org_id):
                    logger.error(f"Permission denied: User org {user_org_id} cannot edit question org {question.organization_id}")
                    return Response(
                        {'error': 'Permission denied'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Apply the template to the question
                result = template_serializer.apply_template(
                    question_id=question_id,
                    template_name=template_name,
                    custom_instruction=custom_instruction,
                    custom_answer_format=custom_answer_format
                )
                
                logger.info(f"Template applied successfully: {result}")
                return Response(result, status=status.HTTP_200_OK)
            else:
                logger.error(f"Template serializer validation failed: {template_serializer.errors}")
                return Response(template_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """
        Get available templates for a question type.
        
        This method:
        1. Gets question_type from query parameters
        2. Returns available templates for the specified question type
        3. Includes template previews and descriptions
        
        Args:
            request: HTTP request object with question_type query parameter and JWT token
            
        Returns:
            Response with available templates (200) or error responses
        """
        logger.info("=== TEMPLATE APPLICATION GET METHOD CALLED ===")
        
        try:
            # Get question_type from query parameters
            question_type = request.query_params.get('question_type')
            if not question_type:
                logger.error("Question type not provided in query parameters")
                return Response(
                    {'error': 'Question type is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get available templates for the question type
            templates = self._get_templates_for_question_type(question_type)
            
            logger.info(f"Retrieved {len(templates)} templates for question type {question_type}")
            return Response({
                'question_type': question_type,
                'templates': templates
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_templates_for_question_type(self, question_type):
        """
        Get available templates for a specific question type.
        
        Args:
            question_type (str): The question type to get templates for
            
        Returns:
            list: List of available templates for the question type
        """
        templates = []
        
        # Standard templates based on question type
        if question_type == 'TFNG':
            templates = [
                {
                    'name': 'standard_tfng',
                    'display_name': 'Standard True/False/Not Given',
                    'description': 'Standard IELTS True/False/Not Given template with dynamic question range',
                    'instruction_preview': 'Questions 1-7\nDo the following statements agree with the information given in Reading Passage 1?',
                    'answer_format_preview': 'In boxes 1-7 on your answer sheet, write\nTRUE if the statement agrees with the information\nFALSE if the statement contradicts the information\nNOT GIVEN if there is no information on this',
                    'question_type': 'TFNG',
                    'is_customizable': True
                }
            ]
        elif question_type == 'MC':
            templates = [
                {
                    'name': 'standard_mc',
                    'display_name': 'Standard Multiple Choice',
                    'description': 'Standard IELTS Multiple Choice template with dynamic question range',
                    'instruction_preview': 'Questions 8-13\nChoose the correct letter, A, B, C or D.',
                    'answer_format_preview': 'Write the correct letter in boxes 8-13 on your answer sheet.',
                    'question_type': 'MC',
                    'is_customizable': True
                }
            ]
        elif question_type in ['SC', 'SUMC', 'NC', 'TC', 'FCC']:
            templates = [
                {
                    'name': 'standard_completion',
                    'display_name': 'Standard Completion',
                    'description': 'Standard IELTS Completion template with dynamic question range',
                    'instruction_preview': 'Questions 14-18\nComplete the following.\nChoose ONE WORD ONLY from the passage for each answer.',
                    'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.',
                    'question_type': question_type,
                    'is_customizable': True
                }
            ]
        elif question_type in ['MH', 'MP', 'MF', 'MSE']:
            templates = [
                {
                    'name': 'standard_matching',
                    'display_name': 'Standard Matching',
                    'description': 'Standard IELTS Matching template with dynamic question range',
                    'instruction_preview': 'Questions 19-25\nMatch the following.',
                    'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.',
                    'question_type': question_type,
                    'is_customizable': True
                }
            ]
        
        # Add custom template option
        templates.append({
            'name': 'custom',
            'display_name': 'Custom Template',
            'description': 'Create a custom template with your own instruction and answer format',
            'instruction_preview': 'Custom instruction text...',
            'answer_format_preview': 'Custom answer format...',
            'question_type': question_type,
            'is_customizable': True
        })
        
        return templates


class TemplateInfoView(APIView):
    """
    TemplateInfoView: Get detailed template information.
    
    This view provides detailed information about available templates
    and their configurations for frontend integration.
    """
    permission_classes = [SharedAuthPermission]
    authentication_classes = []

    def get(self, request):
        """
        Get detailed template information for all question types.
        
        Args:
            request: HTTP request object with JWT token
            
        Returns:
            Response with detailed template information (200) or error responses
        """
        logger.info("=== TEMPLATE INFO GET METHOD CALLED ===")
        
        try:
            # Get all question type configurations
            type_configs = QuestionTypeConfig.objects.filter(is_active=True)
            
            # Create template information for each question type
            template_info = {}
            for type_config in type_configs:
                templates = self._get_templates_for_question_type(type_config.type_code)
                template_info[type_config.type_code] = {
                    'display_name': type_config.display_name,
                    'description': type_config.description,
                    'templates': templates,
                    'default_instruction': type_config.default_instruction,
                    'default_answer_format': type_config.default_answer_format,
                    'template_examples': type_config.get_template_examples(),
                    'word_limit_rules': type_config.get_word_limit_rules()
                }
            
            logger.info(f"Retrieved template information for {len(template_info)} question types")
            return Response({
                'template_info': template_info,
                'total_question_types': len(template_info)
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting template information: {str(e)}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_templates_for_question_type(self, question_type):
        """
        Get available templates for a specific question type.
        
        Args:
            question_type (str): The question type to get templates for
            
        Returns:
            list: List of available templates for the question type
        """
        templates = []
        
        # Standard templates based on question type
        if question_type == 'TFNG':
            templates = [
                {
                    'name': 'standard_tfng',
                    'display_name': 'Standard True/False/Not Given',
                    'description': 'Standard IELTS True/False/Not Given template with dynamic question range',
                    'instruction_preview': 'Questions 1-7\nDo the following statements agree with the information given in Reading Passage 1?',
                    'answer_format_preview': 'In boxes 1-7 on your answer sheet, write\nTRUE if the statement agrees with the information\nFALSE if the statement contradicts the information\nNOT GIVEN if there is no information on this',
                    'question_type': 'TFNG',
                    'is_customizable': True
                }
            ]
        elif question_type == 'MC':
            templates = [
                {
                    'name': 'standard_mc',
                    'display_name': 'Standard Multiple Choice',
                    'description': 'Standard IELTS Multiple Choice template with dynamic question range',
                    'instruction_preview': 'Questions 8-13\nChoose the correct letter, A, B, C or D.',
                    'answer_format_preview': 'Write the correct letter in boxes 8-13 on your answer sheet.',
                    'question_type': 'MC',
                    'is_customizable': True
                }
            ]
        elif question_type in ['SC', 'SUMC', 'NC', 'TC', 'FCC']:
            templates = [
                {
                    'name': 'standard_completion',
                    'display_name': 'Standard Completion',
                    'description': 'Standard IELTS Completion template with dynamic question range',
                    'instruction_preview': 'Questions 14-18\nComplete the following.\nChoose ONE WORD ONLY from the passage for each answer.',
                    'answer_format_preview': 'Write your answers in boxes 14-18 on your answer sheet.',
                    'question_type': question_type,
                    'is_customizable': True
                }
            ]
        elif question_type in ['MH', 'MP', 'MF', 'MSE']:
            templates = [
                {
                    'name': 'standard_matching',
                    'display_name': 'Standard Matching',
                    'description': 'Standard IELTS Matching template with dynamic question range',
                    'instruction_preview': 'Questions 19-25\nMatch the following.',
                    'answer_format_preview': 'Write the correct letter in boxes 19-25 on your answer sheet.',
                    'question_type': question_type,
                    'is_customizable': True
                }
            ]
        
        # Add custom template option
        templates.append({
            'name': 'custom',
            'display_name': 'Custom Template',
            'description': 'Create a custom template with your own instruction and answer format',
            'instruction_preview': 'Custom instruction text...',
            'answer_format_preview': 'Custom answer format...',
            'question_type': question_type,
            'is_customizable': True
        })
        
        return templates

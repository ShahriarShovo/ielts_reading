# reading/views/answer_comparison_views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import authentication_classes
from django.shortcuts import get_object_or_404
from ..models import SubmitAnswer
from ..services.answer_comparison_service import AnswerComparisonService

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@authentication_classes([])
@permission_classes([AllowAny])
def compare_submission(request):
    """Compare student submission with correct answers."""
    try:
        # Accept either submit_id or session_id
        submit_id = request.data.get('submit_id')
        session_id = request.data.get('session_id')
        
        if not submit_id and not session_id:
            return Response(
                {'error': 'Either submit_id or session_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find submission by submit_id or session_id
        if submit_id:
            submit_answer = get_object_or_404(SubmitAnswer, submit_id=submit_id)
        else:
            submit_answer = get_object_or_404(SubmitAnswer, session_id=session_id)
        
        # Check if already processed
        if submit_answer.is_processed:
            return Response(
                {'error': 'Submission already processed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = AnswerComparisonService()
        result = service.compare_submission(submit_answer)
        
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        
    except SubmitAnswer.DoesNotExist:
        return Response(
            {'error': 'Submission not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny]) 
def get_comparison_summary(request, submit_id):
    """
    Get comparison summary for a submission.
    
    GET /api/reading/comparison-summary/{submit_id}/
    
    Response:
    {
        "success": true,
        "ielts_band_score": 7.0,
        "question_type_breakdown": {...}
    }
    """
    try:
        submit_answer = get_object_or_404(SubmitAnswer, submit_id=submit_id)
        service = AnswerComparisonService()
        summary = service.get_comparison_summary(submit_answer)
        
        return Response(summary, status=status.HTTP_200_OK)
        
    except SubmitAnswer.DoesNotExist:
        return Response(
            {'error': 'Submission not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny]) 
def batch_compare_submissions(request):
    """
    Compare multiple submissions at once.
    
    POST /api/reading/batch-compare/
    
    Request Body:
    {
        "submit_ids": ["uuid1", "uuid2", "uuid3"]
    }
    
    Response:
    {
        "total_processed": 3,
        "results": [...]
    }
    """
    try:
        submit_ids = request.data.get('submit_ids', [])
        
        if not submit_ids:
            return Response(
                {'error': 'submit_ids list is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(submit_ids, list):
            return Response(
                {'error': 'submit_ids must be a list'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        errors = []
        
        service = AnswerComparisonService()
        
        for submit_id in submit_ids:
            try:
                submit_answer = SubmitAnswer.objects.get(submit_id=submit_id)
                
                # Check if already processed
                if submit_answer.is_processed:
                    errors.append({
                        'submit_id': submit_id,
                        'error': 'Already processed'
                    })
                    continue
                
                result = service.compare_submission(submit_answer)
                results.append(result)
                
            except SubmitAnswer.DoesNotExist:
                errors.append({
                    'submit_id': submit_id,
                    'error': 'Submission not found'
                })
            except Exception as e:
                errors.append({
                    'submit_id': submit_id,
                    'error': str(e)
                })
        
        return Response({
            'total_processed': len(results),
            'total_errors': len(errors),
            'results': results,
            'errors': errors
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
@permission_classes([AllowAny]) 
def get_ielts_band_score(request, submit_id):
    """
    Get IELTS band score for a submission.
    
    GET /api/reading/ielts-band-score/{submit_id}/
    
    Response:
    {
        "submit_id": "uuid",
        "ielts_band_score": 7.0,
        "correct_answers": 28,
        "total_questions": 40
    }
    """
    try:
        submit_answer = get_object_or_404(SubmitAnswer, submit_id=submit_id)
        service = AnswerComparisonService()
        summary = service.get_comparison_summary(submit_answer)
        
        if summary['success']:
            return Response({
                'submit_id': submit_id,
                'ielts_band_score': summary['ielts_band_score'],
                'correct_answers': summary['correct_answers'],
                'total_questions': summary['total_questions'],
                'percentage': summary['percentage']
            }, status=status.HTTP_200_OK)
        else:
            return Response(summary, status=status.HTTP_400_BAD_REQUEST)
        
    except SubmitAnswer.DoesNotExist:
        return Response(
            {'error': 'Submission not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
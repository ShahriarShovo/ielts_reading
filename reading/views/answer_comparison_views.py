# reading/views/answer_comparison_views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ..models import SubmitAnswer
from ..services.answer_comparison_service import AnswerComparisonService
from reading.permissions import SharedAuthPermission
import logging

# Set up logging
logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class CompareSubmissionView(APIView):
    """
    Compare student submission with correct answers.
    
    POST /api/reading/compare-submission/
    
    Request Body:
    {
        "submit_id": "uuid" OR "session_id": "36"
    }
    
    Headers:
    Authorization: Bearer {jwt_token}
    X-Organization-ID: {organization_id}
    """
    
    permission_classes = [SharedAuthPermission]
    authentication_classes = []
    
    def post(self, request):
        """Compare submission and return results."""
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
            # if submit_answer.is_processed:
            #     return Response(
            #         {'error': 'Submission already processed'}, 
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            
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
            logger.error(f"Error in CompareSubmissionView: {str(e)}")
            return Response(
                {'error': f'Server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class GetComparisonSummaryView(APIView):
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
    
    permission_classes = [AllowAny]  # Allow public access for now
    
    def get(self, request, submit_id):
        """Get comparison summary for a submission."""
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
            logger.error(f"Error in GetComparisonSummaryView: {str(e)}")
            return Response(
                {'error': f'Server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class BatchCompareSubmissionsView(APIView):
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
    
    permission_classes = [SharedAuthPermission]
    
    def post(self, request):
        """Process multiple submissions in batch."""
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
            
            service = AnswerComparisonService()
            results = []
            total_processed = 0
            
            for submit_id in submit_ids:
                try:
                    submit_answer = get_object_or_404(SubmitAnswer, submit_id=submit_id)
                    
                    # Check if already processed
                    # if submit_answer.is_processed:
                    #     results.append({
                    #         'submit_id': submit_id,
                    #         'status': 'skipped',
                    #         'message': 'Already processed'
                    #     })
                    #     continue
                    
                    # Process submission
                    result = service.compare_submission(submit_answer)
                    results.append({
                        'submit_id': submit_id,
                        'status': 'success' if result['success'] else 'failed',
                        'result': result
                    })
                    total_processed += 1
                    
                except SubmitAnswer.DoesNotExist:
                    results.append({
                        'submit_id': submit_id,
                        'status': 'error',
                        'message': 'Submission not found'
                    })
                except Exception as e:
                    results.append({
                        'submit_id': submit_id,
                        'status': 'error',
                        'message': str(e)
                    })
            
            return Response({
                'total_processed': total_processed,
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in BatchCompareSubmissionsView: {str(e)}")
            return Response(
                {'error': f'Server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class GetSubmissionStatusView(APIView):
    """
    Get the processing status of a submission.
    
    GET /api/reading/submission-status/{submit_id}/
    
    Response:
    {
        "submit_id": "uuid",
        "is_processed": true/false,
        "processed_at": "timestamp",
        "status": "completed/pending/error"
    }
    """
    
    permission_classes = [AllowAny]  # Allow public access for status checks
    
    def get(self, request, submit_id):
        """Get submission processing status."""
        try:
            submit_answer = get_object_or_404(SubmitAnswer, submit_id=submit_id)
            
            status_info = {
                'submit_id': submit_id,
                # 'is_processed': submit_answer.is_processed,
                'processed_at': submit_answer.processed_at if hasattr(submit_answer, 'processed_at') else None,
                # 'status': 'completed' if submit_answer.is_processed else 'pending'
            }
            
            return Response(status_info, status=status.HTTP_200_OK)
            
        except SubmitAnswer.DoesNotExist:
            return Response(
                {'error': 'Submission not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error in GetSubmissionStatusView: {str(e)}")
            return Response(
                {'error': f'Server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
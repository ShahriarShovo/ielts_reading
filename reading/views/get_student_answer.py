from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging
from reading.models.submit_answer import SubmitAnswer
from reading.serializers.get_student_answer import SubmitAnswerSerializer

# Set up logging for debugging and monitoring
logger = logging.getLogger(__name__)

class StudentAnswer(APIView):
    
    authentication_classes = []   # 👈 Disable auth for this view
    permission_classes = []       # 👈 Disable permission checks
    
    def get(self, request, session_id):
        submission = get_object_or_404(SubmitAnswer, session_id=session_id)
        serializer = SubmitAnswerSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)
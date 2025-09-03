from rest_framework import serializers
from reading.models.submit_answer import SubmitAnswer
from reading.models.student_answer import StudentAnswer

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = '__all__'

class SubmitAnswerSerializer(serializers.ModelSerializer):
    student_answers = StudentAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = SubmitAnswer
        fields = '__all__'

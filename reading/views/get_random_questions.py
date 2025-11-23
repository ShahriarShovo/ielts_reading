# =============================================================================
# RANDOM QUESTIONS VIEW
# =============================================================================
# This view handles random ReadingTest retrieval for student exams.
# It returns random ReadingTests with their associated Passages and QuestionTypes
# for a specific organization, maintaining the hierarchical structure.
# =============================================================================

import random
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from reading.models.reading_test import ReadingTest
from reading.models.passage import Passage
from reading.models.question_type import QuestionType
from reading.permissions import SharedAuthPermission
from reading.serializers.reading_test import ReadingTestSerializer
from reading.serializers.passage import PassageSerializer
from reading.serializers.question_type import QuestionTypeSerializer

# Set up logging for debugging and monitoring
logger = logging.getLogger('reading')

class RandomQuestionsView(APIView):
    """
    RandomQuestionsView: Returns random ReadingTests with Passages and QuestionTypes for an organization.

    This view:
    1. Receives organization_id and optional count from query parameters
    2. Validates permission using SharedAuthPermission
    3. Returns random ReadingTests that contain Passages and QuestionTypes
    4. Maintains the hierarchical structure (Test -> Passage -> QuestionTypes)
    """
    permission_classes = [SharedAuthPermission]  # Enable authentication for production
    authentication_classes = []  # Disable default JWT authentication since we use custom permission

    def get(self, request):
        """
        Get random ReadingTests with their Passages and QuestionTypes for the user's organization.

        Args:
            request: HTTP request object with JWT token and organization_id query parameter
                    Optional query param: count (default = 1)

        Returns:
            Response with random ReadingTests containing Passages and QuestionTypes
        """
        logger.info("=== RANDOM QUESTIONS GET METHOD CALLED ===")
        logger.info(f"Request user_id: {getattr(request, 'user_id', 'Not set')}")
        logger.info(f"Request organization_id: {getattr(request, 'organization_id', 'Not set')}")
        logger.info(f"Query params: {request.query_params}")

        try:
            # =============================================================================
            # STEP 1: VALIDATE ORGANIZATION ID
            # =============================================================================
            # Get organization_id from query parameters
            organization_id = request.query_params.get('organization_id')
            logger.info(f"Organization ID from query params: {organization_id}")
            if not organization_id:
                logger.error("Organization ID not provided in query parameters")
                return Response({'error': 'Organization ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            # =============================================================================
            # STEP 2: VALIDATE PERMISSIONS
            # =============================================================================
            # Check if user has permission to view this organization's data
            user_org_id = getattr(request, 'organization_id', None)
            logger.info(f"User org ID: {user_org_id}, Requested org ID: {organization_id}")
            logger.info(f"Permission check: {str(user_org_id)} != {organization_id} = {str(user_org_id) != organization_id}")
            if str(user_org_id) != organization_id:
                logger.error(f"Permission denied: User org {user_org_id} cannot view org {organization_id}")
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            # =============================================================================
            # STEP 3: VALIDATE COUNT PARAMETER
            # =============================================================================
            # Get count from query params (default = 1)
            count = request.query_params.get('count', 1)
            try:
                count = int(count)
                if count <= 0:
                    raise ValueError
            except ValueError:
                logger.error("Invalid count value provided")
                return Response({'error': 'Count must be a positive integer'}, status=status.HTTP_400_BAD_REQUEST)

            # =============================================================================
            # STEP 4: RETRIEVE READING TESTS
            # =============================================================================
            # Get all tests for the organization
            all_tests = ReadingTest.objects.filter(organization_id=organization_id)
            
            # Check if any tests exist
            if not all_tests.exists():
                logger.error(f"No reading tests found for organization {organization_id}")
                return Response({
                    'error': 'No reading tests available for this organization'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Select random tests (up to count)
            available_tests = list(all_tests)
            if len(available_tests) > count:
                random_reading = random.sample(available_tests, count)
            else:
                random_reading = available_tests
            
            # Filter tests that have at least one passage (safety check)
            tests_with_passages = []
            for test in random_reading:
                passage_count = Passage.objects.filter(test=test).count()
                if passage_count > 0:
                    tests_with_passages.append(test)
                else:
                    # Log warning for tests without passages
                    logger.warning(f"Test {test.test_id} has no passages - skipping")
            
            if not tests_with_passages:
                logger.error(f"No reading tests with passages found for organization {organization_id}")
                return Response({
                    'error': 'No reading tests with passages available for this organization',
                    'details': 'All available tests lack passages'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Use the selected tests
            random_reading = tests_with_passages
            reading_serializer = ReadingTestSerializer(random_reading, many=True)
            
            # =============================================================================
            # STEP 5: GET COMPLETE DATA
            # =============================================================================
            # Get complete data for each reading test
            complete_reading_data = []
            for i, reading_test in enumerate(random_reading):
                # Get passages for this test
                passages = Passage.objects.filter(test=reading_test).order_by('order')
                passages_serializer = PassageSerializer(passages, many=True)
                
                # Get questions for each passage
                complete_passages = []
                for j, passage in enumerate(passages):
                    # Get question types for this passage
                    question_types = QuestionType.objects.filter(passage=passage).order_by('order')
                    
                    # Update student_range for all question types to ensure correct numbering
                    for question_type in question_types:
                        question_type.update_student_range()
                    
                    question_types_serializer = QuestionTypeSerializer(question_types, many=True)
                    
                    passage_data = passages_serializer.data[j]
                    passage_data['question_types'] = question_types_serializer.data
                    complete_passages.append(passage_data)
                
                # Combine test data with passages and questions
                test_data = reading_serializer.data[i]
                test_data['passages'] = complete_passages
                complete_reading_data.append(test_data)

            logger.info(f"Retrieved {len(complete_reading_data)} complete reading tests with passages and questions for organization {organization_id} (filtered from {len(tests_with_passages)} tests with passages)")

            # =============================================================================
            # STEP 6: RETURN SUCCESS RESPONSE
            # =============================================================================
            # Return structured JSON with complete data
            return Response({
                "reading": complete_reading_data,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # =============================================================================
            # STEP 7: ERROR HANDLING
            # =============================================================================
            logger.error(f"Error retrieving random questions: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



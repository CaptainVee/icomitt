from django.utils import timezone
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Goal
from core_apps.common.mixins import StandardResponseMixin
from core_apps.verifications.models import HumanVerifier
from .serializers import (
    GoalSerializer, GoalBasicInfoSerializer, GoalHumanVerifierInfoSerializer,
    GoalStakeInfoSerializer, GoalVerificationInfoSerializer)



class BaseGoalCreationView(StandardResponseMixin, APIView):
    """Base class for goal creation steps with common functionality"""
    permission_classes = [IsAuthenticated]
    step_number = None
    required_previous_step = None
    
    def get_cache_key(self):
        return f"goal_creation_{self.request.user.id}"
    
    def get_goal_data(self):
        return cache.get(self.get_cache_key()) or {}
    
    def save_goal_data(self, data):
        cache_key = self.get_cache_key()
        goal_data = self.get_goal_data()
        goal_data.update(data)
        goal_data['step'] = self.step_number
        goal_data['user_id'] = self.request.user.id
        
        # Convert date/time objects to strings for JSON serialization
        if 'start_date' in goal_data and hasattr(goal_data['start_date'], 'isoformat'):
            goal_data['start_date'] = goal_data['start_date'].isoformat()
        if 'end_date' in goal_data and hasattr(goal_data['end_date'], 'isoformat'):
            goal_data['end_date'] = goal_data['end_date'].isoformat()
        if 'time_of_day' in goal_data and hasattr(goal_data['time_of_day'], 'isoformat'):
            goal_data['time_of_day'] = goal_data['time_of_day'].isoformat()
        
        cache.set(cache_key, goal_data, timeout=3600)
        return goal_data
    
    def validate_previous_steps(self):
        if self.required_previous_step:
            goal_data = self.get_goal_data()
            if not goal_data or goal_data.get('step', 0) < self.required_previous_step:
                return False
        return True
    
    def get_next_step(self, current_data):
        """Override in subclasses for custom next step logic"""
        return self.step_number + 1


class GoalStep1BasicInfoView(BaseGoalCreationView):
    """Step 1: Capture basic goal information"""
    step_number = 1
    
    def post(self, request):
        serializer = GoalBasicInfoSerializer(data=request.data)
        if serializer.is_valid():
            self.save_goal_data(serializer.validated_data)
            return Response({
                'success': True,
                'message': 'Basic information saved successfully',
                'data': serializer.validated_data,
                'next_step': self.get_next_step(serializer.validated_data)
            }, status=status.HTTP_200_OK)
        
        return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class GoalStep2VerificationInfoView(BaseGoalCreationView):
    """Step 2: Capture verification method and type"""
    step_number = 2
    required_previous_step = 1
    
    def post(self, request):
        if not self.validate_previous_steps():
            return self.error_response('Please complete previous steps first', status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = GoalVerificationInfoSerializer(data=request.data)
        if serializer.is_valid():
            self.save_goal_data(serializer.validated_data)
            return Response({
                'success': True,
                'message': 'Verification information saved successfully',
                'data': serializer.validated_data,
                'next_step': self.get_next_step(serializer.validated_data)
            }, status=status.HTTP_200_OK)
        
        return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
    
    def get_next_step(self, current_data):
        # Skip human verifier step if AI verification
        if current_data.get('verification_type') == 'ai':
            return 5  # Skip to summary
        return 4  # Go to human verifier step


class GoalStep3HumanVerifiersView(BaseGoalCreationView):
    """Step 3: Add human verifiers"""
    step_number = 3
    required_previous_step = 2
    
    def post(self, request):
        if not self.validate_previous_steps():
            return self.error_response('Please complete previous steps first', status_code=status.HTTP_400_BAD_REQUEST)
        
        goal_data = self.get_goal_data()
        if goal_data.get('verification_type') != 'human':
            return self.error_response('This step is only for human verification goals', status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = GoalHumanVerifierInfoSerializer(data=request.data)
        if serializer.is_valid():
            self.save_goal_data(serializer.validated_data)
            return Response({
                'success': True,
                'message': 'Human verifiers saved successfully',
                'data': serializer.validated_data,
                'next_step': self.get_next_step(serializer.validated_data)
            }, status=status.HTTP_200_OK)
        
        return self.error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoalStep4StakeInfoView(BaseGoalCreationView):
    """Step 4: Capture stake amount and payment method"""
    step_number = 4
    required_previous_step = 3
    
    def post(self, request):
        if not self.validate_previous_steps():
            return self.error_response('Please complete step 1 first', status_code=status.HTTP_400_BAD_REQUEST)
        
        serializer = GoalStakeInfoSerializer(data=request.data)
        if serializer.is_valid():
            self.save_goal_data(serializer.validated_data)
            return Response({
                'success': True,
                'message': 'Stake information saved successfully',
                'data': serializer.validated_data,
                'next_step': self.get_next_step(serializer.validated_data)
            }, status=status.HTTP_200_OK)
        
        return self.error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

class GoalStep5SummaryView(BaseGoalCreationView):
    """Step 5: Show summary for confirmation"""
    step_number = 5
    required_previous_step = 4  # Can come from either step 3 (AI) or 4 (Human)
    
    def get(self, request):
        goal_data = self.get_goal_data()
        
        if not goal_data:
            return self.error_response('No goal data found. Please start the process again.', status_code=status.HTTP_404_NOT_FOUND)
        
        # Validate that we have enough data
        # min_step = 4 if goal_data.get('verification_type') == 'human' else 3
        if goal_data.get('step', 0) < 4:
            return self.error_response('Please complete all required steps first', status_code=status.HTTP_400_BAD_REQUEST)
        
        # Prepare summary data
        summary = {
            'basic_info': {k: v for k, v in goal_data.items() 
                          if k in ['title', 'description', 'start_date', 'end_date', 
                                  'frequency', 'time_of_day', 'duration_minutes']},
            'stake_info': {k: v for k, v in goal_data.items() 
                          if k in ['penalty_amount', 'payment_method']},
            'verification_info': {k: v for k, v in goal_data.items() 
                                 if k in ['verification_type', 'verification_method']},
        }
        
        if goal_data.get('verification_type') == 'human':
            summary['human_verifiers'] = goal_data.get('human_verifiers', [])
        
        return Response({
            'success': True,
            'message': 'Goal summary',
            'data': summary,
            'ready_to_create': True
        }, status=status.HTTP_200_OK)


class GoalCreateFinalView(BaseGoalCreationView):
    """Final step: Create the actual goal"""
    
    def post(self, request):
        goal_data = self.get_goal_data()
        
        if not goal_data:
            return self.error_response('No goal data found. Please start the process again.', status_code=status.HTTP_404_NOT_FOUND)
        
        try:
            # Remove non-model fields
            user_id = goal_data.pop('user_id', None)
            goal_data.pop('step', None)
            goal_data.pop('created_at', None)
            human_verifiers_data = goal_data.pop('human_verifiers', [])
            
            # Convert string dates back to date objects
            if goal_data.get('start_date'):
                goal_data['start_date'] = timezone.datetime.fromisoformat(
                    goal_data['start_date']
                ).date()
            if goal_data.get('end_date'):
                goal_data['end_date'] = timezone.datetime.fromisoformat(
                    goal_data['end_date']
                ).date()
            if goal_data.get('time_of_day'):
                goal_data['time_of_day'] = timezone.datetime.fromisoformat(
                    f"2000-01-01T{goal_data['time_of_day']}"
                ).time()
            
            # Create the goal
            goal_data['user'] = request.user
            goal = Goal.objects.create(**goal_data)
            
            # Create human verifiers if any
            for verifier_data in human_verifiers_data:
                HumanVerifier.objects.create(goal=goal, **verifier_data)
            
            # Clear cache
            cache.delete(self.get_cache_key())
            
            # Serialize the created goal
            serializer = GoalSerializer(goal)
            
            return Response({
                'success': True,
                'message': 'Goal created successfully!',
                'goal': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return self.error_response(f'Failed to create goal: {str(e)}', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoalCancelCreationView(StandardResponseMixin, APIView):
    """Cancel goal creation process"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        cache_key = f"goal_creation_{request.user.id}"
        cache.delete(cache_key)
        
        return self.success_response(message='Goal creation cancelled successfully', status=status.HTTP_200_OK)


class GoalListCreateView(StandardResponseMixin, ListCreateAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(
                data=serializer.data,
                message="Goals retrieved successfully"
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # def create(self, request, *args, **kwargs):
    #     try:
    #         serializer = self.get_serializer(data=request.data)
    #         if not serializer.is_valid():
    #             error_message = self.format_serializer_errors(serializer.errors)
    #             return self.error_response(error_message)
            
    #         self.perform_create(serializer)
    #         return self.success_response(
    #             data=serializer.data,
    #             message="Goal created successfully", 
    #             status_code=status.HTTP_201_CREATED
    #         )
    #     except Exception as e:
    #         return self.error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)





class GoalDetailView(StandardResponseMixin, RetrieveUpdateDestroyAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    lookup_field = 'id'

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data,
                message="Goal retrieved successfully"
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if not serializer.is_valid():
                error_message = self.format_serializer_errors(serializer.errors)
                return self.error_response(error_message)
            
            self.perform_update(serializer)
            return self.success_response(
                data=serializer.data,
                message="Goal updated successfully"
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return self.success_response(
                data=None,
                message="Goal deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_404_NOT_FOUND)
        



from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from core_apps.common.mixins import StandardResponseMixin
from .models import GoalLog
from .serializers import GoalLogListSerializer, GoalLogDetailSerializer

# Create your views here.






class GoalLogListView(StandardResponseMixin, ListAPIView):
    serializer_class = GoalLogListSerializer

    def get_queryset(self):
        queryset = GoalLog.objects.filter(goal__user=self.request.user).order_by("-date")

        # Optional: filter by goal_id query param
        goal_id = self.request.query_params.get("goal_id")
        if goal_id:
            queryset = queryset.filter(goal_id=goal_id)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.success_response(
            data=serializer.data,
            message="Goal logs retrieved successfully",
            status_code=status.HTTP_200_OK,
        )


class GoalLogDetailView(StandardResponseMixin, RetrieveAPIView):
    queryset = GoalLog.objects.all()
    serializer_class = GoalLogDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return GoalLog.objects.filter(goal__user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(
            data=serializer.data,
            message="Goal log retrieved successfully",
            status_code=status.HTTP_200_OK,
        )
    




class UserGoalLogsView(ListAPIView):
    """
    List all goal logs for the authenticated user
    """
    # permission_classes = [IsAuthenticated]
    # serializer_class = GoalLogSerializer
    
    def get_queryset(self):
        user = self.request.user
        goal_id = self.request.query_params.get('goal_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        status_filter = self.request.query_params.get('status')
        
        queryset = GoalLog.objects.filter(goal__user=user).select_related('goal')
        
        if goal_id:
            queryset = queryset.filter(goal_id=goal_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date')
    

class GoalLogDetailView(RetrieveAPIView):
    """
    Get detailed information about a specific goal log including verification details
    """
    # permission_classes = [IsAuthenticated]
    # serializer_class = GoalLogSerializer
    
    def get_queryset(self):
        return GoalLog.objects.filter(goal__user=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        goal_log = self.get_object()
        serializer = self.get_serializer(goal_log)
        
        # Add verification details based on goal's verification method
        verification_data = self._get_verification_details(goal_log)
        
        response_data = serializer.data
        response_data['verification_details'] = verification_data
        
        return Response(response_data)
    
    def _get_verification_details(self, goal_log):
        """
        Get verification details based on the goal's verification method
        """
        goal = goal_log.goal
        verification_method = goal.verification_method
        
        if verification_method == 'text':
            verifications = goal_log.text_verifications.all()
            return TextVerificationSerializer(verifications, many=True).data
        elif verification_method == 'photo':
            verifications = goal_log.image_verifications.all()
            return PhotoVerificationSerializer(verifications, many=True).data
        elif verification_method == 'video':
            verifications = goal_log.video_verifications.all()
            return VideoVerificationSerializer(verifications, many=True).data
        elif verification_method == 'friend':
            verifications = goal_log.friend_verifications.all()
            return FriendVerificationSerializer(verifications, many=True).data
        
        return []
    


class MissedGoalDaysView(APIView):
    """
    Get all missed goal days and apply penalties if needed
    """
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        goal_id = request.query_params.get('goal_id')
        
        if goal_id:
            goals = Goal.objects.filter(id=goal_id, user=user, is_active=True)
        else:
            goals = Goal.objects.filter(user=user, is_active=True)
        
        missed_days = []
        today = date.today()
        
        for goal in goals:
            # Get all days that should have been completed
            expected_dates = self._get_expected_dates(goal, today)
            
            for expected_date in expected_dates:
                # Check if there's a completed log for this date
                log_exists = GoalLog.objects.filter(
                    goal=goal,
                    date=expected_date,
                    status='completed'
                ).exists()
                
                if not log_exists:
                    # Check if missed log already exists
                    missed_log, created = GoalLog.objects.get_or_create(
                        goal=goal,
                        date=expected_date,
                        defaults={'status': 'missed'}
                    )
                    
                    missed_days.append({
                        'goal_id': goal.id,
                        'goal_title': goal.title,
                        'date': expected_date,
                        'penalty_amount': goal.penalty_amount,
                        'penalty_applied': missed_log.penalty_applied
                    })
        
        return Response({
            'missed_days': missed_days,
            'total_penalty': sum(day['penalty_amount'] for day in missed_days if not day['penalty_applied'])
        })
    
    def _get_expected_dates(self, goal, end_date):
        """
        Calculate all dates when the goal should have been completed
        """
        expected_dates = []
        current_date = goal.start_date
        
        while current_date <= end_date and (not goal.end_date or current_date <= goal.end_date):
            if self._should_complete_on_date(goal, current_date):
                expected_dates.append(current_date)
            current_date += timedelta(days=1)
        
        return expected_dates
    
    def _should_complete_on_date(self, goal, check_date):
        """
        Check if goal should be completed on a specific date based on frequency
        """
        if goal.frequency == 'daily':
            return True
        elif goal.frequency == 'weekly':
            # Assuming weekly goals should be completed on the same day of week as start_date
            return check_date.weekday() == goal.start_date.weekday()
        elif goal.frequency == 'specific_days':
            # Parse weekdays from stored string (you might want to use ArrayField)
            if goal.weekdays:
                import json
                try:
                    weekdays = json.loads(goal.weekdays.replace("'", '"'))
                    day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    return day_names[check_date.weekday()] in weekdays
                except:
                    return False
        elif goal.frequency == 'count_based':
            # This would require more complex logic based on your requirements
            return False
        
        return False
    



# class PendingGoalLogsView(ListAPIView):
#     """
#     Get pending goal logs that need submissions
    
#     GET /api/submissions/pending/ - Get pending goal logs for submission
#     """
#     serializer_class = GoalLogSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         """Get pending goal logs without submissions"""
#         pending_logs = GoalLog.objects.filter(
#             goal__user=self.request.user,
#             status='pending',
#             date__lte=date.today()
#         ).select_related('goal').order_by('date')
        
#         # Filter out logs that already have submissions
#         # Note: This is done in Python to avoid complex SQL
#         return [
#             log for log in pending_logs 
#             if not hasattr(log, 'submission')
#         ]
    
#     def list(self, request, *args, **kwargs):
#         """Override list to handle Python filtering"""
#         queryset = self.get_queryset()
#         serializer = self.get_serializer(queryset, many=True)
#         return Response(serializer.data)
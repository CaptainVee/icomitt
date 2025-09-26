from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework import permissions
from django.db import transaction
from core_apps.verifications.tasks import process_ai_verification, send_verification_reminder
from .serializers import SubmissionSerializer, SubmissionListSerializer
from .models import Submission


class SubmissionListCreateView(ListCreateAPIView):
    """
    List user's submissions and create new submissions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return submissions for authenticated user only"""
        return Submission.objects.filter(
            goal_log__goal__user=self.request.user
        ).select_related(
            'goal_log', 'goal_log__goal'
        ).prefetch_related(
            'text_content', 'photo_content', 'video_content', 'friend_content'
        ).order_by('-submitted_at')
    
    def get_serializer_class(self):
        """Use different serializers for list vs create"""
        if self.request.method == 'GET':
            return SubmissionListSerializer
        return SubmissionSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @transaction.atomic
    def perform_create(self, serializer):
        """Create submission and queue verification"""
        submission = serializer.save()
        
        # Queue AI verification if needed
        if submission.goal_log.goal.verification_type == 'ai':
            process_ai_verification.delay(submission.id)
        
        # For human verification, send notification to verifier
        elif submission.goal_log.goal.verification_type == 'human':
            self._handle_human_verification(submission)
        
        return submission
    
    def _handle_human_verification(self, submission):
        """Handle human verification workflow"""
        
        # Get primary human verifier
        verifier = submission.goal_log.goal.human_verifiers.filter(
            is_primary=True, 
            has_accepted=True
        ).first()
        
        if verifier:
            # Send immediate notification to verifier
            send_verification_reminder.delay(submission.id, verifier.id)


class SubmissionDetailView(RetrieveAPIView):
    """
    Get submission details
    """
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return submissions for authenticated user only"""
        return Submission.objects.filter(
            goal_log__goal__user=self.request.user
        ).select_related(
            'goal_log', 'goal_log__goal'
        ).prefetch_related(
            'text_content', 'photo_content', 'video_content', 'friend_content'
        )
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context



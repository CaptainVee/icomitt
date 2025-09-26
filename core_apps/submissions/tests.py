

class SubmissionDetailView(RetrieveAPIView):
    """
    Get submission details
    
    GET /api/submissions/{id}/ - Get submission details
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


class SubmissionContentView(APIView):
    """
    Get submission content details
    
    GET /api/submissions/{id}/content/ - Get submission content details
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Get submission object"""
        return get_object_or_404(
            Submission.objects.filter(goal_log__goal__user=self.request.user),
            pk=self.kwargs['pk']
        )
    
    def get(self, request, pk):
        """Get submission content details"""
        submission = self.get_object()
        
        content_data = {}
        verification_method = submission.goal_log.goal.verification_method
        
        if verification_method == 'text' and hasattr(submission, 'text_content'):
            content_data = TextSubmissionSerializer(submission.text_content).data
        elif verification_method == 'photo' and hasattr(submission, 'photo_content'):
            content_data = PhotoSubmissionSerializer(submission.photo_content).data
        elif verification_method == 'video' and hasattr(submission, 'video_content'):
            content_data = VideoSubmissionSerializer(submission.video_content).data
        elif verification_method == 'friend' and hasattr(submission, 'friend_content'):
            content_data = FriendSubmissionSerializer(submission.friend_content).data
        
        return Response({
            'submission_id': submission.id,
            'verification_method': verification_method,
            'content': content_data
        })

























class FriendSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for friend verification submissions"""
    
    class Meta:
        model = FriendSubmission
        fields = [
            'friend_email', 'friend_name', 'message_to_friend',
            'friend_confirmed', 'friend_confirmed_at'
        ]
        read_only_fields = ['friend_confirmed', 'friend_confirmed_at', 'verification_code']
    
    def validate_friend_email(self, value):
        from django.core.validators import validate_email
        validate_email(value)
        
        # Don't allow user to verify their own submission
        request = self.context.get('request')
        if request and request.user.email == value:
            raise ValidationError("You cannot verify your own submission")
        
        return value
    
    def validate_friend_name(self, value):
        if len(value.strip()) < 2:
            raise ValidationError("Friend name must be at least 2 characters")
        return value.strip()








# =============================================================================
# API VIEWS
# =============================================================================

from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django.db import transaction
from django.shortcuts import get_object_or_404

# Import your background tasks
from .tasks import process_ai_verification


class SubmissionViewSet(ModelViewSet):
    """
    ViewSet for managing submissions
    
    Endpoints:
    - GET /api/submissions/ - List user's submissions
    - POST /api/submissions/ - Create new submission
    - GET /api/submissions/{id}/ - Get submission details
    - GET /api/submissions/pending/ - Get pending goal logs for submission
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
        ).order_by('-submitted_at')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return SubmissionListSerializer
        return SubmissionSerializer
    
    @transaction.atomic
    def create(self, request):
        """Create a new submission"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        submission = serializer.save()
        
        # Queue AI verification if needed
        if submission.goal_log.goal.verification_type == 'ai':
            process_ai_verification.delay(submission.id)
        
        # For human verification, send notification to verifier
        elif submission.goal_log.goal.verification_type == 'human':
            self._handle_human_verification(submission)
        
        return Response(
            SubmissionSerializer(submission, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def _handle_human_verification(self, submission):
        """Handle human verification workflow"""
        from .tasks import send_verification_reminder
        
        # Get primary human verifier
        verifier = submission.goal_log.goal.human_verifiers.filter(
            is_primary=True, 
            has_accepted=True
        ).first()
        
        if verifier:
            # Send immediate notification to verifier
            send_verification_reminder.delay(submission.id, verifier.id)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending goal logs that need submissions"""
        pending_logs = GoalLog.objects.filter(
            goal__user=request.user,
            status='pending',
            date__lte=date.today()
        ).select_related('goal').order_by('date')
        
        # Filter out logs that already have submissions
        pending_logs = [
            log for log in pending_logs 
            if not hasattr(log, 'submission')
        ]
        
        serializer = GoalLogSerializer(pending_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        """Get submission content details"""
        submission = self.get_object()
        
        content_data = {}
        verification_method = submission.goal_log.goal.verification_method
        
        if verification_method == 'text' and hasattr(submission, 'text_content'):
            content_data = TextSubmissionSerializer(submission.text_content).data
        elif verification_method == 'photo' and hasattr(submission, 'photo_content'):
            content_data = PhotoSubmissionSerializer(submission.photo_content).data
        elif verification_method == 'video' and hasattr(submission, 'video_content'):
            content_data = VideoSubmissionSerializer(submission.video_content).data
        elif verification_method == 'friend' and hasattr(submission, 'friend_content'):
            content_data = FriendSubmissionSerializer(submission.friend_content).data
        
        return Response({
            'submission_id': submission.id,
            'verification_method': verification_method,
            'content': content_data
        })





class FriendVerificationView(APIView):
    """
    Friend verification endpoint
    GET /api/verify/friend/{verification_code}/ - Get verification details
    POST /api/verify/friend/{verification_code}/ - Submit friend verification
    """
    permission_classes = []  # No authentication required for friend verification
    
    def get(self, request, verification_code):
        """Get verification details for friend"""
        try:
            friend_submission = FriendSubmission.objects.get(
                verification_code=verification_code
            )
            
            return Response({
                'friend_name': friend_submission.friend_name,
                'user_name': friend_submission.submission.goal_log.goal.user.get_full_name(),
                'goal_title': friend_submission.submission.goal_log.goal.title,
                'goal_date': friend_submission.submission.goal_log.date,
                'message': friend_submission.message_to_friend,
                'already_verified': friend_submission.friend_confirmed
            })
            
        except FriendSubmission.DoesNotExist:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def post(self, request, verification_code):
        """Submit friend verification"""
        try:
            friend_submission = FriendSubmission.objects.get(
                verification_code=verification_code
            )
            
            if friend_submission.friend_confirmed:
                return Response(
                    {'error': 'Already verified'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get verification decision
            verified = request.data.get('verified', False)
            notes = request.data.get('notes', '')
            
            with transaction.atomic():
                # Update friend submission
                friend_submission.friend_confirmed = True
                friend_submission.friend_confirmed_at = timezone.now()
                friend_submission.save()
                
                # Update main submission
                submission = friend_submission.submission
                submission.status = 'approved' if verified else 'rejected'
                submission.verified_at = timezone.now()
                submission.verification_notes = f"Friend verification: {notes}" if notes else "Friend verification completed"
                submission.save()
                
                # Update goal log
                if verified:
                    submission.goal_log.status = 'completed'
                    submission.goal_log.completion_time = timezone.now()
                else:
                    submission.goal_log.status = 'missed'
                
                submission.goal_log.save()
            
            return Response({
                'message': 'Verification completed successfully',
                'verified': verified
            })
            
        except FriendSubmission.DoesNotExist:
            return Response(
                {'error': 'Invalid verification code'},
                status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# URLS CONFIGURATION
# =============================================================================

"""
Add these to your urls.py:

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubmissionViewSet, QuickSubmissionView, FriendVerificationView

router = DefaultRouter()
router.register(r'submissions', SubmissionViewSet, basename='submissions')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/quick-submit/', QuickSubmissionView.as_view(), name='quick-submit'),
    path('api/verify/friend/<str:verification_code>/', 
         FriendVerificationView.as_view(), 
         name='friend-verification'),
]
"""

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
MOBILE APP USAGE EXAMPLES:

1. GET PENDING SUBMISSIONS:
GET /api/submissions/pending/
Response: [
    {
        "id": "uuid",
        "date": "2025-10-15",
        "status": "pending",
        "goal_title": "Read for 30 minutes",
        "verification_method": "photo",
        "penalty_amount": "10.00"
    }
]

2. SUBMIT TEXT PROOF:
POST /api/submissions/
{
    "goal_log_id": "uuid",
    "text_content": {
        "content": "I completed my reading session today. Read Chapter 5 of Atomic Habits and took detailed notes about habit stacking."
    }
}

3. SUBMIT PHOTO PROOF:
POST /api/submissions/
Content-Type: multipart/form-data
{
    "goal_log_id": "uuid",
    "photo_content": {
        "image": <file>,
        "caption": "Reading setup with my morning coffee"
    }
}

4. QUICK SUBMIT (Mobile-friendly):
POST /api/quick-submit/
{
    "goal_log_id": "uuid",
    "content": "Finished my 30-minute reading session",
    "image": <file>,  // for photo verification
    "caption": "Optional caption"
}

5. FRIEND VERIFICATION:
GET /api/verify/friend/ABC123/  // Friend clicks email link
POST /api/verify/friend/ABC123/
{
    "verified": true,
    "notes": "I saw John reading at the coffee shop this morning"
}

6. LIST USER SUBMISSIONS:
GET /api/submissions/
Response: [
    {
        "id": "uuid",
        "goal_title": "Read for 30 minutes",
        "goal_date": "2025-10-15",
        "submitted_at": "2025-10-15T20:30:00Z",
        "status": "approved",
        "verification_method": "photo",
        "ai_confidence_score": 0.87
    }
]
"""








































# =============================================================================
# ENHANCED MODELS (Adjustments to support background jobs)
# =============================================================================

from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta, datetime
from celery import shared_task
import logging
import uuid

# Enhanced Wallet model with staking methods
class Wallet(TimeStampedUUIDModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    staked_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.email} - Balance: ${self.balance}, Staked: ${self.staked_balance}"

    def credit(self, amount: Decimal):
        self.balance += amount
        self.save(update_fields=["balance"])

    def debit(self, amount: Decimal):
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save(update_fields=["balance"])
    
    def stake_amount(self, amount: Decimal):
        """Move money from balance to staked_balance"""
        if self.balance < amount:
            raise ValueError("Insufficient balance to stake")
        self.balance -= amount
        self.staked_balance += amount
        self.save(update_fields=["balance", "staked_balance"])
    
    def unstake_amount(self, amount: Decimal):
        """Move money from staked_balance back to balance (reward)"""
        if self.staked_balance < amount:
            raise ValueError("Insufficient staked balance")
        self.staked_balance -= amount
        self.balance += amount
        self.save(update_fields=["balance", "staked_balance"])
    
    def forfeit_stake(self, amount: Decimal):
        """Remove money from staked_balance (penalty)"""
        if self.staked_balance < amount:
            amount = self.staked_balance  # Take whatever is available
        self.staked_balance -= amount
        self.save(update_fields=["staked_balance"])
        return amount  # Return actual amount forfeited


# Enhanced WalletTransaction with more transaction types
class WalletTransaction(TimeStampedUUIDModel):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    TRANSACTION_STATUS = [
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]

    DEPOSIT = "deposit"
    STAKE = "stake"
    UNSTAKE = "unstake"
    PENALTY = "penalty"
    REWARD = "reward"

    TRANSACTION_TYPE = [
        (DEPOSIT, "Deposit"),
        (STAKE, "Stake"),
        (UNSTAKE, "Unstake"),
        (PENALTY, "Penalty"),
        (REWARD, "Reward"),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default=PENDING)
    
    # Link to penalty transaction if applicable
    penalty_transaction = models.ForeignKey(
        'PenaltyTransaction', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.wallet.user.email} - {self.type} - ${self.amount} - {self.status}"


# Enhanced PenaltyTransaction
class PenaltyTransaction(TimeStampedUUIDModel):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

    TRANSACTION_STATUS = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
        (REFUNDED, "Refunded"),
    ]

    goal_log = models.ForeignKey(
        'GoalLog', 
        on_delete=models.CASCADE, 
        related_name="penalty_transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=TRANSACTION_STATUS, default=PENDING)
    payment_method = models.CharField(max_length=20)
    
    # Enhanced tracking
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Penalty ${self.amount} for {self.goal_log} - {self.status}"


# =============================================================================
# BACKGROUND JOB 1: DAILY LOG CREATOR
# =============================================================================

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def create_daily_goal_logs(self, days_ahead=7):
    """
    Create GoalLog entries for active goals for the next N days
    Runs daily at midnight
    """
    try:
        from datetime import date, timedelta
        
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        # Get all active goals
        active_goals = Goal.objects.filter(
            is_active=True,
            is_completed=False,
            start_date__lte=end_date
        ).select_related('user')
        
        logs_created = 0
        
        for goal in active_goals:
            # Determine date range for this goal
            goal_start = max(goal.start_date, today)
            goal_end = goal.end_date if goal.end_date else end_date
            goal_end = min(goal_end, end_date)
            
            current_date = goal_start
            
            while current_date <= goal_end:
                should_create_log = False
                
                # Check if log should be created based on frequency
                if goal.frequency == 'daily':
                    should_create_log = True
                elif goal.frequency == 'weekly':
                    # Create on the same weekday as start_date
                    if current_date.weekday() == goal.start_date.weekday():
                        should_create_log = True
                elif goal.frequency == 'specific_days' and goal.weekdays:
                    day_name = current_date.strftime("%A").lower()
                    if day_name in goal.weekdays:
                        should_create_log = True
                elif goal.frequency == 'specific_dates' and goal.specific_dates:
                    if current_date.isoformat() in goal.specific_dates:
                        should_create_log = True
                
                if should_create_log:
                    # Create log if it doesn't exist
                    goal_log, created = GoalLog.objects.get_or_create(
                        goal=goal,
                        date=current_date,
                        defaults={
                            'status': 'pending',
                            'penalty_amount': goal.penalty_amount,
                            'penalty_applied': False
                        }
                    )
                    
                    if created:
                        logs_created += 1
                        logger.info(f"Created GoalLog for {goal.title} on {current_date}")
                
                current_date += timedelta(days=1)
        
        logger.info(f"Daily log creator completed. Created {logs_created} new logs.")
        return f"Created {logs_created} goal logs"
        
    except Exception as exc:
        logger.error(f"Daily log creator failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry in 5 minutes


# =============================================================================
# BACKGROUND JOB 2: MISSED GOAL PROCESSOR
# =============================================================================

@shared_task(bind=True, max_retries=3)
def process_missed_goals(self, check_date=None):
    """
    Process missed goals from previous day and apply penalties
    Runs daily at 1 AM
    """
    try:
        if check_date is None:
            check_date = date.today() - timedelta(days=1)  # Yesterday
        else:
            check_date = datetime.strptime(check_date, '%Y-%m-%d').date()
        
        # Find all pending goal logs from check_date
        missed_logs = GoalLog.objects.filter(
            date=check_date,
            status='pending'  # Still pending means user never submitted
        ).select_related('goal', 'goal__user')
        
        penalties_applied = 0
        
        for missed_log in missed_logs:
            try:
                with transaction.atomic():
                    # Update status to missed
                    missed_log.status = 'missed'
                    missed_log.save(update_fields=['status'])
                    
                    # Create penalty transaction
                    penalty = PenaltyTransaction.objects.create(
                        goal_log=missed_log,
                        amount=missed_log.penalty_amount,
                        status='pending',
                        payment_method=missed_log.goal.payment_method,
                        notes=f'Penalty for missing {missed_log.goal.title} on {missed_log.date}'
                    )
                    
                    # Queue penalty processing
                    process_penalty_payment.delay(penalty.id)
                    
                    penalties_applied += 1
                    logger.info(f"Applied penalty for {missed_log.goal.title} on {missed_log.date}")
                    
            except Exception as e:
                logger.error(f"Failed to process missed goal {missed_log.id}: {str(e)}")
                continue
        
        # Also check for goals that have passed their end date
        completed_goals = Goal.objects.filter(
            is_active=True,
            is_completed=False,
            end_date__lt=date.today()
        )
        
        for goal in completed_goals:
            goal.is_completed = True
            goal.is_active = False
            goal.save(update_fields=['is_completed', 'is_active'])
            logger.info(f"Marked goal {goal.title} as completed (end date passed)")
        
        logger.info(f"Missed goal processor completed. Applied {penalties_applied} penalties.")
        return f"Processed {penalties_applied} missed goals"
        
    except Exception as exc:
        logger.error(f"Missed goal processor failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * 10)  # Retry in 10 minutes


# =============================================================================
# BACKGROUND JOB 3: AI VERIFICATION QUEUE
# =============================================================================

@shared_task(bind=True, max_retries=3)
def process_ai_verification(self, submission_id):
    """
    Process AI verification for photo/video submissions
    Triggered when user submits verification
    """
    try:
        submission = Submission.objects.get(id=submission_id)
        
        if submission.status != 'submitted':
            logger.warning(f"Submission {submission_id} already processed")
            return f"Submission {submission_id} already processed"
        
        # Update status to under review
        submission.status = 'under_review'
        submission.save(update_fields=['status'])
        
        # Determine verification type based on goal
        goal = submission.goal_log.goal
        verification_result = None
        
        if goal.verification_method == 'photo':
            verification_result = verify_photo_submission(submission)
        elif goal.verification_method == 'video':
            verification_result = verify_video_submission(submission)
        elif goal.verification_method == 'text':
            verification_result = verify_text_submission(submission)
        elif goal.verification_method == 'friend':
            # Friend verification is handled separately
            return handle_friend_verification(submission)
        
        # Update submission based on AI result
        if verification_result:
            submission.ai_confidence_score = verification_result.get('confidence_score', 0)
            submission.verification_notes = verification_result.get('notes', '')
            
            # Auto-approve if confidence is high enough
            if verification_result.get('confidence_score', 0) >= 0.8:
                submission.status = 'approved'
                submission.verified_at = timezone.now()
                
                # Update goal log
                submission.goal_log.status = 'completed'
                submission.goal_log.completion_time = timezone.now()
                submission.goal_log.save(update_fields=['status', 'completion_time'])
                
                logger.info(f"Auto-approved submission {submission_id}")
                
            elif verification_result.get('confidence_score', 0) <= 0.3:
                submission.status = 'rejected'
                submission.verified_at = timezone.now()
                
                # Update goal log
                submission.goal_log.status = 'missed'
                submission.goal_log.save(update_fields=['status'])
                
                logger.info(f"Auto-rejected submission {submission_id}")
            else:
                # Send to human review queue
                submission.status = 'under_review'
                create_human_review_task.delay(submission_id)
                logger.info(f"Sent submission {submission_id} for human review")
            
            submission.save(update_fields=['status', 'ai_confidence_score', 'verification_notes', 'verified_at'])
        
        return f"Processed AI verification for submission {submission_id}"
        
    except Submission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return f"Submission {submission_id} not found"
    except Exception as exc:
        logger.error(f"AI verification failed for submission {submission_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * 2)  # Retry in 2 minutes


def verify_photo_submission(submission):
    """
    AI verification for photo submissions
    Replace with actual AI service integration
    """
    try:
        photo_content = submission.photo_content
        
        # Mock AI analysis - replace with actual AI service call
        # Example: OpenAI Vision, Google Vision, AWS Rekognition
        
        # Simulate AI processing
        import random
        confidence = random.uniform(0.1, 1.0)  # Mock confidence score
        
        # Mock analysis based on goal type
        goal_title = submission.goal_log.goal.title.lower()
        
        if 'read' in goal_title:
            detected_objects = ['book', 'person'] if confidence > 0.5 else ['person']
            notes = f"Detected: {', '.join(detected_objects)}. Reading activity confidence: {confidence:.2f}"
        elif 'exercise' in goal_title or 'workout' in goal_title:
            detected_objects = ['person', 'gym equipment'] if confidence > 0.5 else ['person']
            notes = f"Detected: {', '.join(detected_objects)}. Exercise activity confidence: {confidence:.2f}"
        else:
            detected_objects = ['person']
            notes = f"General activity confidence: {confidence:.2f}"
        
        return {
            'confidence_score': confidence,
            'detected_objects': detected_objects,
            'notes': notes,
            'verified': confidence > 0.5
        }
        
    except Exception as e:
        logger.error(f"Photo verification failed: {str(e)}")
        return None


def verify_video_submission(submission):
    """AI verification for video submissions"""
    # Similar to photo verification but for videos
    # Would integrate with video analysis AI services
    return verify_photo_submission(submission)  # Placeholder


def verify_text_submission(submission):
    """AI verification for text submissions"""
    try:
        text_content = submission.text_content
        
        # Mock text analysis - replace with actual NLP service
        content_length = len(text_content.content)
        
        # Simple heuristics for text verification
        confidence = min(1.0, content_length / 100)  # Longer text = higher confidence
        
        return {
            'confidence_score': confidence,
            'notes': f"Text analysis: {content_length} characters. Confidence: {confidence:.2f}",
            'verified': confidence > 0.3
        }
        
    except Exception as e:
        logger.error(f"Text verification failed: {str(e)}")
        return None


@shared_task
def create_human_review_task(submission_id):
    """Create a task for human reviewers"""
    # This would integrate with your admin panel or review system
    # For now, just log it
    logger.info(f"Human review needed for submission {submission_id}")
    return f"Created human review task for submission {submission_id}"


def handle_friend_verification(submission):
    """Handle friend verification process"""
    # Send email to friend with verification link
    friend_content = submission.friend_content
    
    # Generate verification code and send email
    verification_code = str(uuid.uuid4())[:6].upper()
    friend_content.verification_code = verification_code
    friend_content.save()
    
    # Queue email sending
    send_friend_verification_email.delay(submission.id, friend_content.friend_email, verification_code)
    
    return f"Friend verification email sent for submission {submission.id}"


@shared_task
def send_friend_verification_email(submission_id, friend_email, verification_code):
    """Send verification email to friend"""
    # Integrate with your email service (SendGrid, AWS SES, etc.)
    logger.info(f"Sending verification email to {friend_email} with code {verification_code}")
    return f"Verification email sent to {friend_email}"


# =============================================================================
# BACKGROUND JOB 4: PAYMENT PROCESSOR
# =============================================================================

@shared_task(bind=True, max_retries=5)
def process_penalty_payment(self, penalty_transaction_id):
    """
    Process penalty payment by deducting from staked balance
    """
    try:
        penalty = PenaltyTransaction.objects.get(id=penalty_transaction_id)
        
        if penalty.status != 'pending':
            logger.warning(f"Penalty {penalty_transaction_id} already processed")
            return f"Penalty {penalty_transaction_id} already processed"
        
        penalty.status = 'processing'
        penalty.save(update_fields=['status'])
        
        user = penalty.goal_log.goal.user
        wallet = user.wallet
        
        try:
            with transaction.atomic():
                # Forfeit from staked balance
                forfeited_amount = wallet.forfeit_stake(penalty.amount)
                
                # Create wallet transaction record
                wallet_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    reference=f"PENALTY-{penalty.id}",
                    amount=forfeited_amount,
                    type=WalletTransaction.PENALTY,
                    status=WalletTransaction.SUCCESS,
                    penalty_transaction=penalty,
                    notes=f"Penalty for missing {penalty.goal_log.goal.title} on {penalty.goal_log.date}"
                )
                
                # Update penalty status
                penalty.status = 'completed'
                penalty.processed_at = timezone.now()
                penalty.notes = f"Forfeited ${forfeited_amount} from staked balance"
                penalty.save(update_fields=['status', 'processed_at', 'notes'])
                
                # Mark penalty as applied on goal log
                penalty.goal_log.penalty_applied = True
                penalty.goal_log.save(update_fields=['penalty_applied'])
                
                logger.info(f"Successfully processed penalty ${forfeited_amount} for user {user.email}")
                
                # Send notification to user
                send_penalty_notification.delay(user.id, forfeited_amount, penalty.goal_log.goal.title)
                
                return f"Penalty ${forfeited_amount} processed successfully"
                
        except ValueError as e:
            # Insufficient staked balance
            penalty.status = 'failed'
            penalty.notes = f"Failed: {str(e)}"
            penalty.retry_count += 1
            penalty.next_retry_at = timezone.now() + timedelta(hours=24)  # Retry tomorrow
            penalty.save(update_fields=['status', 'notes', 'retry_count', 'next_retry_at'])
            
            logger.warning(f"Penalty payment failed for user {user.email}: {str(e)}")
            
            # Notify user about insufficient staked balance
            send_insufficient_balance_notification.delay(user.id, penalty.amount)
            
            return f"Penalty payment failed: {str(e)}"
            
    except PenaltyTransaction.DoesNotExist:
        logger.error(f"Penalty transaction {penalty_transaction_id} not found")
        return f"Penalty transaction {penalty_transaction_id} not found"
    except Exception as exc:
        logger.error(f"Penalty payment processing failed: {str(exc)}")
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)  # 1min, 2min, 4min, 8min, 16min
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3) 
def retry_failed_penalties(self):
    """
    Retry failed penalty payments that are due for retry
    Runs every hour
    """
    try:
        failed_penalties = PenaltyTransaction.objects.filter(
            status='failed',
            next_retry_at__lte=timezone.now(),
            retry_count__lt=5  # Max 5 retries
        )
        
        retried_count = 0
        
        for penalty in failed_penalties:
            # Queue for retry
            process_penalty_payment.delay(penalty.id)
            retried_count += 1
            logger.info(f"Queued retry for penalty {penalty.id}")
        
        return f"Queued {retried_count} penalties for retry"
        
    except Exception as exc:
        logger.error(f"Retry failed penalties job failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * 5)


# =============================================================================
# NOTIFICATION TASKS
# =============================================================================

@shared_task
def send_penalty_notification(user_id, amount, goal_title):
    """Send penalty notification to user"""
    try:
        user = User.objects.get(id=user_id)
        # Integrate with your notification system
        logger.info(f"Penalty notification sent to {user.email}: ${amount} for {goal_title}")
        return f"Notification sent to {user.email}"
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for penalty notification")
        return f"User {user_id} not found"


@shared_task
def send_insufficient_balance_notification(user_id, penalty_amount):
    """Notify user about insufficient staked balance"""
    try:
        user = User.objects.get(id=user_id)
        # Send notification about need to stake more money
        logger.info(f"Insufficient balance notification sent to {user.email}: needed ${penalty_amount}")
        return f"Insufficient balance notification sent to {user.email}"
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found for balance notification")
        return f"User {user_id} not found"


# =============================================================================
# CELERY BEAT SCHEDULE (Add to your settings.py)
# =============================================================================

"""
Add this to your Django settings.py CELERY_BEAT_SCHEDULE:

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Daily log creator - runs at midnight
    'create-daily-goal-logs': {
        'task': 'your_app.tasks.create_daily_goal_logs',
        'schedule': crontab(hour=0, minute=0),
        'args': (7,)  # Create logs 7 days ahead
    },
    
    # Missed goal processor - runs at 1 AM
    'process-missed-goals': {
        'task': 'your_app.tasks.process_missed_goals', 
        'schedule': crontab(hour=1, minute=0),
    },
    
    # Retry failed penalties - runs every hour
    'retry-failed-penalties': {
        'task': 'your_app.tasks.retry_failed_penalties',
        'schedule': crontab(minute=0),  # Every hour
    },
}
"""

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

def example_usage():
    """Examples of how to use these background jobs"""
    
    # Manual job triggering (for testing or admin actions)
    
    # Create logs for next week
    create_daily_goal_logs.delay(days_ahead=7)
    
    # Process missed goals for specific date
    process_missed_goals.delay(check_date='2025-10-15')
    
    # Process AI verification for a submission
    process_ai_verification.delay(submission_id=123)
    
    # Process penalty payment
    process_penalty_payment.delay(penalty_transaction_id=456)
    
    # Retry failed penalties
    retry_failed_penalties.delay()

# =============================================================================
# MONITORING AND HEALTH CHECKS
# =============================================================================

@shared_task
def health_check():
    """Health check for background job system"""
    try:
        # Check database connectivity
        Goal.objects.count()
        
        # Check wallet system
        Wallet.objects.count()
        
        return {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': 'ok',
                'wallet_system': 'ok'
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }


if __name__ == "__main__":
    print("Background Jobs for Productivity App")
    print("=====================================")
    print("1. Daily Log Creator - Creates future GoalLog entries")
    print("2. Missed Goal Processor - Applies penalties for missed goals") 
    print("3. AI Verification Queue - Processes submission verifications")
    print("4. Payment Processor - Handles penalty deductions from staked balance")
    print("\nAll jobs are configured with proper error handling, retries, and monitoring.")
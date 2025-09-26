from rest_framework import serializers
from datetime import date
from rest_framework.exceptions import ValidationError
from core_apps.goals.models import Goal
from .models import TextSubmission, PhotoSubmission, VideoSubmission, Submission
from django.core.files.uploadedfile import UploadedFile
from core_apps.logs.models import GoalLog


class GoalLogSerializer(serializers.ModelSerializer):
    """Basic goal log info for submission"""
    goal_title = serializers.CharField(source='goal.title', read_only=True)
    verification_method = serializers.CharField(source='goal.verification_method', read_only=True)
    
    class Meta:
        model = GoalLog
        fields = [
            'id', 'date', 'status', 'goal_title', 
            'verification_method', 'penalty_amount'
        ]
        read_only_fields = ['id', 'date', 'status', 'penalty_amount']


class TextSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for text-based submissions"""
    
    class Meta:
        model = TextSubmission
        fields = ['content']
    
    def validate_content(self, value):
        if len(value.strip()) < 10:
            raise ValidationError("Content must be at least 10 characters long")
        return value.strip()
    

class VideoSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for video-based submissions"""
    
    class Meta:
        model = VideoSubmission
        fields = ['video', 'caption', 'duration_seconds']
        read_only_fields = ['duration_seconds']
    
    def validate_video(self, value):
        if not isinstance(value, UploadedFile):
            raise ValidationError("A valid video file is required")
        
        # Check file size (max 100MB)
        if value.size > 100 * 1024 * 1024:
            raise ValidationError("Video size cannot exceed 100MB")
        
        # Check file type
        allowed_types = ['video/mp4', 'video/mov', 'video/avi', 'video/webm']
        if value.content_type not in allowed_types:
            raise ValidationError("Only MP4, MOV, AVI, and WebM videos are allowed")
        
        return value
    

class PhotoSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for photo-based submissions"""
    
    class Meta:
        model = PhotoSubmission
        fields = ['image', 'caption']
    
    def validate_image(self, value):
        if not isinstance(value, UploadedFile):
            raise ValidationError("A valid image file is required")
        
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise ValidationError("Image size cannot exceed 10MB")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        if value.content_type not in allowed_types:
            raise ValidationError("Only JPEG, PNG, and WebP images are allowed")
        
        return value
    
    def validate_caption(self, value):
        if value and len(value) > 255:
            raise ValidationError("Caption cannot exceed 255 characters")
        return value


class SubmissionSerializer(serializers.ModelSerializer):
    """Main submission serializer"""
    goal_log = GoalLogSerializer(read_only=True)
    goal_log_id = serializers.UUIDField(write_only=True)
    
    # Content serializers
    text_content = TextSubmissionSerializer(required=False, allow_null=True)
    photo_content = PhotoSubmissionSerializer(required=False, allow_null=True)
    video_content = VideoSubmissionSerializer(required=False, allow_null=True)
    # friend_content = FriendSubmissionSerializer(required=False, allow_null=True)
    
    # Read-only fields
    verification_method = serializers.CharField(source='goal_log.goal.verification_method', read_only=True)
    ai_confidence_score = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'goal_log', 'goal_log_id', 'submitted_at', 'status',
            'verified_by', 'verified_at', 'verification_notes', 'ai_confidence_score',
            'verification_method',
            'text_content', 'photo_content', 'video_content',
        ]
        read_only_fields = [
            'id', 'submitted_at', 'status', 'verified_by', 
            'verified_at', 'verification_notes', 'ai_confidence_score'
        ]
    
    def validate_goal_log_id(self, value):
        """Validate goal log exists and belongs to user"""
        request = self.context.get('request')
        if not request or not request.user:
            raise ValidationError("Authentication required")
        
        try:
            goal_log = GoalLog.objects.get(id=value)
        except GoalLog.DoesNotExist:
            raise ValidationError("Goal log not found")
        
        # Check if goal log belongs to the authenticated user
        if goal_log.goal.user != request.user:
            raise ValidationError("You can only submit for your own goals")
        
        # Check if goal log is in pending status
        if goal_log.status != 'pending':
            raise ValidationError(f"Cannot submit for goal with status: {goal_log.status}")
        
        # Check if submission already exists
        #TODO we may want to have multiple submissions in the future
        if hasattr(goal_log, 'submission'):
            raise ValidationError("Submission already exists for this goal log")
        
        # Check if submission is on time (not too late)
        days_late = (date.today() - goal_log.date).days
        if days_late > 1:  # Allow submissions up to 1 days late
            raise ValidationError("Submission is too late (more than 1 days)")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        goal_log_id = attrs.get('goal_log_id')
        
        # Get the goal log to check verification method
        try:
            goal_log = GoalLog.objects.get(id=goal_log_id)
        except GoalLog.DoesNotExist:
            raise ValidationError("Goal log not found")
        
        verification_method = goal_log.goal.verification_method
        
        # Validate that correct content type is provided
        content_fields = {
            'text': 'text_content',
            'photo': 'photo_content', 
            'video': 'video_content',
            # 'friend': 'friend_content'
        }
        
        required_field = content_fields.get(verification_method)
        if not required_field:
            raise ValidationError(f"Unknown verification method: {verification_method}")
        
        # Check that required content is provided
        if not attrs.get(required_field):
            raise ValidationError(f"{required_field.replace('_', ' ').title()} is required for this verification method")
        
        # Check that no other content types are provided
        for field_name, field_key in content_fields.items():
            if field_name != verification_method and attrs.get(field_key):
                raise ValidationError(f"Cannot provide {field_key.replace('_', ' ')} for {verification_method} verification")
        
        return attrs
    
    def create(self, validated_data):
        """Create submission with appropriate content"""
        # Extract content data
        text_data = validated_data.pop('text_content', None)
        photo_data = validated_data.pop('photo_content', None)
        video_data = validated_data.pop('video_content', None)
        # friend_data = validated_data.pop('friend_content', None)
        
        # Create main submission
        submission = Submission.objects.create(**validated_data)
        
        # Create appropriate content model
        if text_data:
            TextSubmission.objects.create(submission=submission, **text_data)
        elif photo_data:
            PhotoSubmission.objects.create(submission=submission, **photo_data)
        elif video_data:
            VideoSubmission.objects.create(submission=submission, **video_data)
        # elif friend_data:
        #     # Generate verification code for friend
        #     import uuid
        #     verification_code = str(uuid.uuid4())[:6].upper()
        #     friend_data['verification_code'] = verification_code
        #     FriendSubmission.objects.create(submission=submission, **friend_data)
        
        return submission



class SubmissionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing submissions"""
    goal_title = serializers.CharField(source='goal_log.goal.title', read_only=True)
    goal_date = serializers.DateField(source='goal_log.date', read_only=True)
    verification_method = serializers.CharField(source='goal_log.goal.verification_method', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'goal_title', 'goal_date', 'submitted_at', 'status',
            'verification_method', 'ai_confidence_score'
        ]




























class ProofSubmissionSerializer(serializers.Serializer):
    """
    Generic serializer for proof submission that handles different verification methods
    """
    goal_id = serializers.UUIDField()
    date = serializers.DateField(default=date.today)
    
    # Text verification fields
    content = serializers.CharField(required=False, allow_blank=True)
    
    # Photo/Video verification fields
    image = serializers.ImageField(required=False)
    video = serializers.FileField(required=False)
    
    # Friend verification fields
    verifier_id = serializers.IntegerField(required=False)
    message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        """
        Ensure that the required fields are provided based on the goal's verification method
        """
        try:
            goal = Goal.objects.get(id=data['goal_id'], user=self.context['request'].user)
        except Goal.DoesNotExist:
            raise serializers.ValidationError("Goal not found or you don't have permission to access it")
        
        verification_method = goal.verification_method
        
        # Validate based on verification method
        if verification_method == 'text' and not data.get('content'):
            raise serializers.ValidationError("Content is required for text verification")
        elif verification_method == 'photo' and not data.get('image'):
            raise serializers.ValidationError("Image is required for photo verification")
        elif verification_method == 'video' and not data.get('video'):
            raise serializers.ValidationError("Video is required for video verification")
        elif verification_method == 'friend':
            if goal.verification_type == 'human' and not data.get('verifier_id'):
                raise serializers.ValidationError("Verifier is required for human friend verification")
        
        data['goal'] = goal
        return data
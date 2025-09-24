from django.urls import path

from .views import (
    GoalDetailView, GoalListCreateView, GoalStep1BasicInfoView, GoalStep2StakeInfoView,
    GoalCancelCreationView, GoalCreateFinalView, GoalStep5SummaryView, GoalStep4HumanVerifiersView,
    GoalStep3VerificationInfoView)

app_name = 'users'


urlpatterns = [
    path('', GoalListCreateView.as_view(), name='goal-list'),
    path('<uuid:id>/', GoalDetailView.as_view(), name='goal-detail'),
    path('goals/create/step1/', GoalStep1BasicInfoView.as_view(), name='goal_step1'),
    path('goals/create/step2/', GoalStep2StakeInfoView.as_view(), name='goal_step2'),
    path('goals/create/step3/', GoalStep3VerificationInfoView.as_view(), name='goal_step3'),
    path('goals/create/step4/', GoalStep4HumanVerifiersView.as_view(), name='goal_step4'),
    path('goals/create/step5/', GoalStep5SummaryView.as_view(), name='goal_step5'),
    path('goals/create/final/', GoalCreateFinalView.as_view(), name='goal_create_final'),
    path('goals/create/cancel/', GoalCancelCreationView.as_view(), name='goal_cancel_creation'),
    # path('create/', GoalListCreateView.as_view(), name='goal-create'),
    # path("goal-logs/", GoalLogListView.as_view(), name="goal-log-list"),
    # path("goal-logs/<uuid:id>/", GoalLogDetailView.as_view(), name="goal-log-detail"),
    # path('update/<int:pk>/', GoalDetailView.as_view(), name='update'),
    # path('delete/<int:pk>/', GoalDetailView.as_view(), name='delete')
]
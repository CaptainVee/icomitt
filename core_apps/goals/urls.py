from django.urls import path

from .views import (
    GoalDetailView, GoalListCreateView, GoalStep1BasicInfoView, GoalStep4StakeInfoView,
    GoalCancelCreationView, GoalCreateFinalView, GoalStep5SummaryView, GoalStep3HumanVerifiersView,
    GoalStep2VerificationInfoView)

app_name = 'users'


urlpatterns = [
    path('', GoalListCreateView.as_view(), name='goal-list'),
    path('<uuid:id>/', GoalDetailView.as_view(), name='goal-detail'),
    path('create/step1/', GoalStep1BasicInfoView.as_view(), name='goal_step1'),
    path('create/step2/', GoalStep2VerificationInfoView.as_view(), name='goal_step3'),
    path('create/step3/', GoalStep3HumanVerifiersView.as_view(), name='goal_step4'),
    path('create/step4/', GoalStep4StakeInfoView.as_view(), name='goal_step2'),
    path('create/step5/', GoalStep5SummaryView.as_view(), name='goal_step5'),
    path('create/final/', GoalCreateFinalView.as_view(), name='goal_create_final'),
    path('create/cancel/', GoalCancelCreationView.as_view(), name='goal_cancel_creation'),
    # path('create/', GoalListCreateView.as_view(), name='goal-create'),
    # path("goal-logs/", GoalLogListView.as_view(), name="goal-log-list"),
    # path("goal-logs/<uuid:id>/", GoalLogDetailView.as_view(), name="goal-log-detail"),
    # path('update/<int:pk>/', GoalDetailView.as_view(), name='update'),
    # path('delete/<int:pk>/', GoalDetailView.as_view(), name='delete')
]

from django.urls import path

from .views import GoalLogDetailView, GoalLogListView

app_name = 'users'


urlpatterns = [
    path("goal-logs/", GoalLogListView.as_view(), name="goal-log-list"),
    path("goal-logs/<uuid:id>/", GoalLogDetailView.as_view(), name="goal-log-detail"),
    #     path('goals/logs/', UserGoalLogsView.as_view(), name='user_goal_logs'),
    # path('goals/logs/<int:pk>/', GoalLogDetailView.as_view(), name='goal_log_detail'),
]
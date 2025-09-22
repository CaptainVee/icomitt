from django.urls import path

from .views import (GoalDetailView, GoalListCreateView)

app_name = 'users'


urlpatterns = [
    path('', GoalListCreateView.as_view(), name='goal-list'),
    path('<uuid:id>/', GoalDetailView.as_view(), name='goal-detail'),
    path('create/', GoalListCreateView.as_view(), name='goal-create'),
    # path('update/<int:pk>/', GoalDetailView.as_view(), name='update'),
    # path('delete/<int:pk>/', GoalDetailView.as_view(), name='delete')
]

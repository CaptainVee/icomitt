from django.urls import path
from .views import SubmissionListCreateView, SubmissionDetailView


urlpatterns = [
    path('', SubmissionListCreateView.as_view(http_method_names=['get']), name='submission-list'),
    path('create/', SubmissionListCreateView.as_view(http_method_names=['post']), name='submission-create'),
    path('<uuid:id>/', SubmissionDetailView.as_view(), name='submission-detail'),
]
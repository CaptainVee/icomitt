from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView
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
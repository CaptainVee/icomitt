from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, RetrieveAPIView
from .models import Goal, GoalLog
from .serializers import GoalSerializer, GoalLogSerializer
from core_apps.common.mixins import StandardResponseMixin


class GoalListCreateView(StandardResponseMixin, ListCreateAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return self.success_response(
                data=serializer.data,
                message="Goals retrieved successfully"
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                error_message = self.format_serializer_errors(serializer.errors)
                return self.error_response(error_message)
            
            self.perform_create(serializer)
            return self.success_response(
                data=serializer.data,
                message="Goal created successfully", 
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoalDetailView(StandardResponseMixin, RetrieveUpdateDestroyAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    lookup_field = 'id'

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return self.success_response(
                data=serializer.data,
                message="Goal retrieved successfully"
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if not serializer.is_valid():
                error_message = self.format_serializer_errors(serializer.errors)
                return self.error_response(error_message)
            
            self.perform_update(serializer)
            return self.success_response(
                data=serializer.data,
                message="Goal updated successfully"
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return self.success_response(
                data=None,
                message="Goal deleted successfully",
                status_code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return self.error_response(str(e), status.HTTP_404_NOT_FOUND)
        


class GoalLogListView(StandardResponseMixin, ListAPIView):
    serializer_class = GoalLogSerializer

    def get_queryset(self):
        queryset = GoalLog.objects.all().order_by("-date")

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
    serializer_class = GoalLogSerializer
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(
            data=serializer.data,
            message="Goal log retrieved successfully",
            status_code=status.HTTP_200_OK,
        )

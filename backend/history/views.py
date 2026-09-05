from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Solution
from .serializers import SolutionSerializer


class HistoryView(APIView):
    """List persisted solver results or clear the complete local history."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50

        limit = max(1, min(limit, 200))
        solutions = Solution.objects.all().order_by("-created_at")[:limit]
        return Response(SolutionSerializer(solutions, many=True).data)

    def delete(self, request):
        deleted_count, _ = Solution.objects.all().delete()
        return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)


class HistoryDetailView(APIView):
    """Read or delete one persisted result."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, solution_id):
        solution = get_object_or_404(Solution, pk=solution_id)
        return Response(SolutionSerializer(solution).data)

    def delete(self, request, solution_id):
        solution = get_object_or_404(Solution, pk=solution_id)
        solution.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

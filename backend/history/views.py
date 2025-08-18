from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Solution
from .serializers import SolutionSerializer


class HistoryView(APIView):
    def get(self, request):
        solutions = Solution.objects.all().order_by('-created_at')[:50]
        serializer = SolutionSerializer(solutions, many=True)
        return Response(serializer.data)
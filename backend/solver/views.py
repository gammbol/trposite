from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import SolveSerializer
from .services.solver_service import process_job
from .services.job_manager import create_job, get_job


class SolveView(APIView):
    def post(self, request):
        serializer = SolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        job = create_job(
            data["equation"],
            data.get("variable", "x")
        )

        process_job(job)

        return Response({
            "job_id": job["id"],
            "status": job["status"]
        })


class ResultView(APIView):
    def get(self, request, job_id):
        job = get_job(job_id)

        if not job:
            return Response({"error": "Not found"}, status=404)

        if job["status"] == "done":
            return Response(job["result"])

        if job["status"] == "error":
            return Response({"error": job["error"]}, status=500)

        return Response({"status": job["status"]})
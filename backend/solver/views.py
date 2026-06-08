from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ExplainSerializer, SolveSerializer
from .services.ai.explanation_service import AIExplanationError, AIExplanationService
from .services.job_manager import create_job, get_job
from .services.solvers.sympy_solver import SympySolver


class SolveView(APIView):
    """Fast deterministic solving path. The public endpoint always uses SymPy."""

    def post(self, request):
        serializer = SolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        equation = data["equation"]
        variable = data.get("variable", "x")
        job = create_job(equation, variable)

        try:
            result = SympySolver().solve(equation, variable)
            job["status"] = "done"
            job["result"] = result
            return Response(job)
        except Exception as exc:
            job["status"] = "error"
            job["error"] = str(exc)
            return Response(
                job,
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )


class ExplainView(APIView):
    """AI explanation path with independent verification and self-correction."""

    def post(self, request):
        serializer = ExplainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = AIExplanationService().explain(
                equation=data["equation"],
                variable=data.get("variable", "x"),
            )
            return Response(result)
        except AIExplanationError as exc:
            return Response(
                {
                    "error": str(exc),
                    "verification": exc.verification,
                    "attempts": exc.attempts,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception as exc:
            return Response(
                {"error": f"Не удалось получить AI-объяснение: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


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

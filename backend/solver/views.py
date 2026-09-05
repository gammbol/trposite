from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from history.models import Solution

from .serializers import ConsensusSerializer, ExplainSerializer, SolveSerializer
from .services.ai.explanation_service import AIExplanationError, AIExplanationService
from .services.consensus import ConsensusEngine
from .services.job_manager import create_job, get_job
from .services.solvers.sympy_solver import SympySolver


class PublicAPIView(APIView):
    """Base class for the public local API.

    Explicitly avoids Django session authentication so logging into /admin/
    cannot make SPA requests suddenly require CSRF tokens.
    """

    authentication_classes = []
    permission_classes = []


class SolveView(PublicAPIView):
    """Fast deterministic solve path. Every successful result is persisted."""

    def post(self, request):
        serializer = SolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        equation = data["equation"]
        variable = data.get("variable", "x")
        job = create_job(equation, variable)

        try:
            result = SympySolver().solve(equation, variable)
        except Exception as exc:
            job["status"] = "error"
            job["error"] = str(exc)
            return Response(job, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        try:
            history_entry = Solution.objects.create(
                equation=equation,
                solution=result.get("solution", ""),
                steps=result.get("steps", []),
            )
        except Exception as exc:
            job["status"] = "error"
            job["error"] = f"Решение получено, но не удалось сохранить историю: {exc}"
            return Response(job, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        job["status"] = "done"
        job["result"] = result
        job["history_id"] = history_entry.pk
        return Response(job)


class ExplainView(PublicAPIView):
    """AI explanation path with independent verification/self-correction."""

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


class ConsensusView(PublicAPIView):
    """Independent multi-solver verification and candidate ranking endpoint."""

    def post(self, request):
        serializer = ConsensusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = ConsensusEngine().evaluate(
                equation=data["equation"],
                variable=data.get("variable", "x"),
            )
            return Response(result)
        except Exception as exc:
            return Response(
                {"error": f"Не удалось выполнить независимую проверку: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class ResultView(PublicAPIView):
    def get(self, request, job_id):
        job = get_job(job_id)
        if not job:
            return Response({"error": "Not found"}, status=404)

        if job["status"] == "done":
            return Response(job["result"])

        if job["status"] == "error":
            return Response({"error": job["error"]}, status=500)

        return Response({"status": job["status"]})

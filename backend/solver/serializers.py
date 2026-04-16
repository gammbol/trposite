from rest_framework import serializers

class SolveSerializer(serializers.Serializer):
    equation = serializers.CharField()
    variable = serializers.CharField(required=False, default='x')
    solver = serializers.CharField(required=False, default='sympy')
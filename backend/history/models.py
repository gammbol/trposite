from django.db import models

class Solution(models.Model):
    equation = models.TextField()
    solution = models.TextField()
    steps = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
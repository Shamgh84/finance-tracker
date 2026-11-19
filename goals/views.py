from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Goal, GoalContribution
from .serializers import ContributionSerializer, GoalSerializer


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Goal.objects.none()
        return services.annotate_saved(Goal.objects.filter(user=self.request.user))

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @extend_schema(
        summary='واریز (مبلغ مثبت) یا برداشت (مبلغ منفی) از هدف',
        request=ContributionSerializer,
        responses=GoalSerializer,
    )
    @action(detail=True, methods=['post'])
    def contribute(self, request, pk=None):
        goal = self.get_object()
        form = ContributionSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        amount = form.validated_data['amount']

        if goal.saved + amount < 0:
            return Response(
                {'amount': ['مبلغ برداشت بیشتر از موجودی این هدف است.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        GoalContribution.objects.create(
            goal=goal, amount=amount, note=form.validated_data.get('note', '')
        )
        goal = self.get_queryset().get(pk=goal.pk)
        return Response(self.get_serializer(goal).data)
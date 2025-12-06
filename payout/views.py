"""
Views for payout API
"""
import uuid
from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema

from .models import Payout
from .serializers import PayoutSerializer, PayoutUpdateSerializer
from .tasks import process_payout_task


class PayoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payout applications.
    """
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        if self.action == 'partial_update':
            return PayoutUpdateSerializer
        return PayoutSerializer

    @swagger_auto_schema(
        operation_description="List all payout applications",
        responses={200: PayoutSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all payouts."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a payout by ID",
        responses={200: PayoutSerializer, 404: "Not found"}
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific payout."""
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new payout application",
        request_body=PayoutSerializer,
        responses={201: PayoutSerializer, 400: "Validation error"}
    )
    def create(self, request, *args, **kwargs):
        """Create a new payout and trigger async processing."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payout_id = uuid.uuid4()
        payout = serializer.save(id=payout_id)
        
        # Trigger Celery task for async processing
        process_payout_task.delay(str(payout.id))
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @swagger_auto_schema(
        operation_description="Partially update a payout (mainly status)",
        request_body=PayoutUpdateSerializer,
        responses={200: PayoutSerializer, 400: "Validation error", 404: "Not found"}
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially update a payout."""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a payout",
        responses={204: "No content", 404: "Not found"}
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a payout."""
        return super().destroy(request, *args, **kwargs)


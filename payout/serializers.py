"""
Serializers for payout API
"""
from rest_framework import serializers
from .models import Payout


class PayoutSerializer(serializers.ModelSerializer):
    """
    Serializer for payout model.
    """
    class Meta:
        model = Payout
        fields = [
            'id',
            'amount',
            'currency',
            'recipient_details',
            'status',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

    def validate_amount(self, value):
        """Validate that amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value

    def validate_currency(self, value):
        """Validate currency code format."""
        if not value or len(value) != 3:
            raise serializers.ValidationError("Currency must be a 3-letter code (e.g., USD, EUR).")
        return value.upper()

    def validate_recipient_details(self, value):
        """Validate recipient details."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Recipient details cannot be empty.")
        if len(value) > 1000:
            raise serializers.ValidationError("Recipient details cannot exceed 1000 characters.")
        return value.strip()

    def validate_description(self, value):
        """Validate description if provided."""
        if value and len(value) > 2000:
            raise serializers.ValidationError("Description cannot exceed 2000 characters.")
        return value


class PayoutUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for partial update of payout (mainly status).
    """
    class Meta:
        model = Payout
        fields = ['status', 'description']

    def validate_status(self, value):
        """Validate status transition."""
        if self.instance:
            current_status = self.instance.status
            # Allow status updates based on business logic
            valid_transitions = {
                Payout.Status.PENDING: [Payout.Status.PROCESSING, Payout.Status.CANCELLED],
                Payout.Status.PROCESSING: [Payout.Status.COMPLETED, Payout.Status.FAILED],
            }
            if current_status in valid_transitions:
                if value not in valid_transitions[current_status]:
                    raise serializers.ValidationError(
                        f"Cannot change status from {current_status} to {value}."
                    )
        return value


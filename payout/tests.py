"""
Tests for payout application
"""
import uuid
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import Payout
from .tasks import process_payout_task


class PayoutModelTest(TestCase):
    """Test cases for Payout model."""

    def setUp(self):
        self.payout_data = {
            'id': uuid.uuid4(),
            'amount': Decimal('100.50'),
            'currency': 'USD',
            'recipient_details': 'John Doe, Account: 1234567890',
            'status': Payout.Status.PENDING,
        }

    def test_create_payout(self):
        """Test creating a payout."""
        payout = Payout.objects.create(**self.payout_data)
        self.assertEqual(payout.amount, Decimal('100.50'))
        self.assertEqual(payout.currency, 'USD')
        self.assertEqual(payout.status, Payout.Status.PENDING)

    def test_payout_str(self):
        """Test payout string representation."""
        payout = Payout.objects.create(**self.payout_data)
        self.assertIn(str(payout.id), str(payout))
        self.assertIn('100.50', str(payout))


class PayoutAPITest(TestCase):
    """Test cases for Payout API."""

    def setUp(self):
        self.client = APIClient()
        self.payout_data = {
            'amount': '100.50',
            'currency': 'USD',
            'recipient_details': 'John Doe, Account: 1234567890',
            'description': 'Test payout',
        }

    @patch('payouts.views.process_payout_task.delay')
    def test_create_payout_success(self, mock_task):
        """Test successful payout creation."""
        url = reverse('payout-list')
        response = self.client.post(url, self.payout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['amount'], '100.50')
        self.assertEqual(response.data['currency'], 'USD')
        self.assertEqual(response.data['status'], Payout.Status.PENDING)
        
        # Verify Celery task was called
        mock_task.assert_called_once()
        payout_id = response.data['id']
        mock_task.assert_called_with(payout_id)

    def test_create_payout_invalid_amount(self):
        """Test payout creation with invalid amount."""
        url = reverse('payout-list')
        invalid_data = self.payout_data.copy()
        invalid_data['amount'] = '-10'
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_payout_invalid_currency(self):
        """Test payout creation with invalid currency."""
        url = reverse('payout-list')
        invalid_data = self.payout_data.copy()
        invalid_data['currency'] = 'US'
        
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_payouts(self):
        """Test listing payouts."""
        # Create a payout
        payout = Payout.objects.create(
            id=uuid.uuid4(),
            amount=Decimal('100.00'),
            currency='USD',
            recipient_details='Test recipient',
        )
        
        url = reverse('payout-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_payout(self):
        """Test retrieving a specific payout."""
        payout = Payout.objects.create(
            id=uuid.uuid4(),
            amount=Decimal('100.00'),
            currency='USD',
            recipient_details='Test recipient',
        )
        
        url = reverse('payout-detail', kwargs={'pk': payout.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(payout.id))

    def test_update_payout_status(self):
        """Test updating payout status."""
        payout = Payout.objects.create(
            id=uuid.uuid4(),
            amount=Decimal('100.00'),
            currency='USD',
            recipient_details='Test recipient',
            status=Payout.Status.PENDING,
        )
        
        url = reverse('payout-detail', kwargs={'pk': payout.id})
        update_data = {'status': Payout.Status.PROCESSING}
        response = self.client.patch(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payout.refresh_from_db()
        self.assertEqual(payout.status, Payout.Status.PROCESSING)

    def test_delete_payout(self):
        """Test deleting a payout."""
        payout = Payout.objects.create(
            id=uuid.uuid4(),
            amount=Decimal('100.00'),
            currency='USD',
            recipient_details='Test recipient',
        )
        
        url = reverse('payout-detail', kwargs={'pk': payout.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Payout.objects.filter(id=payout.id).exists())


class PayoutTaskTest(TestCase):
    """Test cases for Celery tasks."""

    def setUp(self):
        self.payout = Payout.objects.create(
            id=uuid.uuid4(),
            amount=Decimal('100.00'),
            currency='USD',
            recipient_details='Test recipient',
            status=Payout.Status.PENDING,
        )

    def test_process_payout_task_success(self):
        """Test successful payout processing."""
        process_payout_task(str(self.payout.id))
        
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, Payout.Status.COMPLETED)

    def test_process_payout_task_large_amount(self):
        """Test payout processing with large amount (should fail)."""
        self.payout.amount = Decimal('2000000.00')
        self.payout.save()
        
        process_payout_task(str(self.payout.id))
        
        self.payout.refresh_from_db()
        self.assertEqual(self.payout.status, Payout.Status.FAILED)


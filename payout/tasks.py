"""
Celery tasks for payout processing
"""
import logging
import time
from celery import shared_task

from .models import Payout

logger = logging.getLogger(__name__)


@shared_task
def process_payout_task(payout_id: str) -> None:
    """
    Process a payout application asynchronously.
    
    This task simulates payout processing:
    - Updates status to PROCESSING
    - Performs validation checks
    - Simulates processing delay
    - Updates status to COMPLETED or FAILED
    
    Args:
        payout_id: UUID of the payout to process
    """
    try:
        payout = Payout.objects.get(id=payout_id)
        
        logger.info(f"Starting processing for payout {payout_id}")
        
        # Update status to processing
        payout.status = Payout.Status.PROCESSING
        payout.save(update_fields=['status'])
        
        # Simulate processing delay
        time.sleep(2)
        
        # Simple validation check (example: amount should be reasonable)
        if payout.amount > 1000000:
            payout.status = Payout.Status.FAILED
            logger.warning(f"Payout {payout_id} failed: amount too large")
        else:
            payout.status = Payout.Status.COMPLETED
            logger.info(f"Payout {payout_id} processed successfully")
        
        payout.save(update_fields=['status'])
        
    except Payout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
    except Exception as e:
        logger.error(f"Error processing payout {payout_id}: {str(e)}")
        try:
            payout = Payout.objects.get(id=payout_id)
            payout.status = Payout.Status.FAILED
            payout.save(update_fields=['status'])
        except Payout.DoesNotExist:
            pass


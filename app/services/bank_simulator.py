"""Bank API simulator for testing transaction processing."""
import asyncio
import random
import uuid
from typing import Dict, Any
from app.config import settings


class BankAPIError(Exception):
    """Base exception for bank API errors."""
    pass


class BankTimeoutError(BankAPIError):
    """Bank API timeout error."""
    pass


class InsufficientFundsError(BankAPIError):
    """Insufficient funds error for withdrawals."""
    pass


class BankSystemUnavailableError(BankAPIError):
    """Bank system unavailable error."""
    pass


class BankSimulator:
    """
    Simulated bank API that mimics real-world behavior.
    
    Features:
    - Random processing delays (2-10 seconds)
    - Configurable success rate (default 90%)
    - Various error scenarios
    """
    
    def __init__(
        self,
        min_delay: int = None,
        max_delay: int = None,
        success_rate: float = None
    ):
        self.min_delay = min_delay or settings.BANK_MIN_DELAY_SECONDS
        self.max_delay = max_delay or settings.BANK_MAX_DELAY_SECONDS
        self.success_rate = success_rate or settings.BANK_SUCCESS_RATE
    
    async def process_deposit(self, amount: float, user_id: int) -> Dict[str, Any]:
        """
        Simulate deposit processing.
        
        Args:
            amount: Deposit amount
            user_id: User ID
            
        Returns:
            Dict with bank_reference and status
            
        Raises:
            BankAPIError: On various error scenarios
        """
        # Simulate processing delay
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
        
        # Simulate random failures
        if random.random() > self.success_rate:
            error_type = random.choice([
                'timeout',
                'system_unavailable',
                'invalid_request'
            ])
            
            if error_type == 'timeout':
                raise BankTimeoutError("Bank API request timed out")
            elif error_type == 'system_unavailable':
                raise BankSystemUnavailableError("Bank system is temporarily unavailable")
            else:
                raise BankAPIError("Invalid request parameters")
        
        # Success case
        bank_reference = f"DEP-{uuid.uuid4().hex[:12].upper()}"
        return {
            "bank_reference": bank_reference,
            "status": "success",
            "amount": amount,
            "user_id": user_id
        }
    
    async def process_withdrawal(self, amount: float, user_id: int) -> Dict[str, Any]:
        """
        Simulate withdrawal processing.
        
        Args:
            amount: Withdrawal amount
            user_id: User ID
            
        Returns:
            Dict with bank_reference and status
            
        Raises:
            BankAPIError: On various error scenarios
        """
        # Simulate processing delay
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
        
        # Simulate random failures
        if random.random() > self.success_rate:
            error_type = random.choice([
                'timeout',
                'system_unavailable',
                'insufficient_funds',
                'invalid_request'
            ])
            
            if error_type == 'timeout':
                raise BankTimeoutError("Bank API request timed out")
            elif error_type == 'system_unavailable':
                raise BankSystemUnavailableError("Bank system is temporarily unavailable")
            elif error_type == 'insufficient_funds':
                # Note: This is a simulated bank-side check, not our balance check
                raise InsufficientFundsError("Insufficient funds in bank account")
            else:
                raise BankAPIError("Invalid request parameters")
        
        # Success case
        bank_reference = f"WTH-{uuid.uuid4().hex[:12].upper()}"
        return {
            "bank_reference": bank_reference,
            "status": "success",
            "amount": amount,
            "user_id": user_id
        }


# Global bank simulator instance
bank_simulator = BankSimulator()

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.case import ResolutionCase, ScheduledFollowup, CaseActionLog
from app.models.payment import Transaction, PaymentEvent
from app.agents.rescue_agent import run_rescue_investigation
from app.agents.pulse_agent import RaahPulseAgent
from app.utils.time_utils import utcnow, ensure_naive

logger = logging.getLogger("raah.followup_worker")

class FollowupWorker:
    """
    Background worker that runs asynchronously to execute scheduled autonomous follow-ups,
    recheck unconfirmed payments, evaluate exponential backoff, and invoke Raah Pulse telemetry scans.
    """
    _is_running = False

    @classmethod
    async def start(cls, interval_seconds: int = 5):
        if cls._is_running:
            return
        cls._is_running = True
        logger.info("Followup background worker started.")
        
        while cls._is_running:
            try:
                await cls.process_due_followups()
                # Run Pulse incident scan every cycle
                await RaahPulseAgent.analyze_telemetry_and_correlate()
            except Exception as e:
                logger.error(f"Error in background worker tick: {e}", exc_info=True)
            
            await asyncio.sleep(interval_seconds)

    @classmethod
    def stop(cls):
        cls._is_running = False

    @classmethod
    async def process_due_followups(cls):
        db: Session = SessionLocal()
        try:
            now = utcnow()
            # Fetch pending followups that are due
            due_followups = db.query(ScheduledFollowup).filter(
                ScheduledFollowup.status == "PENDING",
                ScheduledFollowup.scheduled_for <= now
            ).all()

            for item in due_followups:
                case = db.query(ResolutionCase).filter(ResolutionCase.id == item.case_id).first()
                if not case or case.status in ("RESOLVED", "CLOSED"):
                    item.status = "CANCELLED"
                    db.commit()
                    continue

                item.status = "EXECUTED"
                item.executed_at = now
                case.retry_count = (case.retry_count or 0) + 1
                case.last_checked_at = now
                db.commit()

                logger.info(f"Executing autonomous follow-up for Case {case.case_number} (Retry #{case.retry_count})")
                
                # Run the LangGraph investigation workflow
                await run_rescue_investigation(case.transaction_id, case.user_id)
        finally:
            db.close()

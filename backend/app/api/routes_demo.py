from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.demo.seed_data import reset_database, seed_standard_data
from app.demo.scenario_engine import ScenarioEngine
from app.schemas.demo import TriggerScenarioRequest, DemoScenarioInfo

router = APIRouter(prefix="/demo", tags=["Demo & Scenarios Control"])

@router.post("/reset")
def reset_demo():
    """Drops all tables and re-seeds clean demo data."""
    reset_database()
    res = seed_standard_data()
    return {"status": "RESET_SUCCESSFUL", "details": res}


@router.post("/seed")
def seed_demo():
    """Seeds or refreshes default realistic data."""
    res = seed_standard_data()
    return {"status": "SEED_SUCCESSFUL", "details": res}


@router.get("/scenarios", response_model=List[DemoScenarioInfo])
def list_scenarios():
    """Returns list of supported synthetic failure & recovery scenarios."""
    results = []
    for s_id, s_data in ScenarioEngine.SCENARIOS.items():
        results.append(DemoScenarioInfo(
            id=s_id,
            scenario_number=int(s_id),
            name=s_data["name"],
            description=s_data["desc"],
            expected_outcome="Autonomous recovery workflow execution with verifiable timeline updates.",
            category=s_data["category"]
        ))
    return sorted(results, key=lambda x: x.scenario_number)


@router.post("/scenarios/{scenario_id}/trigger")
async def trigger_scenario(scenario_id: str, payload: TriggerScenarioRequest):
    """Triggers a synthetic scenario to demonstrate Raah Rescue, Raah Pulse, or RetryGuard."""
    res = await ScenarioEngine.trigger_scenario(
        scenario_id=scenario_id,
        user_id=payload.user_id or "user_default_01",
        merchant_id=payload.merchant_id or "merch_grocery_01",
        amount=payload.amount or 4000.0
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

from typing import Optional
from pydantic import BaseModel

class TriggerScenarioRequest(BaseModel):
    user_id: Optional[str] = "user_default_01"
    merchant_id: Optional[str] = "merch_grocery_01"
    amount: Optional[float] = 4000.0

class DemoScenarioInfo(BaseModel):
    id: str
    scenario_number: int
    name: str
    description: str
    expected_outcome: str
    category: str

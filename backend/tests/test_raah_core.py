import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.demo.seed_data import reset_database, seed_standard_data
from app.mcp_servers.client import RaahMCPClient
from app.agents.rescue_agent import run_rescue_investigation
from app.agents.pulse_agent import RaahPulseAgent
from app.policies.reversal_policy import RegulatoryPolicyEngine

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    reset_database()
    seed_standard_data()

@pytest.fixture
def client():
    return TestClient(app)

def test_qr_scanner_supported_merchant(client):
    """Test 1: QR scanner correctly maps a supported demo merchant QR."""
    res = client.post("/api/scan/resolve", json={"qr_content": "upi://pay?pa=grocery@paytm&pn=Demo+Grocery&am=4000"})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["merchant"]["id"] == "merch_grocery_01"
    assert "Grocery" in data["merchant"]["name"]

def test_invalid_qr_rejected(client):
    """Test 2: Invalid QR codes are rejected gracefully."""
    res = client.post("/api/scan/resolve", json={"qr_content": "invalid_random_string_1234"})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert "Unsupported or unrecognized" in data["error_message"]

def test_retryguard_duplicate_detection(client):
    """Test 3: Duplicate payment warnings trigger when unconfirmed payment exists."""
    # Transaction A is already unconfirmed ₹4,000 to merch_grocery_01
    res = client.post("/api/scan/resolve", json={"qr_content": "merch_grocery_01"})
    assert res.status_code == 200
    data = res.json()
    dup = data["duplicate_check"]
    assert dup["has_potential_duplicate"] is True
    assert "RetryGuard Alert" in dup["warning_message"]

def test_network_interruption_does_not_fail_payment(client):
    """Test 4: Frontend network interruption does not automatically mark payment FAILED."""
    res = client.post("/api/payments/tx_demo_4000_grocery/verify", json={"simulate_network_drop": True})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] != "FAILED"
    assert "Client network dropped" in data["message"]

def test_provider_confirmed_success_remains_success(client):
    """Test 5: Provider-confirmed successful payment remains SUCCESS."""
    res = client.get("/api/payments/tx_demo_750_cafe")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"

def test_debit_reported_enters_investigation(client):
    """Test 6: Debit-reported/receiver-unknown cases enter the investigation workflow."""
    res = client.get("/api/payments/tx_demo_4000_grocery/journey")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OUTCOME_UNKNOWN"
    assert data["rescue_card"]["case_number"] is not None
    assert len(data["money_journey"]) > 0
    assert len(data["ai_resolution_journey"]) > 0

def test_mcp_tool_execution():
    """Test 7 & 9: Real MCP tool execution and Idempotency."""
    async def run():
        res1 = await RaahMCPClient.call_tool("get_applicable_reversal_policy", {"category": "UPI_P2M"})
        assert res1["tat_working_days"] == 5

        # Test case creation idempotency
        case_res1 = await RaahMCPClient.call_tool("create_resolution_case", {
            "transaction_id": "tx_demo_4000_grocery",
            "reason": "Test duplicate creation"
        })
        assert case_res1["success"] is True
        assert case_res1.get("already_exists") is True
    asyncio.run(run())

def test_timelines_remain_separate(client):
    """Test 11 & 12: Money Journey (Timeline A) and AI Resolution Journey (Timeline B) remain separate."""
    res = client.get("/api/payments/tx_demo_4000_grocery/journey")
    assert res.status_code == 200
    data = res.json()
    money_j = data["money_journey"]
    ai_j = data["ai_resolution_journey"]
    
    # Timeline A sources must be financial/system entities
    sources = [m["source"] for m in money_j]
    assert any("BANK" in s or "CLIENT" in s or "MERCHANT" in s for s in sources)
    
    # Timeline B agent types must be AI agents
    agent_types = [a["agent_type"] for a in ai_j]
    assert all("RAAH" in a for a in agent_types)

def test_pulse_incident_correlation(client):
    """Test 13: Raah Pulse links related synthetic failures into shared incident."""
    res = client.get("/api/incidents")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    inc = data[0]
    assert inc["bank"] == "HDFC Bank"
    assert inc["affected_count"] >= 10

def test_honest_unknown_evaluation(client):
    """Test 14: Insufficient evidence produces an honest UNKNOWN result without hallucinating."""
    res = client.get("/api/payments/tx_demo_4000_grocery/journey")
    assert res.status_code == 200
    data = res.json()
    card = data["rescue_card"]
    assert "missing" in card["what_remains_unknown"].lower()
    # Regulatory deadline must explain it is not a guaranteed credit timestamp
    assert "not a guaranteed credit timestamp" in card["regulatory_explanation"].lower()

def test_chat_persistence_and_no_hallucination(client):
    """Test 15: Customer can reopen a saved chat conversation and receive verified facts."""
    res = client.get("/api/chat/sessions")
    assert res.status_code == 200
    sessions = res.json()
    assert len(sessions) > 0
    sess_id = sessions[0]["id"]

    # Post message
    msg_res = client.post(f"/api/chat/sessions/{sess_id}/messages", json={
        "content": "Why did my payment fail?",
        "transaction_id": "tx_demo_4000_grocery"
    })
    assert msg_res.status_code == 200
    bot_msg = msg_res.json()
    assert "Payer Debit: Confirmed" in bot_msg["content"]
    assert len(bot_msg["tool_calls"]) > 0

def test_e2e_main_case_flow(client):
    """End-to-End Integration Test for Main ₹4,000 Case."""
    # 1. Check scan
    scan = client.post("/api/scan/resolve", json={"qr_content": "merch_grocery_01"}).json()
    assert scan["valid"] is True

    # 2. Check journey
    journey = client.get("/api/payments/tx_demo_4000_grocery/journey").json()
    assert journey["amount"] == 4000.0
    assert journey["rescue_card"]["last_verified_status"] == "OUTCOME_UNKNOWN"

    # 3. Trigger simulated reversal completion (Scenario 5)
    scen_res = client.post("/api/demo/scenarios/5/trigger", json={"amount": 4000.0}).json()
    assert scen_res["status"] == "REVERSED"

    # 4. Verify journey now reflects refund credit
    updated_journey = client.get("/api/payments/tx_demo_4000_grocery/journey").json()
    assert updated_journey["status"] == "REVERSED"
    assert any(e["event_type"] == "REVERSAL_COMPLETED" for e in updated_journey["money_journey"])

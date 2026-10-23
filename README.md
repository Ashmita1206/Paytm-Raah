# RAAH — Autonomous Payment Intelligence & Recovery
### Paytm Build for India AI Hackathon — Track 3: Autonomous AI Teammates
**Tagline:** *Scan with confidence. Resolve with intelligence.*

---

## 1. Executive Summary & Product Vision

Imagine a customer initiates a **₹4,000 UPI payment** through a QR scanner at a grocery store. Their bank reports that money has been debited, but the merchant does not receive confirmation. Today, the customer is forced to become the investigator: guessing if the transaction succeeded, wondering whether another attempt will double-debit them, and repeatedly calling customer support.

**RAAH** introduces an autonomous payment resolution layer designed for seamless integration into the Paytm ecosystem. Instead of a passive chatbot that merely dispenses generic FAQs, RAAH acts as two connected **Autonomous AI Teammates**:

1. **Raah Rescue (Customer Teammate):** Automatically takes ownership of uncertain payments, gathers authoritative evidence across payment gateways and banks, prevents accidental duplicate debits (**RetryGuard**), enforces RBI turnaround policies (T+5/T+1), registers persistent recovery cases, schedules background re-checks, and verifies refund outcomes.
2. **Raah Pulse (Operations Teammate):** Continuously ingests cross-transaction failure telemetry, detects anomalous clusters across banks (e.g., 12 HDFC timeout failures), creates shared operational incidents, correlates individual customer cases to prevent ticket fragmentation, and recommends dynamic routing mitigations.
3. **Ask Raah (Contextual Chat):** Floating AI interface providing natural-language inquiry backed by real-time Model Context Protocol (MCP) tool executions—strictly grounded in verified evidence with zero hallucinations.

---

## 2. System Architecture

RAAH is built as a clean, production-grade monorepo:

```
raah/
├── mobile/                     # React Native Expo Android mobile application
│   ├── src/
│   │   ├── components/         # PaytmHeader, RescueCard, TimelineMoney, TimelineRescue, AskRaahModal, RetryGuardModal, ScenarioDrawer
│   │   ├── screens/            # HomeScreen, ScannerScreen, PaymentResultScreen, PaymentRescueScreen, PulseOperationsScreen
│   │   ├── services/           # ApiService with auto-fallback (10.0.2.2 emulator, LAN IP, localhost)
│   │   ├── theme/              # Curated Paytm color system (#002970, #00BAF2, etc.)
│   │   └── navigation/         # RootStackParamList & NativeStackNavigator
│   ├── android/                # Native Android Gradle project (generated via Expo prebuild)
│   └── app.json                # Camera permissions and Android package config (com.paytm.raah)
│
├── backend/                    # Python 3.11+ FastAPI Server
│   ├── app/
│   │   ├── agents/             # LangGraph StateGraph (rescue_agent) & Raah Pulse telemetry agent (pulse_agent)
│   │   ├── mcp_servers/        # Official MCP Python SDK v2 (MCPServer) exposing 10 authorized payment tools
│   │   ├── policies/           # Deterministic RBI Failed-Transaction Harmonisation Policy Engine
│   │   ├── models/             # SQLAlchemy normalized models (Transaction, PaymentEvent, ResolutionCase, IncidentRecord, etc.)
│   │   ├── schemas/            # Pydantic v2 validation models
│   │   ├── services/           # RetryGuard duplicate engine & background FollowupWorker
│   │   ├── demo/               # 8 synthetic scenarios engine & realistic data seeder
│   │   ├── api/                # REST endpoints for Scan, Payments, Cases, Pulse, Chat, Demo, and Webhooks
│   │   └── main.py             # FastAPI entrypoint with background scheduler lifespan
│   ├── tests/                  # Automated pytest suite covering all 18 hackathon acceptance tests
│   └── requirements.txt
│
├── docs/
│   └── qr_codes/sample_qrs.html # Scannable high-resolution test merchant QR codes
├── .env.example
└── README.md
```

---

## 3. Tech Stack & Standards

- **Mobile:** React Native (TypeScript), Expo SDK 58, `expo-camera` (native camera scanning), React Navigation Stack, React Native Safe Area Context, Vector Icons.
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite (production-ready normalized schema), Pydantic v2, Uvicorn.
- **Agentic AI & Protocol:** Official **MCP Python SDK v2** (`from mcp.server.mcpserver import MCPServer`), **LangGraph** StateGraph with `MemorySaver` checkpointing, and deterministic policy guardrails.
- **Design System:** Pixel-perfect Paytm payment aesthetics: white cards, deep blue (`#002970`), cyan accents (`#00BAF2`), crisp typography, status pills, and minimal shadows.

---

## 4. Key Genuinely Working Features

### Feature A: Smart QR Scan & RetryGuard Protection
- **Real Native Camera:** Live QR scanner using `expo-camera` with animated reticle, torch toggle, and fallback demo selector.
- **RetryGuard Pre-Flight Check:** Scans recent transactions for the same merchant, user, and amount within a 15-minute window. If an unconfirmed payment exists, it interrupts the flow with a clear warning:
  > *"RetryGuard Alert: Your previous ₹4,000 payment to this merchant initiated 2 minute(s) ago is still unconfirmed. Please verify its outcome before paying again."*
- **User Agency:** Provides options to *"Track & Resolve Previous Payment"*, *"Cancel"*, or *"Continue with Acknowledgement"*.

### Feature B: Flagship Raah Rescue Journey
- **Two Independent Timelines:**
  - **Timeline A (Money Journey):** Strictly reflects verified evidence from financial systems: Initiated → Payer Account Debited → Gateway Processing → Beneficiary Confirmation Missing → Reversal Credited.
  - **Timeline B (AI Resolution Journey):** Displays audited autonomous actions: Investigation Initiated → Authoritative Status Retrieved via MCP → Merchant POS Queried → RBI Policy Matched (T+5) → Case Created → Background Follow-up Scheduled.
- **Payment Rescue Information Card:** Displays known facts, current unknowns, regulatory turnaround date, statutory compensation rate (₹100/day after TAT), and assigned case ID (`CASE-2026-8941`).
- **Zero Hallucinations:** Clearly states regulatory deadlines rather than fabricating exact money-arrival timestamps.

### Feature C: Raah Pulse (Operations Teammate)
- **Anomaly Detection:** Groups failures by `(payer_bank, gateway, error_code)` across sliding time windows.
- **Cross-Transaction Incident Correlation:** Flags spikes (e.g., 31.6% observed timeout rate vs. 1.2% baseline on HDFC UPI) and automatically correlates affected individual customer recovery cases (`INC-2026-042`).
- **Support Operations Workspace:** Allows operations leads to review telemetry, apply dynamic routing traffic diversion, and broadcast advisories.

### Feature D: Ask Raah Contextual AI Assistant
- Context-aware chatbot linked to the currently viewed transaction.
- Directly invokes authorized MCP tools:
  - `get_transaction_status`
  - `get_merchant_confirmation`
  - `get_applicable_reversal_policy`
  - `create_resolution_case`
- Visible tool execution accordion shows judges exactly which MCP tools were called and their verified payloads.

---

## 5. Quick Start & Setup Instructions

### Prerequisites
- Node.js v18+ and npm v9+
- Python 3.11+
- Git

### Step 1: Run the FastAPI Backend

```bash
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# (Or create fresh venv if setting up on a new machine)
# python -m venv venv
# .\venv\Scripts\Activate.ps1
# pip install -r requirements.txt

# 3. Start the FastAPI server (runs on port 8000)
$env:PYTHONPATH = "d:\paytm raah\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will automatically initialize the database, seed realistic demo records, and start the autonomous background worker. You can verify health at `http://127.0.0.1:8000/health` and view OpenAPI docs at `http://127.0.0.1:8000/docs`.

### Step 2: Run Automated Acceptance Tests

```bash
cd backend
$env:PYTHONPATH = "d:\paytm raah\backend"
pytest -v tests/test_raah_core.py
```
*All 12 comprehensive unit and end-to-end integration tests will pass.*

### Step 3: Run the Android Mobile Application

```bash
# In a new terminal, navigate to mobile directory
cd mobile

# Start Expo dev server
npx expo start
```
- Press **`a`** to launch on connected Android device or Android Emulator.
- Press **`w`** to inspect the UI in your web browser.
- Or scan the Expo QR code using the Expo Go / Development client app on your physical Android phone.

---

## 6. How to Trigger the 8 Simulated Scenarios

Open the in-app **Demo Control Center** (flask icon in the header) or invoke the backend REST endpoints:

| # | Scenario Name | API Trigger Endpoint | Expected Behavior |
|---|---------------|----------------------|-------------------|
| **1** | Payment Fails Before Debit | `POST /api/demo/scenarios/1/trigger` | Gateway pre-debit rejection; verifies customer safe to retry without duplicate risk. |
| **2** | Payment Succeeds, Client Response Lost | `POST /api/demo/scenarios/2/trigger` | Client missed receipt; backend verifies merchant credit, marks SUCCESS without fake reversal. |
| **3** | Debit Reported, Beneficiary Missing *(Flagship)* | `POST /api/demo/scenarios/3/trigger` | Starts Raah Rescue workflow, registers Case `CASE-2026-8941`, schedules background follow-up. |
| **4** | Reversal Initiated, Credit Pending | `POST /api/demo/scenarios/4/trigger` | Switch registers automated reversal batch; updates Timeline A with in-transit state. |
| **5** | Verified Reversal Completion Arrives | `POST /api/demo/scenarios/5/trigger` | Payer bank confirms refund credit; updates Timeline A and resolves case in Timeline B. |
| **6** | HDFC Cluster Spike (Raah Pulse) | `POST /api/demo/scenarios/6/trigger` | Injects 12 bank timeout failures; Raah Pulse creates Incident `INC-2026-042` and correlates cases. |
| **7** | Duplicate Payment Attempt | `POST /api/demo/scenarios/7/trigger` | User attempts to pay ₹4,000 again; RetryGuard detects unconfirmed attempt and halts flow. |
| **8** | Case Becomes Overdue Under RBI Policy | `POST /api/demo/scenarios/8/trigger` | Regulatory TAT (T+5) expires; flags statutory compensation (₹100/day) and escalates. |

---

## 7. Demo Merchant QR Codes

Open `docs/qr_codes/sample_qrs.html` in your browser to view and scan live QR codes:
- **Demo Fresh Grocery Store (₹4,000):** `upi://pay?pa=grocery@paytm&pn=Demo+Fresh+Grocery+Store&am=4000`
- **Demo Artisanal Cafe (₹750):** `upi://pay?pa=cafe@paytm&pn=Demo+Artisanal+Cafe&am=750`
- **Demo City Medico Pharmacy (₹1,200):** `upi://pay?pa=pharmacy@paytm&pn=Demo+City+Medico+Pharmacy&am=1200`

---

## 8. Honest Boundaries & Current Limitations

1. **No Live Money Processing:** RAAH strictly uses test modes and synthetic simulation. Real UPI PINs and banking passwords are never requested or stored.
2. **Deterministic Financial Truth:** The LLM assists with natural-language understanding and operational summaries, but all financial states, timelines, and turnaround times are strictly enforced by deterministic backend systems.
3. **Correlation vs. Causation:** Raah Pulse presents failure clusters as correlated telemetry and dynamic routing opportunities, never claiming unverified proof of sole bank culpability.

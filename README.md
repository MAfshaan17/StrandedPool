# 🚆 StrandedPool
### Predict, Pool & Recover Travel Disruptions with AI

**StrandedPool is an AI-powered travel disruption recovery system that helps stranded travellers find alternatives, protect downstream bookings, and coordinate recovery for entire groups—not just individuals.**

When a train is cancelled, a flight is delayed, or severe weather disrupts travel, passengers often struggle to find alternatives while seats become scarce and prices rise. StrandedPool combines AI agents, real-time travel data, constraint-based optimization, and group pooling to make recovery faster, smarter, and more accessible.

> **Our vision:** Turn travel disruptions into coordinated recovery plans instead of individual travel emergencies.

---

## 🌟 The Problem

Travel disruptions create a chain reaction. A cancelled train can cause missed cab pickups, hotel check-ins, connecting journeys, and appointments.

Existing travel tools often focus on helping one traveller at a time. During a large disruption, hundreds of passengers may compete for the same buses, taxis, and hotel rooms.

Travellers need a system that can:

- Detect or identify travel disruptions.
- Find affected bookings and downstream consequences.
- Discover alternative routes and transport options.
- Respect individual budgets, deadlines, and destinations.
- Coordinate travellers with similar needs.
- Generate a clear recovery itinerary with actionable next steps.

## 💡 Our Solution

StrandedPool uses a hybrid AI architecture combining language models with deterministic optimization and verified data sources.

### 🔮 1. Predict

- Analyze weather forecasts and route-related risk signals.
- Warn travellers about potential disruptions when supported data is available.
- Help travellers explore alternatives before options become scarce.

### 👥 2. Pool

- Group affected travellers by destination, schedule, and constraints.
- Identify opportunities for shared cab journeys.
- Allocate available alternatives across travellers instead of recommending the same scarce option to everyone.
- Aggregate unmet demand to help operators evaluate the need for additional transport.

### 🌐 3. Reach Everyone

- Conversational interface for English, Hindi, and Kannada.
- Voice-input support for seniors, families, pilgrims, and other travellers.
- Clear explanations and step-by-step recovery guidance.

### 🧭 4. Recover

- Analyze affected train, flight, cab, hotel, and appointment bookings.
- Rank alternatives according to budget, timing, destination, and availability.
- Generate an original-versus-recovered itinerary.
- Draft hotel late-check-in messages, refund requests, and pickup updates.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| Disruption detection | Identify or simulate delays, cancellations, and weather-related disruptions. |
| Booking cascade analysis | Determine which downstream bookings may be affected. |
| Alternative discovery | Search supported data sources for alternative transport and accommodation. |
| Constraint-based ranking | Rank options using cost, travel time, deadlines, and traveller preferences. |
| Group pooling | Identify compatible travellers and propose shared transport. |
| Recovery itinerary | Present the original journey alongside the proposed recovery plan. |
| Action pack | Generate ready-to-review messages for hotels, transport providers, and refund requests. |
| Multilingual assistance | Support conversational recovery workflows in English, Hindi, and Kannada. |

---

## 🏗️ System Architecture

```text
              Traveller
             Chat / Voice
                  |
                  v
          Frontend: Next.js
                  |
                  v
           FastAPI Backend
                  |
                  v
          AI Agent Orchestrator
                  |
       +----------+-----------+
       |          |           |
       v          v           v
  Disruption   Cascade    Alternative
   Detector    Analyzer   Discovery
       |          |           |
       +----------+-----------+
                  |
                  v
        Scoring & Pooling Engine
        (Python / OR-Tools)
                  |
                  v
          Itinerary Builder
                  |
                  v
           Action Drafter
                  |
                  v
       Recovery Itinerary
         + Action Pack
```

### Hybrid AI Design

StrandedPool separates data-backed decisions from language generation.

- **Deterministic backend:** filters available options, calculates costs, checks constraints, ranks alternatives, and manages group allocations.
- **AI agent:** interprets natural-language requests, selects appropriate tools, explains recommendations, and drafts messages.
- **External data connectors:** retrieve information from supported transport, weather, and mapping services.
- **Database:** stores traveller preferences, bookings, alternatives, pool assignments, and recovery plans.

The AI must not invent seat availability, fares, train status, or hotel inventory. If reliable information is unavailable, the system should clearly identify the limitation.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | React / Next.js |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| AI integration | Gemini API or another supported LLM API |
| Optimization | Python, OR-Tools or custom constraint-based logic |
| Database | SQLite for MVP; PostgreSQL for production |
| Weather | Open-Meteo API |
| Railway data | Authorized railway APIs or Qrail, subject to endpoint access |
| Flight data | Amadeus Self-Service APIs, subject to quota and environment |
| Maps and routing | OpenStreetMap-based services or Google Maps Platform |
| Voice input | Browser speech recognition or a compatible speech-to-text service |

### 🌍 Real-World Data Strategy

StrandedPool is designed to integrate real data wherever authorized access is available.

- **Weather:** Open-Meteo provides weather forecasts and related environmental data.
- **Railways:** Evaluate Qrail and official railway data services for supported train information.
- **Flights:** Use Amadeus APIs for supported flight searches and test-environment demonstrations.
- **Routes:** Use OpenStreetMap-based routing services or Google Maps Platform.
- **Bus, cab, and hotel inventory:** Integrate authorized operator or booking-partner APIs when available.

**Important:** Free quotas, API keys, live-data access, commercial-use permissions, and booking capabilities vary by provider. A test API response is not proof of live availability. The application should identify live, cached, simulated, and unavailable data separately.

---

## 🤖 AI Agent Tools

The agent orchestrator can use the following tools:

| Tool | Responsibility |
|---|---|
| `detect_disruption()` | Identify or simulate a travel disruption. |
| `find_affected_bookings()` | Find bookings affected by the disruption. |
| `search_alternatives()` | Retrieve available alternatives from connected sources. |
| `score_options()` | Rank alternatives using traveller constraints. |
| `pool_travellers()` | Group compatible travellers and propose shared transport. |
| `build_itinerary()` | Generate the proposed recovery itinerary. |
| `draft_actions()` | Prepare messages and recommended next steps. |

These tools should execute through validated backend functions. The LLM should not directly determine factual availability or bypass constraint checks.

---

## 🔄 Example Workflow

Consider a train cancellation affecting travellers on the Mangaluru–Udupi corridor.

1. **Detect:** The system receives a verified disruption update or a simulated event.
2. **Analyze:** It identifies passengers whose onward journeys, pickups, or hotel check-ins may be affected.
3. **Search:** It retrieves supported bus, train, route, or other alternatives.
4. **Evaluate:** It filters and ranks options according to budget, timing, destination, and availability.
5. **Pool:** It identifies compatible travellers and proposes shared cabs or alternative allocations.
6. **Recover:** Each traveller receives a personalized itinerary and an action pack.

If 42 travellers need to reach Udupi, StrandedPool can aggregate their demand, allocate available options where feasible, and expose any unmet demand to transport operators.

The system does not assume that an extra bus can be booked automatically; that requires operator participation or an authorized booking integration.

---

## 📊 Impact and Evaluation

StrandedPool can be evaluated using a reproducible disruption simulation and, where available, real API data.

Suggested evaluation metrics:

- Percentage of travellers successfully assigned a feasible alternative.
- Average additional recovery cost per traveller.
- Average time required to generate a recovery plan.
- Number of downstream bookings identified before they are missed.
- Number of compatible shared-cab groups formed.
- Percentage of recommendations satisfying all hard constraints.

Compare individual recommendations against group-aware pooling using the same initial bookings, available alternatives, and budget constraints.

**Results should be reported only after running the simulation or evaluation.** Any simulated measurements must be labelled as simulated rather than presented as real-world outcomes.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or a compatible supported version.
- Node.js and npm.
- Git.
- API keys for whichever external providers you choose to integrate.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd StrandedPool
```

### 2. Set up the backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

If you already have a compatible venv, reuse it and run the install, migration, and server commands from the `backend` directory.

The API documentation and health checks are available at:

```text
http://localhost:8000/docs
http://localhost:8000/health
http://localhost:8000/api/health/ready
```

### 3. Set up the frontend

Create `frontend/.env.local` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`, then run:

```powershell
cd ..\frontend
npm ci
npm run dev -- --port 3001
```

Open `http://localhost:3001`.
If port 3001 is occupied, use `npm run dev -- --port 3002` instead.

---

## 🔐 Environment Variables

The backend uses safe local defaults. Optionally copy `backend/.env.example` to `backend/.env` to customize:

```env
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:3001
DATABASE_URL=sqlite+aiosqlite:///./strandedpool.db
```

The frontend defaults to `http://localhost:8000`; set `NEXT_PUBLIC_API_BASE_URL` only if the backend uses a different address. No third-party API keys are currently used.

Never commit `.env` files, API secrets, personal booking information, or access tokens to GitHub. Use environment variables and a committed `.env.example` containing placeholders.

### MVP scope and data accuracy

- Journey and booking details, disruption reports, and alternative options are stored in local SQLite.
- Disruption reports and traveller-entered transport alternatives are explicitly unverified.
- Alternative ranking is deterministic and uses the destination, stated budget, and arrival deadline when supplied.
- Pooling matches are proposals based on destination and departure time only; they do not confirm consent, vehicle capacity, fare, or availability.
- There is no live transport provider, authentication, encryption, or booking execution in this MVP. Do not enter booking references or sensitive personal information.

---

## 🧪 Testing and Reliability

Before deploying StrandedPool, validate:

- Disruption detection with both valid and invalid inputs.
- Booking cascade analysis for multiple connecting bookings.
- Budget, deadline, destination, and availability constraints.
- Group assignments without exceeding stated transport capacity.
- API timeouts, rate limits, missing data, and expired credentials.
- AI-generated messages and itinerary consistency.
- Authentication, input validation, and protection of traveller information.

Use mock fixtures for repeatable automated tests, even when production integrations use real data. Mock data is useful for testing; it should not be confused with live travel inventory.

---

## 📈 Business Model

StrandedPool follows a potential B2B2C model.

- **Operator subscriptions:** dashboards and disruption-recovery tools for transport operators.
- **Recovery commissions:** potential commissions from participating booking and mobility partners.
- **Enterprise plans:** custom integrations for travel agencies, tour operators, pilgrimage organizers, and corporate travel teams.
- **Demand intelligence:** aggregated disruption and unmet-demand insights, subject to privacy and contractual requirements.

### Scalability Roadmap

1. **Coastal Karnataka:** validate rail disruptions and alternative journeys around the Konkan corridor.
2. **Regional expansion:** integrate additional bus, rail, and flight data sources.
3. **National coverage:** support multiple transport modes, larger traveller groups, and operator integrations.
4. **Broader applications:** airport disruptions, pilgrimage crowds, tourism, corporate travel, and other group journeys.

This is a proposed roadmap, not a claim that all integrations or deployments are already operational.

---

## 🔮 Future Enhancements

- Proactive disruption-risk alerts.
- Better multilingual speech recognition and voice responses.
- More advanced constraint optimization for large groups.
- Authorized booking and rebooking integrations.
- Notifications for itinerary changes.
- Operator dashboards for aggregated demand and alternative capacity.
- Privacy-preserving analytics and production-grade monitoring.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request with a clear description.

Potential contribution areas include API connectors, optimization algorithms, frontend accessibility, automated tests, multilingual support, and documentation.

---

## 🔒 Privacy and Safety

Travel bookings may contain personal information. StrandedPool should collect only the data necessary for recovery, protect credentials, restrict access to booking details, and avoid exposing individual traveller information in group-demand reports.

Recommendations must distinguish confirmed availability from estimates. Travellers should review consequential booking changes before they are executed unless a properly authorized integration and consent flow explicitly supports automated actions.

---

## 👥 Team and Links

- **Project:** StrandedPool
- **Problem Statement:** PS 4.1 — AI Agent for Travel Disruption Recovery
- **Team:** Add your team name and member details.

  

**StrandedPool — Predict. Pool. Recover.**

*Helping travellers move forward when journeys go off track.*

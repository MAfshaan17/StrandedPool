# 🚆 StrandedPool
### Travel disruption recovery, together

**StrandedPool is an early-stage travel recovery MVP.** It provides account-scoped journeys, booking dependency/cascade analysis, explicit disruption simulations, hard-constraint filtering for traveller-entered alternatives, opt-in anonymized pooling proposals, and Open-Meteo forecast risk estimates. Live transport inventory, booking execution, the Gemini assistant, and the broader product vision are not implemented yet.

The long-term product vision is to help travellers find authorized alternatives, protect downstream bookings, and coordinate recovery for groups—not just individuals.

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

## 💡 Product Direction

The intended product uses a hybrid architecture combining language models with deterministic optimization and verified data sources. The current implementation status is summarized under [Key Features](#-key-features) and [MVP scope and data accuracy](#mvp-scope-and-data-accuracy).

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
| Disruption reports | Save traveller-reported disruptions; these are not verified against transport operators. |
| Weather forecast | View a six-hour Open-Meteo forecast and transparent estimated weather-risk indicator. |
| Booking cascade analysis | Link bookings and analyze delayed/cancelled journeys; outputs are schedule-based estimates and do not change bookings. |
| Alternative discovery | Live transport search reports when no authorized provider is configured; traveller-entered options can be ranked. |
| Constraint-based ranking | Excludes options with a mismatched destination, unknown/over-budget fare when a budget is set, or unknown/late arrival when a deadline is set. Feasible options use configurable 40/35/15/10 cost/time/reliability/convenience weights. |
| Group pooling | Proposes anonymized matches only when both journeys opt in and origin, destination, and departure window match. Capacity/fare are not verified. |
| Recovery itinerary | Shows saved reports, bookings, feasible alternatives, and next steps. Cascade analysis is available as a separate labelled simulation or analysis call. |
| Action pack | Not implemented yet; messages are not sent or automatically drafted. |
| Multilingual assistance | Not implemented yet. |
| Authentication | Registration/login, PBKDF2 password hashes, signed one-hour bearer tokens, and owner-scoped journey endpoints. |

### Implemented weather integration

`GET /api/v1/weather/forecast?location=Mangaluru` geocodes the requested place and retrieves hourly precipitation probability, precipitation, wind speed, and weather codes from Open-Meteo. The API returns the next six forecast hours and a deterministic low/moderate/high risk estimate with the thresholds and contributing factors in the response. Results are cached in process memory for 15 minutes. If the provider is unavailable, the endpoint returns an explicit unavailable result or clearly labelled stale cached data.

Open-Meteo forecasts are weather forecasts, not transport status. The risk estimate does not confirm a service delay, cancellation, or unsafe route. Open-Meteo's public forecast API does not require a key for this integration.

### Booking dependencies and disruption analysis

Create bookings with schedule timestamps that include a UTC offset, then link predecessor and downstream bookings with:

```text
POST /api/journeys/{journey_id}/bookings/{booking_id}/dependencies
{"downstream_booking_id": 2, "dependency_type": "pickup"}
```

Analyze a reported delay/cancellation with `POST /api/v1/disruptions/analyze`, or use `POST /api/v1/disruptions/simulate` to explicitly label a demo simulation. A delay requires `delay_minutes`. The analyzer traverses the booking graph, detects cycles, and identifies downstream connections that appear missed or at risk. It never cancels or changes a booking, and cannot verify traveller-entered times.

### Authentication and data ownership

Journey, booking, disruption, recovery, dashboard, and alternative endpoints require a bearer token obtained from `POST /api/auth/register` or `/api/auth/login`. Passwords are PBKDF2-SHA256 hashed; access tokens expire after one hour. The UI holds the token in browser `sessionStorage`. Login and registration have an in-process IP rate limit, which is not shared across multiple backend instances.

For local development, the backend generates an ephemeral signing key when `AUTH_SECRET_KEY` is unset; tokens become invalid after a backend restart. For production, configure a stable randomly generated secret of at least 32 characters and use HTTPS. The value in `.env.example` is only a placeholder and must be replaced. The existing MVP does not encrypt stored trip details at rest or support password reset/email verification.

The account-ownership migration leaves pre-existing journeys and disruption reports with a null owner so they are not exposed to newly registered accounts. Those legacy records remain in SQLite but are not visible through account-scoped APIs; back them up and plan an explicit ownership/claim migration before using existing data with accounts.

---

## 🏗️ Target System Architecture

The diagram below describes the planned architecture; several components are not implemented in the current MVP.
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

- **Weather:** The MVP calls Open-Meteo geocoding and forecast endpoints without an API key; results and estimated risk are not transport alerts.
- **Railways:** Evaluate Qrail and official railway data services for supported train information.
- **Flights:** Use Amadeus APIs for supported flight searches and test-environment demonstrations.
- **Routes:** Use OpenStreetMap-based routing services or Google Maps Platform.
- **Bus, cab, and hotel inventory:** Integrate authorized operator or booking-partner APIs when available.

**Important:** Free quotas, API keys, live-data access, commercial-use permissions, and booking capabilities vary by provider. A test API response is not proof of live availability. The MVP currently has no connected live transport inventory, railway status, flight status, routing, or accommodation provider.

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
- API keys only for optional providers you later configure; the current Open-Meteo forecast integration does not require one.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd StrandedPool
```

### 2. Set up the backend

```powershell
cd backend
py -3 -m venv .venv
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

Create `backend/.env` from `.env.example` if desired, and replace the placeholder before relying on authentication across backend restarts. In production set `APP_ENV=production` and a stable `AUTH_SECRET_KEY`.

### 3. Set up the frontend

Create `frontend/.env.local` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`, then run:

```powershell
cd ..\frontend
npm ci
npm run dev -- --port 3001
```

Open `http://localhost:3001`.
If port 3001 is occupied, use `npm run dev -- --port 3002` instead.
If both are occupied, use the next free port (CORS also allows port 3003).

---

## 🔐 Environment Variables

The backend uses safe local defaults. Optionally copy `backend/.env.example` to `backend/.env` to customize:

```env
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:3001,http://localhost:3002,http://localhost:3003
DATABASE_URL=sqlite+aiosqlite:///./strandedpool.db
```

The frontend defaults to `http://localhost:8000`; set `NEXT_PUBLIC_API_BASE_URL` only if the backend uses a different address. The current weather integration needs no API key; no transport, AI, or mapping credentials are configured.

Never commit `.env` files, API secrets, personal booking information, or access tokens to GitHub. Use environment variables and a committed `.env.example` containing placeholders.

### MVP scope and data accuracy

- Journey and booking details, disruption reports, and alternative options are stored in local SQLite.
- Weather forecasts are fetched from Open-Meteo and cached in process memory for 15 minutes; no weather history is persisted.
- Disruption reports and traveller-entered transport alternatives are explicitly unverified.
- Alternative scoring is deterministic and excludes options that fail destination, budget, or arrival-deadline hard checks; the underlying traveller-entered data is still unverified.
- Scoring weights are configurable through `COST_SCORE_WEIGHT`, `TIME_SCORE_WEIGHT`, `RELIABILITY_SCORE_WEIGHT`, and `CONVENIENCE_SCORE_WEIGHT`; the values must sum to 1. Reliability for traveller-entered options is discounted because it is unverified.
- Pooling is opt-in on both journeys and results are anonymized; proposals do not confirm vehicle capacity, fare, seat availability, or reservations.
- Booking-cascade analysis supports dependency graphs and detects cycles; it uses entered schedule times and never changes bookings.
- Authentication scopes journey APIs to the account. The bearer token is stored in browser session storage, and data is not encrypted at rest.
- There is no live transport provider, AI assistant, booking execution, password reset, or email verification. Do not enter booking references or sensitive personal information.

### Reproducible cascade demo

1. Register or sign in on the frontend.
2. Add a journey and one or more bookings. Include each booking's scheduled start/end with offsets.
3. Link bookings in sequence using the dependency form.
4. Select **Simulate cancellation** on the first booking.
5. Review the cascade statuses; the response is labelled `SIMULATED` and does not alter stored booking status.

The simulation uses only the journey's saved booking data. It does not create fake transport inventory or provider confirmations.

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

Run the backend tests from `backend` with `.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp tests`. Run frontend checks from `frontend` with `npm run lint` and `npm run build`. The weather tests use mocked provider responses for repeatability; do not confuse simulated test data with live transport inventory.

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

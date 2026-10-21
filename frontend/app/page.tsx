"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  apiRequest,
  Alternative,
  ActionDraft,
  AuthResponse,
  BookingDependency,
  CascadeAnalysis,
  Dashboard,
  JourneyBooking,
  RecoveryItinerary,
  RecoveryPlan,
  SavedRecoveryPlanSummary,
  TransportSearchResult,
  WeatherForecast,
} from "../lib/api";
import LocationPicker from "../components/LocationPicker";

function toIsoDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw new Error("Enter a valid date and time.");
  }
  return date.toISOString();
}

function formatDate(value: string | null): string {
  if (!value) return "Not provided";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}

function formatFare(value: number | null): string {
  return value === null ? "Not provided" : value.toLocaleString();
}

export default function Home() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [selectedJourneyId, setSelectedJourneyId] = useState("");
  const [recovery, setRecovery] = useState<RecoveryPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [apiError, setApiError] = useState("");
  const [notice, setNotice] = useState("");
  const [journeyError, setJourneyError] = useState("");
  const [disruptionError, setDisruptionError] = useState("");
  const [alternativeError, setAlternativeError] = useState("");
  const [bookingError, setBookingError] = useState("");
  const [searchMessage, setSearchMessage] = useState("");
  const [searching, setSearching] = useState(false);
  const [weatherLocation, setWeatherLocation] = useState("");
  const [weatherCountryCode, setWeatherCountryCode] = useState("");
  const [weatherForecast, setWeatherForecast] = useState<WeatherForecast | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState("");
  const [cascadeAnalysis, setCascadeAnalysis] = useState<CascadeAnalysis | null>(null);
  const [cascadeError, setCascadeError] = useState("");
  const [analyzingCascade, setAnalyzingCascade] = useState(false);
  const [dependencyError, setDependencyError] = useState("");
  const [actionDraft, setActionDraft] = useState<ActionDraft | null>(null);
  const [actionError, setActionError] = useState("");
  const [draftingAction, setDraftingAction] = useState(false);
  const [selectedAlternativeId, setSelectedAlternativeId] = useState<number | null>(null);
  const [recoveryItinerary, setRecoveryItinerary] = useState<RecoveryItinerary | null>(null);
  const [itineraryError, setItineraryError] = useState("");
  const [generatingItinerary, setGeneratingItinerary] = useState(false);
  const [savedRecoveryPlans, setSavedRecoveryPlans] = useState<SavedRecoveryPlanSummary[]>([]);
  const [selectedSavedPlanId, setSelectedSavedPlanId] = useState("");
  const [savedPlanError, setSavedPlanError] = useState("");

  useEffect(() => {
    setAccessToken(window.sessionStorage.getItem("strandedpool_access_token"));
    setAuthReady(true);
  }, []);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const result = await apiRequest<Dashboard>("/api/dashboard");
      setDashboard(result);
      setApiError("");
      setSelectedJourneyId((current) =>
        result.journeys.some((journey) => String(journey.id) === current)
          ? current
          : result.journeys[0]
            ? String(result.journeys[0].id)
            : "",
      );
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Unable to load the dashboard.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!authReady) return;
    if (!accessToken) {
      setDashboard(null);
      setRecovery(null);
      setLoading(false);
      return;
    }
    void loadDashboard();
  }, [authReady, accessToken, loadDashboard]);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setAuthLoading(true);
    setAuthError("");
    try {
      const result = await apiRequest<AuthResponse>(
        authMode === "register" ? "/api/auth/register" : "/api/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: form.get("email"),
            password: form.get("password"),
          }),
        },
      );
      window.sessionStorage.setItem("strandedpool_access_token", result.access_token);
      setAccessToken(result.access_token);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setAuthLoading(false);
    }
  }

  function signOut() {
    window.sessionStorage.removeItem("strandedpool_access_token");
    setAccessToken(null);
    setDashboard(null);
    setRecovery(null);
    setSelectedJourneyId("");
    setRecoveryItinerary(null);
    setSavedRecoveryPlans([]);
    setSelectedSavedPlanId("");
    setActionDraft(null);
  }

  useEffect(() => {
    if (!selectedJourneyId) {
      setRecovery(null);
      setCascadeAnalysis(null);
      setRecoveryItinerary(null);
      setSavedRecoveryPlans([]);
      setSelectedSavedPlanId("");
      return;
    }
    setCascadeAnalysis(null);
    setRecoveryItinerary(null);
    setSelectedAlternativeId(null);
    setSavedRecoveryPlans([]);
    setSelectedSavedPlanId("");
    setActionDraft(null);
    let active = true;
    apiRequest<RecoveryPlan>(`/api/journeys/${selectedJourneyId}/recovery`)
      .then((plan) => {
        if (active) {
          setRecovery(plan);
          setApiError("");
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setRecovery(null);
          setApiError(error instanceof Error ? error.message : "Unable to load recovery details.");
        }
      });
    return () => {
      active = false;
    };
  }, [selectedJourneyId, dashboard?.journeys.length]);

  useEffect(() => {
    if (!selectedJourneyId) return;
    let active = true;
    setSavedPlanError("");
    apiRequest<SavedRecoveryPlanSummary[]>(
      `/api/v1/journeys/${selectedJourneyId}/recovery-plans`,
    )
      .then((plans) => {
        if (!active) return;
        setSavedRecoveryPlans(plans);
        setSelectedSavedPlanId((current) =>
          plans.some((plan) => String(plan.plan_id) === current)
            ? current
            : plans[0]
              ? String(plans[0].plan_id)
              : "",
        );
      })
      .catch((error: unknown) => {
        if (active) {
          setSavedPlanError(
            error instanceof Error ? error.message : "Unable to load saved recovery plans.",
          );
        }
      });
    return () => {
      active = false;
    };
  }, [selectedJourneyId]);

  async function submitJourney(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setSaving(true);
    setJourneyError("");
    setNotice("");
    const form = new FormData(event.currentTarget);
    try {
      const journey = await apiRequest<{ id: number }>("/api/journeys", {
        method: "POST",
        body: JSON.stringify({
          traveller_name: form.get("traveller_name"),
          origin: form.get("origin"),
          destination: form.get("destination"),
          departure_at: toIsoDate(String(form.get("departure_at"))),
          arrive_by: form.get("arrive_by")
            ? toIsoDate(String(form.get("arrive_by")))
            : null,
          budget_amount: form.get("budget_amount")
            ? Number(form.get("budget_amount"))
            : null,
          budget_currency: form.get("budget_currency"),
          pooling_consent: form.get("pooling_consent") === "on",
          passenger_count: Number(form.get("passenger_count") || 1),
          constraints: String(form.get("constraints") ?? "")
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean),
        }),
      });
      formElement.reset();
      setSelectedJourneyId(String(journey.id));
      setNotice("Journey saved.");
      await loadDashboard();
      setSelectedJourneyId(String(journey.id));
    } catch (error) {
      setJourneyError(error instanceof Error ? error.message : "Unable to save this journey.");
    } finally {
      setSaving(false);
    }
  }

  async function submitDisruption(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setSaving(true);
    setDisruptionError("");
    setNotice("");
    const form = new FormData(event.currentTarget);
    try {
      await apiRequest("/api/disruptions", {
        method: "POST",
        body: JSON.stringify({
          journey_id: selectedJourneyId ? Number(selectedJourneyId) : null,
          title: form.get("title"),
          description: form.get("description"),
          transport_mode: form.get("transport_mode") || null,
        }),
      });
      formElement.reset();
      setNotice("Disruption report saved as unverified.");
      await loadDashboard();
    } catch (error) {
      setDisruptionError(
        error instanceof Error ? error.message : "Unable to save this disruption report.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function submitAlternative(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedJourneyId) return;
    const formElement = event.currentTarget;
    setSaving(true);
    setAlternativeError("");
    setNotice("");
    const form = new FormData(event.currentTarget);
    try {
      const savedAlternative = await apiRequest<Alternative>(
        `/api/journeys/${selectedJourneyId}/alternatives`,
        {
          method: "POST",
          body: JSON.stringify({
            mode: form.get("mode"),
            provider: form.get("provider"),
            origin: form.get("origin"),
            destination: form.get("destination"),
            arrival_at: form.get("arrival_at")
              ? toIsoDate(String(form.get("arrival_at")))
              : null,
            fare_amount: form.get("fare_amount")
              ? Number(form.get("fare_amount"))
              : null,
            currency: form.get("currency"),
            constraints_satisfied: String(form.get("constraints_satisfied") ?? "")
              .split(",")
              .map((value) => value.trim())
              .filter(Boolean),
          }),
        },
      );
      formElement.reset();
      setNotice(
        savedAlternative.feasible
          ? "Alternative saved and included in the feasible ranking. Details are traveller-provided, not verified."
          : `Option saved but excluded from recommendations: ${savedAlternative.rejected_reasons.join(" ")}`,
      );
      setRecovery(await apiRequest<RecoveryPlan>(
        `/api/journeys/${selectedJourneyId}/recovery`,
      ));
    } catch (error) {
      setAlternativeError(
        error instanceof Error ? error.message : "Unable to save this alternative.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function submitBooking(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedJourneyId) return;
    const formElement = event.currentTarget;
    setSaving(true);
    setBookingError("");
    setNotice("");
    const form = new FormData(formElement);
    try {
      await apiRequest<JourneyBooking>(
        `/api/journeys/${selectedJourneyId}/bookings`,
        {
          method: "POST",
          body: JSON.stringify({
            kind: form.get("kind"),
            provider: form.get("provider"),
            details: form.get("details") || null,
            origin: form.get("origin") || null,
            destination: form.get("destination") || null,
            scheduled_start: form.get("scheduled_start")
              ? toIsoDate(String(form.get("scheduled_start")))
              : null,
            scheduled_end: form.get("scheduled_end")
              ? toIsoDate(String(form.get("scheduled_end")))
              : null,
            timezone: form.get("timezone") || "UTC",
            latest_acceptable_arrival: form.get("latest_acceptable_arrival")
              ? toIsoDate(String(form.get("latest_acceptable_arrival")))
              : null,
            price_amount: form.get("price_amount")
              ? Number(form.get("price_amount"))
              : null,
            currency: form.get("currency") || "INR",
          }),
        },
      );
      formElement.reset();
      setNotice("Booking detail saved.");
      setRecovery(await apiRequest<RecoveryPlan>(
        `/api/journeys/${selectedJourneyId}/recovery`,
      ));
    } catch (error) {
      setBookingError(error instanceof Error ? error.message : "Unable to save this booking.");
    } finally {
      setSaving(false);
    }
  }

  async function submitDependency(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedJourneyId) return;
    const form = new FormData(event.currentTarget);
    setSaving(true);
    setDependencyError("");
    try {
      const predecessorId = String(form.get("predecessor_booking_id"));
      await apiRequest<BookingDependency>(
        `/api/journeys/${selectedJourneyId}/bookings/${predecessorId}/dependencies`,
        {
          method: "POST",
          body: JSON.stringify({
            downstream_booking_id: Number(form.get("downstream_booking_id")),
            dependency_type: form.get("dependency_type"),
          }),
        },
      );
      setRecovery(await apiRequest<RecoveryPlan>(
        `/api/journeys/${selectedJourneyId}/recovery`,
      ));
      setNotice("Booking dependency saved.");
    } catch (error) {
      setDependencyError(
        error instanceof Error ? error.message : "Unable to save this dependency.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function simulateCancellation(bookingId: number) {
    if (!selectedJourneyId) return;
    setAnalyzingCascade(true);
    setCascadeError("");
    setCascadeAnalysis(null);
    try {
      setCascadeAnalysis(
        await apiRequest<CascadeAnalysis>("/api/v1/disruptions/simulate", {
          method: "POST",
          body: JSON.stringify({
            journey_id: Number(selectedJourneyId),
            affected_booking_id: bookingId,
            disruption_status: "cancelled",
          }),
        }),
      );
    } catch (error) {
      setCascadeError(
        error instanceof Error ? error.message : "Unable to analyze this disruption.",
      );
    } finally {
      setAnalyzingCascade(false);
    }
  }

  async function submitActionDraft(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedJourney) return;
    const form = new FormData(event.currentTarget);
    setDraftingAction(true);
    setActionError("");
    try {
      setActionDraft(
        await apiRequest<ActionDraft>("/api/v1/actions/draft", {
          method: "POST",
          body: JSON.stringify({
            action: form.get("action"),
            language: form.get("language"),
            provider_name: form.get("provider_name"),
            origin: selectedJourney.origin,
            destination: selectedJourney.destination,
          }),
        }),
      );
    } catch (error) {
      setActionDraft(null);
      setActionError(
        error instanceof Error ? error.message : "Unable to draft this message.",
      );
    } finally {
      setDraftingAction(false);
    }
  }

  async function generateRecoveryItinerary() {
    if (!selectedJourneyId) return;
    setGeneratingItinerary(true);
    setItineraryError("");
    try {
      const itinerary = await apiRequest<RecoveryItinerary>("/api/v1/recovery/generate", {
          method: "POST",
          body: JSON.stringify({
            journey_id: Number(selectedJourneyId),
            selected_alternative_id: selectedAlternativeId,
            ...(cascadeAnalysis
              ? {
                  affected_booking_id: cascadeAnalysis.affected_booking_id,
                  disruption_status: cascadeAnalysis.disruption_status,
                  delay_minutes: cascadeAnalysis.delay_minutes,
                }
              : {}),
          }),
        });
      setRecoveryItinerary(itinerary);
      const summary = {
        plan_id: itinerary.plan_id,
        created_at: itinerary.created_at,
        source_label: itinerary.source_label,
        verification_status: itinerary.verification_status,
      };
      setSavedRecoveryPlans((plans) => [
        summary,
        ...plans.filter((plan) => plan.plan_id !== summary.plan_id),
      ]);
      setSelectedSavedPlanId(String(itinerary.plan_id));
    } catch (error) {
      setRecoveryItinerary(null);
      setItineraryError(
        error instanceof Error ? error.message : "Unable to generate the recovery itinerary.",
      );
    } finally {
      setGeneratingItinerary(false);
    }
  }

  async function retrieveRecoveryItinerary() {
    if (!selectedSavedPlanId) return;
    setGeneratingItinerary(true);
    setItineraryError("");
    try {
      setRecoveryItinerary(
        await apiRequest<RecoveryItinerary>(
          `/api/v1/recovery/plans/${Number(selectedSavedPlanId)}`,
        ),
      );
    } catch (error) {
      setItineraryError(
        error instanceof Error ? error.message : "Unable to retrieve the saved itinerary.",
      );
    } finally {
      setGeneratingItinerary(false);
    }
  }

  async function searchTransport() {
    if (!selectedJourney) return;
    setSearching(true);
    setSearchMessage("");
    setAlternativeError("");
    try {
      const params = new URLSearchParams({
        origin: selectedJourney.origin,
        destination: selectedJourney.destination,
      });
      const result = await apiRequest<TransportSearchResult>(
        `/api/transport/search?${params.toString()}`,
      );
      setSearchMessage(result.message);
    } catch (error) {
      setAlternativeError(
        error instanceof Error ? error.message : "Transport search is unavailable.",
      );
    } finally {
      setSearching(false);
    }
  }

  async function searchWeather(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const location = weatherLocation.trim() || selectedJourney?.origin;
    if (!location) {
      setWeatherError("Enter a city or select a journey to check its origin.");
      return;
    }
    setWeatherLoading(true);
    setWeatherError("");
    try {
      const params = new URLSearchParams({ location });
      if (weatherCountryCode) params.set("country_code", weatherCountryCode);
      setWeatherForecast(
        await apiRequest<WeatherForecast>(
          `/api/v1/weather/forecast?${params.toString()}`,
        ),
      );
    } catch (error) {
      setWeatherForecast(null);
      setWeatherError(
        error instanceof Error ? error.message : "Unable to load the weather forecast.",
      );
    } finally {
      setWeatherLoading(false);
    }
  }

  const selectedJourney = dashboard?.journeys.find(
    (journey) => String(journey.id) === selectedJourneyId,
  );
  const statusText = loading ? "Connecting" : apiError ? "Needs attention" : "Connected";

  if (!authReady) {
    return <main className="shell auth-shell"><p className="empty-copy">Loading your secure session…</p></main>;
  }

  if (!accessToken) {
    return (
      <main className="shell auth-shell">
        <a className="brand auth-brand" href="#" aria-label="StrandedPool home">
          <span className="brand-mark">S</span>
          <span>stranded<span className="brand-accent">pool</span></span>
        </a>
        <section className="panel auth-panel">
          <p className="eyebrow">PRIVATE TRAVEL RECOVERY</p>
          <h1>{authMode === "login" ? "Welcome back" : "Create your account"}</h1>
          <p className="section-subtitle">
            Journeys and booking details are available only after signing in.
          </p>
          <form className="form-grid auth-form" onSubmit={submitAuth}>
            <label className="form-field form-field-wide">
              <span>Email</span>
              <input className="input" name="email" type="email" autoComplete="email" required maxLength={254} />
            </label>
            <label className="form-field form-field-wide">
              <span>Password{authMode === "register" ? " · at least 12 characters" : ""}</span>
              <input
                className="input"
                name="password"
                type="password"
                autoComplete={authMode === "register" ? "new-password" : "current-password"}
                required
                minLength={authMode === "register" ? 12 : 1}
                maxLength={128}
              />
            </label>
            {authError && <p className="form-error form-field-wide" role="alert">{authError}</p>}
            <button className="button button-primary form-field-wide" disabled={authLoading}>
              {authLoading ? "Please wait…" : authMode === "register" ? "Create account" : "Sign in"}
            </button>
          </form>
          <button
            className="text-button auth-toggle"
            type="button"
            onClick={() => {
              setAuthMode(authMode === "login" ? "register" : "login");
              setAuthError("");
            }}
          >
            {authMode === "login" ? "New to StrandedPool? Create an account" : "Already registered? Sign in"}
          </button>
          <p className="form-hint">
            Use a unique password. For production, configure a stable secret and HTTPS.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="StrandedPool home">
          <span className="brand-mark">S</span>
          <span>stranded<span className="brand-accent">pool</span></span>
        </a>
        <div className={`connection ${apiError ? "connection-error" : ""}`}>
          <span className="connection-dot" />
          API {statusText}
          <button className="text-button" type="button" onClick={signOut}>Sign out</button>
        </div>
      </header>

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">TRAVEL RECOVERY, TOGETHER</p>
          <h1>When plans change,<br /><span>find your next move.</span></h1>
          <p className="hero-description">
            Keep journeys, disruption reports and practical recovery steps in one place.
          </p>
        </div>
        <div className="hero-stats" aria-label="Dashboard totals">
          <div className="hero-stat">
            <span className="stat-number">{dashboard?.journey_count ?? "—"}</span>
            <span className="stat-label">Journeys</span>
          </div>
          <div className="hero-stat">
            <span className="stat-number">{dashboard?.disruption_count ?? "—"}</span>
            <span className="stat-label">Reports</span>
          </div>
        </div>
      </section>

      {apiError && (
        <div className="alert alert-error" role="alert">
          <strong>Dashboard unavailable</strong>
          <span>{apiError}</span>
          <button className="text-button" onClick={() => void loadDashboard()}>Try again</button>
        </div>
      )}
      {notice && (
        <div
          className={`alert ${notice.startsWith("Option saved but excluded") ? "alert-warning" : "alert-success"}`}
          role="status"
        >
          {notice}
        </div>
      )}

      <div className="notice-bar">
        <span className="notice-icon">i</span>
        <span>
          No live transport provider is connected. Reports and alternatives you add are
          clearly marked as unverified; fares and availability are never assumed.
        </span>
      </div>

      <section className="dashboard-grid">
        <div className="panel journey-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">YOUR TRAVEL</p>
              <h2>Journey details</h2>
            </div>
            <span className="panel-icon">01</span>
          </div>
          {dashboard?.journeys.length ? (
            <>
              <label className="field-label" htmlFor="journey-select">Choose a journey</label>
              <select
                id="journey-select"
                className="input"
                value={selectedJourneyId}
                onChange={(event) => setSelectedJourneyId(event.target.value)}
              >
                {dashboard.journeys.map((journey) => (
                  <option key={journey.id} value={journey.id}>
                    {journey.origin} → {journey.destination} · {journey.traveller_name}
                  </option>
                ))}
              </select>
              {selectedJourney && (
                <div className="journey-summary">
                  <div className="route-line">
                    <span className="route-point" />
                    <div><strong>{selectedJourney.origin}</strong><small>Origin</small></div>
                  </div>
                  <div className="route-connector" />
                  <div className="route-line">
                    <span className="route-point route-point-end" />
                    <div><strong>{selectedJourney.destination}</strong><small>Destination</small></div>
                  </div>
                  <div className="journey-meta">
                    <span>Departure</span><strong>{formatDate(selectedJourney.departure_at)}</strong>
                  </div>
                  {selectedJourney.arrive_by && (
                    <div className="journey-meta">
                      <span>Arrive by</span><strong>{formatDate(selectedJourney.arrive_by)}</strong>
                    </div>
                  )}
                  {selectedJourney.budget_amount !== null && (
                    <div className="journey-meta">
                      <span>Budget</span><strong>{selectedJourney.budget_amount.toLocaleString()}</strong>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="empty-copy">
              {loading ? "Loading journeys…" : "No journeys yet. Add one to start a recovery plan."}
            </p>
          )}
        </div>

        <div className="panel disruption-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">SITUATION UPDATE</p>
              <h2>Recent reports</h2>
            </div>
            <span className="panel-icon">02</span>
          </div>
          {dashboard?.recent_disruptions.length ? (
            <div className="report-list">
              {dashboard.recent_disruptions.map((disruption) => (
                <article className="report-item" key={disruption.id}>
                  <span className="report-marker" />
                  <div className="report-copy">
                    <strong>{disruption.title}</strong>
                    <p>{disruption.description}</p>
                    <div className="report-meta">
                      <span>{disruption.transport_mode || "Travel"} · {formatDate(disruption.reported_at)}</span>
                      <span className="tag tag-amber">Unverified report</span>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-copy">
              {loading ? "Loading reports…" : "No disruption reports. Any report you add will be labelled unverified."}
            </p>
          )}
        </div>
      </section>

      <section className="panel weather-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">WEATHER OUTLOOK</p>
            <h2>Forecast-based risk estimate</h2>
            <p className="section-subtitle">
              Weather can affect travel, but this estimate does not verify a transport disruption.
            </p>
          </div>
          <span className="panel-icon">WX</span>
        </div>
        <form className="weather-search" onSubmit={searchWeather}>
          <LocationPicker
            name="weather_location"
            label="City or location"
            placeholder={selectedJourney?.origin || "e.g. Mangaluru"}
            onLocationChange={(location, countryCode) => {
              setWeatherLocation(location);
              setWeatherCountryCode(countryCode);
            }}
          />
          <button className="button button-primary" type="submit" disabled={weatherLoading}>
            {weatherLoading ? "Checking…" : "Check forecast"}
          </button>
        </form>
        {weatherError && <p className="form-error" role="alert">{weatherError}</p>}
        {weatherForecast?.status === "unavailable" && (
          <p className="empty-copy" role="status">{weatherForecast.notice}</p>
        )}
        {weatherForecast?.status === "available" && weatherForecast.risk && (
          <div className="weather-results" aria-live="polite">
            <div className={`weather-risk weather-risk-${weatherForecast.risk.level}`}>
              <strong>
                {weatherForecast.risk.level} estimated weather risk · {weatherForecast.location?.name}
                {weatherForecast.location?.country ? `, ${weatherForecast.location.country}` : ""}
              </strong>
              <span>{weatherForecast.data_freshness} · {weatherForecast.source}</span>
              {weatherForecast.risk.drivers.length > 0 && (
                <span>{weatherForecast.risk.drivers.join("; ")}</span>
              )}
            </div>
            <ul className="weather-hours">
              {weatherForecast.hours.map((hour) => (
                <li key={hour.time}>
                  <strong>{formatDate(hour.time)}</strong>
                  <span>{hour.condition}</span>
                  <span>Rain chance {hour.precipitation_probability_percent}%</span>
                  <span>{hour.precipitation_mm} mm · wind {hour.wind_speed_kmh} km/h</span>
                </li>
              ))}
            </ul>
            <p className="form-hint">{weatherForecast.notice}</p>
          </div>
        )}
      </section>

      <section className="workbench">
        <div className="panel form-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">BUILD YOUR RECOVERY</p>
              <h2>Add trip information</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={submitJourney}>
            <label className="form-field">
              <span>Display name</span>
              <input className="input" name="traveller_name" maxLength={80} required placeholder="e.g. Alex" />
            </label>
            <LocationPicker name="origin" label="From" required placeholder="Departure city" />
            <LocationPicker name="destination" label="To" required placeholder="Destination city" />
            <label className="form-field">
              <span>Departure</span>
              <input className="input" name="departure_at" type="datetime-local" required />
            </label>
            <label className="form-field">
              <span>Need to arrive by <em>Optional</em></span>
              <input className="input" name="arrive_by" type="datetime-local" />
            </label>
            <label className="form-field">
              <span>Budget <em>Optional</em></span>
              <input className="input" name="budget_amount" type="number" min="0" step="0.01" placeholder="Amount" />
            </label>
            <label className="form-field">
              <span>Budget currency</span>
              <select className="input" name="budget_currency" defaultValue="INR">
                <option value="INR">INR</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </label>
            <label className="form-field form-field-wide">
              <span>Constraints <em>Optional, comma-separated</em></span>
              <input className="input" name="constraints" maxLength={500} placeholder="e.g. wheelchair access, no overnight travel" />
            </label>
            <label className="form-field">
              <span>Passengers</span>
              <input className="input" name="passenger_count" type="number" min="1" max="12" defaultValue="1" />
            </label>
            <label className="consent-field form-field">
              <input name="pooling_consent" type="checkbox" />
              <span>Opt in to anonymous-compatible pooling proposals</span>
            </label>
            {journeyError && <p className="form-error form-field-wide" role="alert">{journeyError}</p>}
            <button className="button button-primary form-field-wide" disabled={saving}>
              {saving ? "Saving…" : "Save journey"}
            </button>
          </form>
        </div>

        <div className="panel form-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">REPORT A CHANGE</p>
              <h2>Log a disruption</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={submitDisruption}>
            <label className="form-field form-field-wide">
              <span>What happened?</span>
              <input className="input" name="title" minLength={3} maxLength={120} required placeholder="e.g. Service cancellation reported" />
            </label>
            <label className="form-field form-field-wide">
              <span>Details</span>
              <textarea className="input textarea" name="description" minLength={3} maxLength={2000} required placeholder="Add what you know and when you heard it." />
            </label>
            <label className="form-field form-field-wide">
              <span>Transport mode <em>Optional</em></span>
              <select className="input" name="transport_mode" defaultValue="">
                <option value="">Choose a mode</option>
                <option value="train">Train</option>
                <option value="bus">Bus</option>
                <option value="flight">Flight</option>
                <option value="road">Road</option>
                <option value="other">Other</option>
              </select>
            </label>
            {disruptionError && <p className="form-error form-field-wide" role="alert">{disruptionError}</p>}
            <button className="button button-secondary form-field-wide" disabled={saving}>
              {saving ? "Saving…" : "Save disruption report"}
            </button>
          </form>
        </div>

        <div className="panel form-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">DOWNSTREAM PLANS</p>
              <h2>Record a booking</h2>
            </div>
          </div>
          <form className="form-grid" onSubmit={submitBooking}>
            <label className="form-field form-field-wide">
              <span>Booking type</span>
              <select className="input" name="kind" defaultValue="transport">
                <option value="transport">Transport</option>
                <option value="accommodation">Accommodation</option>
                <option value="connection">Connection</option>
                <option value="appointment">Appointment</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="form-field form-field-wide">
              <span>Provider</span>
              <input className="input" name="provider" maxLength={120} required placeholder="Provider or service name" />
            </label>
            <label className="form-field form-field-wide">
              <span>Notes <em>Optional</em></span>
              <textarea className="input textarea" name="details" maxLength={2000} placeholder="Non-sensitive details about this booking." />
            </label>
            <LocationPicker name="origin" label="Origin (optional)" placeholder="Choose if known" />
            <LocationPicker name="destination" label="Destination (optional)" placeholder="Choose if known" />
            <label className="form-field">
              <span>Scheduled start <em>Optional</em></span>
              <input className="input" name="scheduled_start" type="datetime-local" />
            </label>
            <label className="form-field">
              <span>Scheduled end / arrival <em>Optional</em></span>
              <input className="input" name="scheduled_end" type="datetime-local" />
            </label>
            <label className="form-field">
              <span>Timezone</span>
              <input className="input" name="timezone" maxLength={80} defaultValue="Asia/Kolkata" />
            </label>
            <label className="form-field">
              <span>Price <em>Optional</em></span>
              <input className="input" name="price_amount" type="number" min="0" step="0.01" />
            </label>
            <p className="form-hint form-field-wide">Booking details are private to your account but are not encrypted at rest. Avoid storing booking references or sensitive personal information.</p>
            {bookingError && <p className="form-error form-field-wide" role="alert">{bookingError}</p>}
            <button className="button button-secondary form-field-wide" disabled={saving || !selectedJourneyId}>
              {saving ? "Saving…" : "Add booking"}
            </button>
          </form>
        </div>
      </section>

      <section className="panel alternatives-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">COMPARE WHAT YOU&apos;VE FOUND</p>
            <h2>Alternative options</h2>
            <p className="section-subtitle">Add options checked with a provider. We rank your details; we do not verify inventory.</p>
          </div>
          <span className="panel-icon">03</span>
        </div>
        <div className="search-status">
          <button className="button button-secondary" type="button" onClick={searchTransport} disabled={!selectedJourney || searching}>
            {searching ? "Checking…" : "Check live provider inventory"}
          </button>
          {searchMessage && <p className="empty-copy" role="status">{searchMessage}</p>}
        </div>
        <div className="alternatives-layout">
          <form key={selectedJourneyId} className="form-grid alternative-form" onSubmit={submitAlternative}>
            <label className="form-field">
              <span>Mode</span>
              <select className="input" name="mode" defaultValue="bus">
                <option value="bus">Bus</option>
                <option value="train">Train</option>
                <option value="flight">Flight</option>
                <option value="taxi">Taxi / shared ride</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="form-field">
              <span>Provider / source</span>
              <input className="input" name="provider" required maxLength={120} placeholder="Where you checked" />
            </label>
            <LocationPicker name="origin" label="From" required defaultValue={selectedJourney?.origin} />
            <LocationPicker name="destination" label="To" required defaultValue={selectedJourney?.destination} />
            <label className="form-field">
              <span>Arrival time <em>Optional</em></span>
              <input className="input" name="arrival_at" type="datetime-local" />
            </label>
            <label className="form-field">
              <span>Fare <em>Optional</em></span>
              <input className="input" name="fare_amount" type="number" min="0" step="0.01" placeholder="Amount" />
            </label>
            <label className="form-field">
              <span>Fare currency</span>
              <select className="input" name="currency" defaultValue="INR">
                <option value="INR">INR</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </label>
            <label className="form-field form-field-wide">
              <span>Constraints this option appears to meet <em>Optional, comma-separated</em></span>
              <input className="input" name="constraints_satisfied" placeholder="Match the constraints on your journey" />
            </label>
            {alternativeError && <p className="form-error form-field-wide" role="alert">{alternativeError}</p>}
            <button className="button button-primary form-field-wide" disabled={saving || !selectedJourneyId}>
              {saving ? "Saving…" : "Add and rank option"}
            </button>
          </form>
          <div className="option-list">
            {!selectedJourneyId ? (
              <p className="empty-copy">Add a journey before comparing alternatives.</p>
            ) : recovery?.alternatives.length ? (
              recovery.alternatives.map((alternative) => (
                <article className="option-card" key={alternative.id}>
                  <div className="option-topline">
                    <strong>{alternative.mode} · {alternative.provider}</strong>
                    <span className="score-pill">{alternative.score}/100</span>
                  </div>
                  <p>{alternative.origin} → {alternative.destination}</p>
                  <div className="option-facts">
                    <span>Fare: {formatFare(alternative.fare_amount)} {alternative.currency}</span>
                    <span>Arrives: {formatDate(alternative.arrival_at)}</span>
                  </div>
                  <div className="report-meta">
                    <span>Entered {formatDate(alternative.entered_at)}</span>
                    <span className="tag tag-blue">{alternative.source_label}</span>
                    <span className="tag tag-amber">{alternative.data_freshness}</span>
                  </div>
                  <ul className="reason-list">
                    {alternative.reasons.map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                  <button
                    className="text-button"
                    type="button"
                    aria-pressed={selectedAlternativeId === alternative.id}
                    onClick={() => setSelectedAlternativeId(alternative.id)}
                  >
                    {selectedAlternativeId === alternative.id ? "Selected for itinerary" : "Use in recovery itinerary"}
                  </button>
                </article>
              ))
            ) : (
              <p className="empty-copy">
                No feasible alternative currently meets the hard constraints. Infeasible or unknown options are excluded from recommendations.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="recovery-grid">
        <div className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">PROPOSED NEXT STEPS</p>
              <h2>Bookings &amp; next steps</h2>
            </div>
          </div>
          {recovery ? (
            <>
              {recovery.bookings.length ? (
                <div className="booking-list">
                  {recovery.bookings.map((booking) => (
                    <article className="booking-item" key={booking.id}>
                      <span className="booking-kind">{booking.kind.slice(0, 1).toUpperCase()}</span>
                      <div>
                        <strong>{booking.provider}</strong>
                        <span>{booking.kind}{booking.details ? ` · ${booking.details}` : ""}</span>
                        <span>
                          {booking.scheduled_start ? `Starts ${formatDate(booking.scheduled_start)}` : "Schedule not provided"}
                          {booking.scheduled_end ? ` · Ends ${formatDate(booking.scheduled_end)}` : ""}
                          {` · ${booking.verification_status}`}
                        </span>
                      </div>
                      <button
                        className="text-button"
                        type="button"
                        onClick={() => void simulateCancellation(booking.id)}
                        disabled={analyzingCascade}
                        title="Runs a labelled simulation only; it does not change this booking."
                      >
                        Simulate cancellation
                      </button>
                    </article>
                  ))}
                  {recovery.bookings.length > 1 && (
                    <form className="form-grid dependency-form" onSubmit={submitDependency}>
                      <label className="form-field">
                        <span>Booking that happens first</span>
                        <select className="input" name="predecessor_booking_id" required defaultValue="">
                          <option value="" disabled>Select a booking</option>
                          {recovery.bookings.map((booking) => (
                            <option key={booking.id} value={booking.id}>{booking.provider} · #{booking.id}</option>
                          ))}
                        </select>
                      </label>
                      <label className="form-field">
                        <span>Downstream booking</span>
                        <select className="input" name="downstream_booking_id" required defaultValue="">
                          <option value="" disabled>Select a booking</option>
                          {recovery.bookings.map((booking) => (
                            <option key={booking.id} value={booking.id}>{booking.provider} · #{booking.id}</option>
                          ))}
                        </select>
                      </label>
                      <label className="form-field">
                        <span>Relationship</span>
                        <select className="input" name="dependency_type" defaultValue="connection">
                          <option value="connection">Connection</option>
                          <option value="pickup">Pickup</option>
                          <option value="check_in">Check-in</option>
                          <option value="appointment">Appointment</option>
                          <option value="other">Other</option>
                        </select>
                      </label>
                      {dependencyError && <p className="form-error form-field-wide" role="alert">{dependencyError}</p>}
                      <button className="button button-secondary form-field-wide" disabled={saving}>
                        Link downstream booking
                      </button>
                    </form>
                  )}
                  {recovery.dependencies.length > 0 && (
                    <p className="form-hint">
                      Linked dependencies: {recovery.dependencies.map((edge) => `#${edge.predecessor_booking_id} → #${edge.downstream_booking_id}`).join(", ")}
                    </p>
                  )}
                </div>
              ) : (
                <p className="empty-copy">No downstream bookings recorded for this journey.</p>
              )}
              {cascadeError && <p className="form-error" role="alert">{cascadeError}</p>}
              {cascadeAnalysis && (
                <section className="cascade-results" aria-live="polite">
                  <strong>SIMULATED cascade · no bookings changed</strong>
                  <ul className="steps-list">
                    {cascadeAnalysis.impacts.map((impact) => (
                      <li key={`${impact.booking_id}-${impact.impact}`}>
                        <span className={`impact-badge impact-${impact.severity}`}>{impact.impact.replaceAll("_", " ")}</span>
                        <span>Booking #{impact.booking_id} · {impact.kind}: {impact.reason}</span>
                      </li>
                    ))}
                  </ul>
                  {cascadeAnalysis.limitations.map((limitation) => (
                    <p className="form-hint" key={limitation}>{limitation}</p>
                  ))}
                </section>
              )}
              <ol className="steps-list steps-after-bookings">
                {recovery.next_steps.map((step, index) => (
                  <li key={step}>
                    <span className="step-number">{String(index + 1).padStart(2, "0")}</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
              <div className="itinerary-controls">
                {itineraryError && <p className="form-error" role="alert">{itineraryError}</p>}
                {savedPlanError && <p className="form-error" role="alert">{savedPlanError}</p>}
                {savedRecoveryPlans.length > 0 && (
                  <div className="saved-plan-controls">
                    <label className="form-field">
                      <span>Saved recovery plans</span>
                      <select
                        className="input"
                        value={selectedSavedPlanId}
                        onChange={(event) => setSelectedSavedPlanId(event.target.value)}
                      >
                        {savedRecoveryPlans.map((plan) => (
                          <option key={plan.plan_id} value={plan.plan_id}>
                            Plan #{plan.plan_id} · {formatDate(plan.created_at)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      className="button button-secondary"
                      type="button"
                      onClick={() => void retrieveRecoveryItinerary()}
                      disabled={generatingItinerary || !selectedSavedPlanId}
                    >
                      Retrieve selected plan
                    </button>
                  </div>
                )}
                <button
                  className="button button-primary"
                  type="button"
                  onClick={() => void generateRecoveryItinerary()}
                  disabled={generatingItinerary}
                >
                  {generatingItinerary ? "Building itinerary…" : "Build recovery itinerary"}
                </button>
                {recoveryItinerary && (
                  <section className="itinerary-results" aria-live="polite">
                    <strong>Recovery itinerary · {recoveryItinerary.verification_status}</strong>
                    <p>
                      Saved plan #{recoveryItinerary.plan_id} ·{" "}
                      {formatDate(recoveryItinerary.created_at)}
                    </p>
                    <div className="itinerary-timelines">
                      <div>
                        <strong>Original timeline</strong>
                        <p>{recoveryItinerary.journey.origin} → {recoveryItinerary.journey.destination}</p>
                        <p>Departure: {formatDate(recoveryItinerary.journey.departure_at)}</p>
                        {recoveryItinerary.original_bookings.length ? (
                          <ul className="timeline-list">
                            {recoveryItinerary.original_bookings.map((booking) => (
                              <li key={booking.id}>
                                <strong>{booking.provider} · {booking.kind}</strong>
                                <span>
                                  {booking.origin || "—"} → {booking.destination || "—"}
                                  {" · "}{formatDate(booking.scheduled_start)}
                                  {booking.verification_status !== "VERIFIED" && " · unverified"}
                                </span>
                              </li>
                            ))}
                          </ul>
                        ) : <p className="empty-copy">No original bookings recorded.</p>}
                      </div>
                      <div>
                        <strong>Proposed timeline</strong>
                        {recoveryItinerary.proposed_alternative ? (
                          <>
                            <p>{recoveryItinerary.journey.origin} → {recoveryItinerary.journey.destination}</p>
                            <p>
                              {recoveryItinerary.proposed_alternative.mode} ·{" "}
                              {recoveryItinerary.proposed_alternative.provider}
                              {" · arrival "}{formatDate(recoveryItinerary.proposed_alternative.arrival_at)}
                            </p>
                            <p>
                              Fare: {formatFare(recoveryItinerary.proposed_alternative.fare_amount)}{" "}
                              {recoveryItinerary.proposed_alternative.currency}
                              {" · user-entered, not provider-verified"}
                            </p>
                            <p className="form-hint">
                              This proposal is not confirmed and has not replaced the original bookings.
                            </p>
                          </>
                        ) : (
                          <p className="empty-copy">No alternative selected; original bookings remain unchanged.</p>
                        )}
                      </div>
                    </div>
                    {recoveryItinerary.cost_comparison.status === "user_entered_comparison" ? (
                      <p className="form-hint">
                        Reported fare change: {formatFare(recoveryItinerary.cost_comparison.difference ?? null)}{" "}
                        {recoveryItinerary.cost_comparison.currency} · {recoveryItinerary.cost_comparison.source_label}
                      </p>
                    ) : (
                      <p className="form-hint">{recoveryItinerary.cost_comparison.reason}</p>
                    )}
                    {recoveryItinerary.booking_changes_made && (
                      <p className="form-error">Unexpected booking state; contact support.</p>
                    )}
                    <ol className="steps-list">
                      {recoveryItinerary.required_next_steps.map((step, index) => (
                        <li key={step}>
                          <span className="step-number">{String(index + 1).padStart(2, "0")}</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </section>
                )}
              </div>
            </>
          ) : (
            <p className="empty-copy">Choose a journey to see bookings and recovery steps.</p>
          )}
        </div>
        <div className="panel pool-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">COORDINATE, DON&apos;T ASSUME</p>
              <h2>Pooling proposal</h2>
            </div>
          </div>
          {recovery?.pooling.matches.length ? (
            <>
              <p className="pool-summary">
                Consenting journeys with the same origin and destination and a departure within two hours.
                Combined stated passenger count: {recovery.pooling.total_consented_passengers}.
              </p>
              <ul className="pool-list">
                {recovery.pooling.matches.map((match) => (
                  <li key={match.passenger_count}>
                    <span className="pool-avatar">•</span>
                    <span>Opted-in traveller group<small>{match.passenger_count} passenger(s)</small></span>
                  </li>
                ))}
              </ul>
              <p className="pool-disclaimer">Proposal only. Participants opted in to matching; no vehicle, seats, fare, or booking is verified.</p>
            </>
          ) : (
            <p className="empty-copy">
              {recovery?.pooling.status === "consent_required"
                ? "Opt in when creating a journey before it can appear in pooling proposals."
                : selectedJourneyId
                ? "No other opted-in journeys match origin, destination, and departure window."
                : "Add a journey to check for compatible travellers."}
            </p>
          )}
        </div>
      </section>

      <section className="panel action-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">REVIEW BEFORE SENDING</p>
            <h2>Draft a service-provider message</h2>
            <p className="section-subtitle">
              These are editable templates, not AI output. StrandedPool never sends them.
            </p>
          </div>
        </div>
        <form className="form-grid action-form" onSubmit={submitActionDraft}>
          <label className="form-field">
            <span>Message purpose</span>
            <select className="input" name="action" defaultValue="hotel_late_checkin">
              <option value="hotel_late_checkin">Hotel late check-in</option>
              <option value="refund_inquiry">Refund inquiry</option>
              <option value="cab_pickup_update">Cab pickup update</option>
              <option value="appointment_reschedule">Appointment reschedule</option>
              <option value="disruption_notification">Disruption notification</option>
            </select>
          </label>
          <label className="form-field">
            <span>Language</span>
            <select className="input" name="language" defaultValue="en">
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="kn">Kannada</option>
            </select>
          </label>
          <label className="form-field form-field-wide">
            <span>Provider or recipient</span>
            <input className="input" name="provider_name" maxLength={120} required placeholder="e.g. hotel or service desk" />
          </label>
          {actionError && <p className="form-error form-field-wide" role="alert">{actionError}</p>}
          <button className="button button-secondary form-field-wide" disabled={draftingAction || !selectedJourneyId}>
            {draftingAction ? "Drafting…" : "Generate editable draft"}
          </button>
        </form>
        {actionDraft && (
          <div className="action-draft">
            <p className="form-hint">{actionDraft.source} · {actionDraft.language.toUpperCase()} · not sent</p>
            <label className="form-field">
              <span>Edit the draft before copying or sending it yourself</span>
              <textarea
                className="input textarea action-textarea"
                value={actionDraft.content}
                onChange={(event) => setActionDraft({ ...actionDraft, content: event.target.value })}
              />
            </label>
          </div>
        )}
      </section>

      <footer className="footer">
        <span>StrandedPool · Plan carefully, confirm directly with providers.</span>
        <span>Transport inventory is not connected.</span>
      </footer>
    </main>
  );
}

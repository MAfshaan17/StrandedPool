const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export interface Journey {
  id: number;
  traveller_name: string;
  origin: string;
  destination: string;
  departure_at: string;
  arrive_by: string | null;
  budget_amount: number | null;
  constraints: string[];
  created_at: string;
}

export interface Disruption {
  id: number;
  journey_id: number | null;
  title: string;
  description: string;
  transport_mode: string | null;
  status: string;
  source_label: string;
  reported_at: string;
}

export interface Alternative {
  id: number;
  journey_id: number;
  mode: string;
  provider: string;
  origin: string;
  destination: string;
  departure_at: string | null;
  arrival_at: string | null;
  fare_amount: number | null;
  constraints_satisfied: string[];
  source_label: string;
  entered_at: string;
  data_freshness: string;
  score: number;
  destination_match: boolean;
  within_budget: boolean | null;
  arrives_on_time: boolean | null;
  reasons: string[];
}

export interface Dashboard {
  journey_count: number;
  disruption_count: number;
  journeys: Journey[];
  recent_disruptions: Disruption[];
  data_notice: string;
}

export interface JourneyBooking {
  id: number;
  journey_id: number;
  kind: string;
  provider: string;
  reference: string | null;
  details: string | null;
  created_at: string;
}

export interface RecoveryPlan {
  journey: Journey;
  disruptions: Disruption[];
  bookings: JourneyBooking[];
  alternatives: Alternative[];
  pooling: {
    status: string;
    matches: Array<{ journey_id: number; traveller_name: string }>;
    availability: string;
  };
  next_steps: string[];
}

export interface TransportSearchResult {
  status: "provider_unavailable";
  origin: string;
  destination: string;
  provider: null;
  source_label: string;
  data_freshness: string;
  checked_at: string | null;
  options: never[];
  message: string;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response;
  try {
    const headers = new Headers(init.headers);
    if (init.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new Error(
      `Cannot reach the StrandedPool API at ${API_BASE_URL}. Start the backend and check NEXT_PUBLIC_API_BASE_URL.`,
    );
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body.detail === "string"
        ? body.detail
        : `API request failed (${response.status})`;
    throw new Error(detail);
  }
  return body as T;
}

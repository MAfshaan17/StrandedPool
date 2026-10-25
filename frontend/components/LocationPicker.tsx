"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

import { apiRequest, LocationSuggestion } from "../lib/api";
import { countries, countryCodeForName } from "../lib/countries";

interface LocationPickerProps {
  name: string;
  label: string;
  required?: boolean;
  defaultValue?: string;
  placeholder?: string;
  onLocationChange?: (location: string, countryCode: string, selected: boolean) => void;
}

function getInitialLocation(value: string | undefined) {
  if (!value) return { city: "", countryCode: "" };
  const parts = value.split(",").map((part) => part.trim());
  const possibleCountry = parts.at(-1) ?? "";
  const countryCode = countryCodeForName(possibleCountry);
  return countryCode
    ? { city: parts.slice(0, -1).join(", "), countryCode }
    : { city: value, countryCode: "" };
}

export default function LocationPicker({
  name,
  label,
  required = false,
  defaultValue,
  placeholder = "Type a city name",
  onLocationChange,
}: LocationPickerProps) {
  const initialLocation = useMemo(() => getInitialLocation(defaultValue), [defaultValue]);
  const containerRef = useRef<HTMLDivElement>(null);
  const [city, setCity] = useState(initialLocation.city);
  const [countryCode, setCountryCode] = useState(initialLocation.countryCode);
  const [cityConfirmed, setCityConfirmed] = useState(Boolean(initialLocation.countryCode));
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestionError, setSuggestionError] = useState("");
  const [activeSuggestion, setActiveSuggestion] = useState(-1);
  const country = countries.find((item) => item.code === countryCode);
  const id = `location-${name}-${useId().replace(/:/g, "")}`;

  useEffect(() => {
    if (!countryCode || city.trim().length < 2 || cityConfirmed) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setLoading(true);
      setSuggestionError("");
      const params = new URLSearchParams({
        query: city.trim(),
        country_code: countryCode,
      });
      apiRequest<{ results: LocationSuggestion[] }>(
        `/api/v1/weather/locations?${params.toString()}`,
        { signal: controller.signal },
      )
        .then((result) => {
          setSuggestions(result.results);
          setActiveSuggestion(-1);
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            setSuggestions([]);
            setSuggestionError(
              error instanceof Error ? error.message : "Unable to find matching cities.",
            );
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 250);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [city, cityConfirmed, countryCode]);

  useEffect(() => {
    const form = containerRef.current?.closest("form");
    if (!form) return;
    const resetLocation = () => {
      setCity(initialLocation.city);
      setCountryCode(initialLocation.countryCode);
      setCityConfirmed(Boolean(initialLocation.countryCode));
      setSuggestions([]);
      setSuggestionError("");
    };
    form.addEventListener("reset", resetLocation);
    return () => form.removeEventListener("reset", resetLocation);
  }, [initialLocation]);

  const formattedLocation = city.trim() && country
    ? `${city.trim()}, ${country.name}`
    : city.trim();

  function updateLocation(nextCity: string, nextCountryCode: string, selected: boolean) {
    const selectedCountry = countries.find((item) => item.code === nextCountryCode);
    const value = nextCity.trim() && selectedCountry
      ? `${nextCity.trim()}, ${selectedCountry.name}`
      : nextCity.trim();
    onLocationChange?.(value, nextCountryCode, selected);
  }

  function chooseSuggestion(suggestion: LocationSuggestion) {
    setCity(suggestion.name);
    setCityConfirmed(true);
    setSuggestions([]);
    setSuggestionError("");
    updateLocation(suggestion.name, countryCode, true);
  }

  return (
    <div className="form-field location-picker" ref={containerRef}>
      <label className="form-field" htmlFor={`${id}-country`}>
        <span>Country</span>
        <select
          className="input"
          id={`${id}-country`}
          value={countryCode}
          required={required}
          onChange={(event) => {
            const nextCountryCode = event.target.value;
            setCountryCode(nextCountryCode);
            setCity("");
            setCityConfirmed(false);
            setSuggestions([]);
            setSuggestionError("");
            updateLocation("", nextCountryCode, false);
          }}
        >
          <option value="">Choose a country first</option>
          {countries.map((item) => (
            <option key={item.code} value={item.code}>{item.name}</option>
          ))}
        </select>
      </label>
      <label className="form-field" htmlFor={`${id}-city`}>
        <span>{label}</span>
        <input
          className="input"
          id={`${id}-city`}
          value={city}
          onChange={(event) => {
            const nextCity = event.target.value;
            setCity(nextCity);
            setCityConfirmed(false);
            setSuggestions([]);
            updateLocation(nextCity, countryCode, false);
          }}
          maxLength={120}
          minLength={2}
          required={required}
          disabled={!countryCode}
          placeholder={countryCode ? placeholder : "Choose a country first"}
          autoComplete="off"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={suggestions.length > 0}
          aria-controls={`${id}-suggestions`}
          aria-busy={loading}
          onKeyDown={(event) => {
            if (!suggestions.length) return;
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setActiveSuggestion((current) => Math.min(current + 1, suggestions.length - 1));
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              setActiveSuggestion((current) => Math.max(current - 1, 0));
            } else if (event.key === "Enter" && activeSuggestion >= 0) {
              event.preventDefault();
              chooseSuggestion(suggestions[activeSuggestion]);
            } else if (event.key === "Escape") {
              setSuggestions([]);
            }
          }}
        />
      </label>
      <input type="hidden" name={name} value={formattedLocation} />
      {loading && <span className="form-hint" role="status">Finding cities…</span>}
      {suggestions.length > 0 && (
        <ul className="location-suggestions" id={`${id}-suggestions`} role="listbox">
          {suggestions.map((suggestion, index) => (
            <li key={`${suggestion.latitude}-${suggestion.longitude}`} role="option" aria-selected={index === activeSuggestion}>
              <button
                type="button"
                className="location-suggestion"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => chooseSuggestion(suggestion)}
              >
                <strong>{suggestion.name}</strong>
                <span>{[suggestion.admin1, suggestion.country].filter(Boolean).join(", ")}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {suggestionError && <span className="form-error" role="status">{suggestionError}</span>}
      {countryCode && city.trim().length > 0 && city.trim().length < 2 && (
        <span className="form-hint">Type at least 2 letters for city suggestions.</span>
      )}
    </div>
  );
}

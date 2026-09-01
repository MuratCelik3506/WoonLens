export type SourceMetadata = Readonly<{
  dataset: string;
  license: string;
  provider: string;
  retrievedAt: string;
}>;

export type ComparedHome = Readonly<{
  addressId: string;
  contextNotes: readonly string[];
  displayName: string | null;
  sources: readonly SourceMetadata[];
  unavailableReason: string | null;
}>;

export type ComparedValue = Readonly<{
  addressId: string;
  isBaseline: boolean;
  missingReason: string | null;
  value: number | string | null;
}>;

export type ComparedMetric = Readonly<{
  definition: string;
  key: string;
  label: string;
  scope: string;
  unit: string;
  values: readonly ComparedValue[];
}>;

export type ComparisonNotice = Readonly<{ code: string; message: string }>;

export type LiveComparison = Readonly<{
  homes: readonly ComparedHome[];
  metrics: readonly ComparedMetric[];
  notices: readonly ComparisonNotice[];
  rulesVersion: string;
}>;

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isUuid(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value);
}

function record(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
  return value as Record<string, unknown>;
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new TypeError(`${label} must be a non-empty string`);
  }
  return value;
}

function nullableText(value: unknown, label: string): string | null {
  return value === null ? null : text(value, label);
}

function list(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value)) throw new TypeError(`${label} must be an array`);
  return value;
}

function parseSource(value: unknown): SourceMetadata {
  const source = record(value, "source");
  return {
    dataset: text(source.dataset, "source.dataset"),
    license: text(source.license, "source.license"),
    provider: text(source.provider, "source.provider"),
    retrievedAt: text(source.retrieved_at ?? source.retrievedAt, "source.retrieved_at"),
  };
}

function collectSources(overview: Record<string, unknown>): readonly SourceMetadata[] {
  const candidates: unknown[] = [];
  const address = record(overview.address, "overview.address");
  candidates.push(address.source);

  for (const section of [
    "property",
    "energy_registration",
    "neighborhood_indicators",
    "air_quality",
  ] as const) {
    const value = overview[section];
    if (value !== null && value !== undefined)
      candidates.push(record(value, section).source);
  }

  const administrative = overview.administrative_context;
  if (administrative !== null && administrative !== undefined) {
    candidates.push(
      ...list(record(administrative, "administrative_context").sources, "sources"),
    );
  }

  const unique = new Map<string, SourceMetadata>();
  for (const candidate of candidates) {
    const source = parseSource(candidate);
    unique.set(`${source.provider}:${source.dataset}:${source.retrievedAt}`, source);
  }
  return [...unique.values()];
}

function collectContextNotes(overview: Record<string, unknown>): readonly string[] {
  const notes: string[] = [];
  const energy = overview.energy_registration;
  if (energy !== null && energy !== undefined) {
    const registration = record(
      record(energy, "energy_registration").registration,
      "registration",
    );
    notes.push(
      `Energy registration valid until ${text(registration.valid_until, "valid_until")}`,
    );
  }
  const neighborhood = overview.neighborhood_indicators;
  if (neighborhood !== null && neighborhood !== undefined) {
    const datasetYear = record(neighborhood, "neighborhood_indicators").dataset_year;
    if (typeof datasetYear !== "number")
      throw new TypeError("dataset_year must be a number");
    notes.push(`CBS neighbourhood reference year ${datasetYear}`);
  }
  const airQuality = overview.air_quality;
  if (airQuality !== null && airQuality !== undefined) {
    for (const value of list(
      record(airQuality, "air_quality").observations,
      "observations",
    )) {
      const observation = record(value, "observation");
      const station = record(observation.station, "station");
      const distance = station.distance_km;
      if (typeof distance !== "number")
        throw new TypeError("station.distance_km must be a number");
      notes.push(
        `${text(observation.pollutant, "pollutant")} observed until ${text(observation.measured_until, "measured_until")} at ${text(station.name, "station.name")} (${distance} km away)`,
      );
    }
  }
  return notes;
}

function parseHome(value: unknown): ComparedHome {
  const home = record(value, "home");
  const addressId = home.address_id ?? home.addressId;
  if (!isUuid(addressId)) throw new TypeError("home.address_id must be a UUID");
  const unavailableReason = nullableText(
    home.unavailable_reason ?? home.unavailableReason ?? null,
    "home.unavailable_reason",
  );
  if ("displayName" in home) {
    return {
      addressId,
      contextNotes: list(home.contextNotes, "home.contextNotes").map((item) =>
        text(item, "context note"),
      ),
      displayName: nullableText(home.displayName, "home.displayName"),
      sources: list(home.sources, "home.sources").map(parseSource),
      unavailableReason,
    };
  }
  if (home.overview === null) {
    if (unavailableReason === null)
      throw new TypeError("unavailable home requires a reason");
    return {
      addressId,
      contextNotes: [],
      displayName: null,
      sources: [],
      unavailableReason,
    };
  }

  const overview = record(home.overview, "home.overview");
  const address = record(overview.address, "overview.address");
  const street = text(address.street, "address.street");
  const houseNumber = text(address.house_number, "address.house_number");
  const houseLetter =
    address.house_letter === null
      ? ""
      : text(address.house_letter, "address.house_letter");
  const suffix =
    address.house_number_suffix === null
      ? ""
      : `-${text(address.house_number_suffix, "address.house_number_suffix")}`;
  const postalCode = text(address.postal_code, "address.postal_code");
  const city = text(address.city, "address.city");
  return {
    addressId,
    contextNotes: collectContextNotes(overview),
    displayName: `${street} ${houseNumber}${houseLetter}${suffix}, ${postalCode} ${city}`,
    sources: collectSources(overview),
    unavailableReason,
  };
}

function parseValue(value: unknown): ComparedValue {
  const item = record(value, "metric value");
  const addressId = item.address_id ?? item.addressId;
  const isBaseline = item.is_baseline ?? item.isBaseline;
  if (!isUuid(addressId)) throw new TypeError("value.address_id must be a UUID");
  if (typeof isBaseline !== "boolean")
    throw new TypeError("value.is_baseline must be boolean");
  const scalar = item.value;
  if (scalar !== null && typeof scalar !== "string" && typeof scalar !== "number") {
    throw new TypeError("value.value must be a scalar or null");
  }
  return {
    addressId,
    isBaseline,
    missingReason: nullableText(
      item.missing_reason ?? item.missingReason ?? null,
      "value.missing_reason",
    ),
    value: scalar,
  };
}

function parseMetric(value: unknown): ComparedMetric {
  const comparison = record(value, "metric comparison");
  const metric =
    "metric" in comparison ? record(comparison.metric, "metric") : comparison;
  return {
    definition: text(metric.definition, "metric.definition"),
    key: text(metric.key, "metric.key"),
    label: text(metric.label, "metric.label"),
    scope: text(metric.scope, "metric.scope"),
    unit: text(metric.unit, "metric.unit"),
    values: list(comparison.values, "metric.values").map(parseValue),
  };
}

export function parseLiveComparison(value: unknown): LiveComparison {
  const response = record(value, "comparison response");
  const homes = list(response.homes, "homes").map(parseHome);
  if (homes.length < 2 || homes.length > 5)
    throw new TypeError("comparison requires 2–5 homes");
  const ids = homes.map((home) => home.addressId);
  if (new Set(ids).size !== ids.length)
    throw new TypeError("comparison homes must be unique");

  const metrics = list(response.metrics, "metrics").map(parseMetric);
  if (metrics.some((metric) => metric.values.length !== homes.length)) {
    throw new TypeError("each metric must contain one value per home");
  }
  if (
    metrics.some((metric) => {
      const valueIds = metric.values.map((value) => value.addressId);
      return (
        new Set(valueIds).size !== ids.length ||
        ids.some((id) => !valueIds.includes(id))
      );
    })
  ) {
    throw new TypeError("metric values must match comparison homes");
  }

  return {
    homes,
    metrics,
    notices: list(response.notices, "notices").map((value) => {
      const notice = record(value, "notice");
      return {
        code: text(notice.code, "notice.code"),
        message: text(notice.message, "notice.message"),
      };
    }),
    rulesVersion: text(
      response.rules_version ?? response.rulesVersion,
      "rules_version",
    ),
  };
}

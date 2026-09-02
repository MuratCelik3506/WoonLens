export type SourceMetadata = Readonly<{
  dataset: string;
  license: string;
  provider: string;
  retrievedAt: string;
}>;

export type SpatialCoordinates = Readonly<{
  latitude: number;
  longitude: number;
}>;

export type MonitoringStationLocation = Readonly<{
  coordinates: SpatialCoordinates;
  distanceKm: number;
  id: string;
  name: string;
  operator: string;
  stationType: string;
}>;

export type HomeDetailFact = Readonly<{
  label: string;
  value: number | string | readonly string[] | null;
  unit: string | null;
}>;

export type HomeDetailSection = Readonly<{
  facts: readonly HomeDetailFact[];
  level: "property" | "building" | "neighborhood" | "monitoring-station";
  limitation: string | null;
  title: string;
}>;

export type ComparedHome = Readonly<{
  addressId: string;
  contextNotes: readonly string[];
  coordinates: SpatialCoordinates | null;
  details: readonly HomeDetailSection[];
  displayName: string | null;
  sources: readonly SourceMetadata[];
  stations: readonly MonitoringStationLocation[];
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

export type ComparisonInsight = Readonly<{
  addressIds: readonly string[];
  classification: string;
  message: string;
  metricKey: string;
  ruleId: string;
}>;

export type SourceAudit = Readonly<{
  addressId: string;
  classification: string;
  fields: readonly [string, string];
  message: string;
  ruleId: string;
  values: readonly [number | string | null, number | string | null];
}>;

export type LiveComparison = Readonly<{
  audits: readonly SourceAudit[];
  homes: readonly ComparedHome[];
  insights: readonly ComparisonInsight[];
  metrics: readonly ComparedMetric[];
  notices: readonly ComparisonNotice[];
  rulesVersion: string;
}>;

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

const INSIGHT_CLASSIFICATIONS = new Set([
  "context_only",
  "descriptive_extreme",
  "directional_indicator",
  "insufficient_data",
  "not_ranked",
  "same",
]);
const AUDIT_CLASSIFICATIONS = new Set([
  "definition-difference",
  "match",
  "missing",
  "possible-conflict",
]);

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

function optionalRecord(value: unknown, label: string): Record<string, unknown> | null {
  return value === null || value === undefined ? null : record(value, label);
}

function coordinates(value: unknown, label: string): SpatialCoordinates {
  const item = record(value, label);
  if (typeof item.latitude !== "number" || typeof item.longitude !== "number") {
    throw new TypeError(`${label} must contain numeric latitude and longitude`);
  }
  if (
    item.latitude < -90 ||
    item.latitude > 90 ||
    item.longitude < -180 ||
    item.longitude > 180
  ) {
    throw new TypeError(`${label} is outside the supported coordinate range`);
  }
  return { latitude: item.latitude, longitude: item.longitude };
}

function parseStation(value: unknown): MonitoringStationLocation {
  const station = record(value, "monitoring station");
  if (
    typeof station.distance_km !== "number" &&
    typeof station.distanceKm !== "number"
  ) {
    throw new TypeError("station distance must be a number");
  }
  return {
    coordinates: coordinates(station.coordinates, "station coordinates"),
    distanceKm: (station.distance_km ?? station.distanceKm) as number,
    id: text(station.id, "station.id"),
    name: text(station.name, "station.name"),
    operator: text(station.operator, "station.operator"),
    stationType: text(
      station.station_type ?? station.stationType,
      "station.station_type",
    ),
  };
}

function collectStations(
  overview: Record<string, unknown>,
): readonly MonitoringStationLocation[] {
  const air = optionalRecord(overview.air_quality, "air_quality");
  if (!air) return [];
  const unique = new Map<string, MonitoringStationLocation>();
  for (const item of list(air.observations, "observations")) {
    const observation = record(item, "observation");
    const station = parseStation(observation.station);
    unique.set(
      `${station.id}:${station.coordinates.longitude}:${station.coordinates.latitude}`,
      station,
    );
  }
  return [...unique.values()];
}

function detailValue(value: unknown, label: string): HomeDetailFact["value"] {
  if (value === null || typeof value === "string" || typeof value === "number") {
    return value;
  }
  if (Array.isArray(value)) return value.map((item) => text(item, label));
  throw new TypeError(`${label} must be a scalar, string list, or null`);
}

function fact(
  source: Record<string, unknown>,
  key: string,
  label: string,
  unit: string | null = null,
): HomeDetailFact {
  return { label, unit, value: detailValue(source[key] ?? null, key) };
}

function collectDetails(
  overview: Record<string, unknown>,
): readonly HomeDetailSection[] {
  const sections: HomeDetailSection[] = [];
  const property = optionalRecord(overview.property, "property");
  if (property) {
    const unit = record(property.residential_unit, "residential_unit");
    sections.push({
      facts: [
        fact(unit, "registered_area_m2", "BAG registered area", "m²"),
        fact(unit, "use_purposes", "Usage purposes"),
        fact(unit, "status", "Residential-unit status"),
        fact(unit, "id", "BAG residential-unit ID"),
      ],
      level: "property",
      limitation:
        "BAG registered area is an official register value, not measured living area.",
      title: "BAG property",
    });
    for (const [index, item] of list(property.buildings, "buildings").entries()) {
      const building = record(item, "building");
      sections.push({
        facts: [
          fact(building, "construction_year", "Construction year", "year"),
          fact(building, "use_purposes", "Usage purposes"),
          fact(building, "status", "Building status"),
          fact(building, "residential_unit_count", "Residential-unit count"),
          fact(building, "id", "BAG building ID"),
        ],
        level: "building",
        limitation: null,
        title: `BAG building ${index + 1}`,
      });
    }
  }

  const energy = optionalRecord(overview.energy_registration, "energy_registration");
  if (energy) {
    const registration = record(energy.registration, "energy registration");
    sections.push({
      facts: [
        fact(registration, "energy_class", "Energy class"),
        fact(registration, "registration_date", "Registration date"),
        fact(registration, "inspection_date", "Inspection date"),
        fact(registration, "valid_until", "Valid until"),
        fact(registration, "assessment_type", "Assessment type"),
        fact(registration, "registration_status", "Registration status"),
        fact(registration, "building_type", "Building type"),
        fact(registration, "building_subtype", "Building subtype"),
        fact(registration, "thermal_zone_area_m2", "Thermal-zone area", "m²"),
        fact(registration, "energy_demand_kwh_m2_year", "Energy demand", "kWh/m²/year"),
        fact(
          registration,
          "primary_fossil_energy_kwh_m2_year",
          "Primary fossil energy",
          "kWh/m²/year",
        ),
        fact(registration, "renewable_energy_share_pct", "Renewable-energy share", "%"),
        fact(registration, "calculated_co2_kg_m2_year", "Calculated CO₂", "kg/m²/year"),
        fact(
          registration,
          "calculated_energy_use_kwh_m2_year",
          "Calculated energy use",
          "kWh/m²/year",
        ),
        fact(registration, "bag_object_id", "BAG object ID"),
        fact(registration, "bag_building_ids", "BAG building IDs"),
      ],
      level: "property",
      limitation:
        "EP-Online thermal-zone area uses a different definition from BAG registered area.",
      title: "EP-Online energy registration",
    });
  }

  const neighborhood = optionalRecord(
    overview.neighborhood_indicators,
    "neighborhood_indicators",
  );
  if (neighborhood) {
    const area = record(neighborhood.neighborhood, "neighborhood");
    const indicators = list(neighborhood.indicators, "indicators").map((item) => {
      const indicator = record(item, "indicator");
      return {
        label: text(indicator.label, "indicator.label"),
        unit: text(indicator.unit, "indicator.unit"),
        value:
          indicator.value === null
            ? `Unavailable: ${text(indicator.missing_reason, "indicator.missing_reason").replaceAll("_", " ")}`
            : detailValue(indicator.value, "indicator.value"),
      };
    });
    sections.push({
      facts: [
        fact(area, "name", "Neighbourhood"),
        fact(area, "code", "CBS neighbourhood code"),
        fact(neighborhood, "dataset_year", "Dataset year", "year"),
        fact(neighborhood, "dataset_id", "CBS dataset ID"),
        ...indicators,
      ],
      level: "neighborhood",
      limitation:
        "These statistics describe the neighbourhood, not the selected property.",
      title: "CBS neighbourhood context",
    });
  }

  const air = optionalRecord(overview.air_quality, "air_quality");
  if (air) {
    for (const item of list(air.observations, "observations")) {
      const observation = record(item, "observation");
      const station = record(observation.station, "station");
      sections.push({
        facts: [
          fact(
            observation,
            "value",
            text(observation.label, "observation.label"),
            text(observation.unit, "observation.unit"),
          ),
          fact(observation, "pollutant", "Pollutant"),
          fact(observation, "measured_from", "Measured from"),
          fact(observation, "measured_until", "Measured until"),
          fact(observation, "status", "Observation status"),
          fact(station, "name", "Station"),
          fact(station, "operator", "Operator"),
          fact(station, "station_type", "Station type"),
          fact(station, "distance_km", "Distance from address", "km"),
          fact(station, "id", "Station ID"),
        ],
        level: "monitoring-station",
        limitation: text(air.limitation, "air_quality.limitation"),
        title: `${text(observation.pollutant, "pollutant")} station context`,
      });
    }
  }
  const unavailable = overview.unavailable_sections ?? [];
  const unavailableMetadata: Record<
    string,
    { level: HomeDetailSection["level"]; title: string }
  > = {
    administrative_context: {
      level: "neighborhood",
      title: "Administrative context",
    },
    air_quality: {
      level: "monitoring-station",
      title: "Luchtmeetnet station context",
    },
    energy_registration: {
      level: "property",
      title: "EP-Online energy registration",
    },
    neighborhood_indicators: {
      level: "neighborhood",
      title: "CBS neighbourhood context",
    },
    property: { level: "property", title: "BAG property" },
  };
  for (const value of list(unavailable, "unavailable_sections")) {
    const item = record(value, "unavailable section");
    const name = text(item.section, "unavailable section name");
    const metadata = unavailableMetadata[name];
    if (!metadata) throw new TypeError("unavailable section name is unsupported");
    sections.push({
      facts: [
        {
          label: "Availability",
          unit: null,
          value: `Unavailable: ${text(item.reason, "unavailable reason").replaceAll("_", " ")}`,
        },
      ],
      level: metadata.level,
      limitation: "Missing official data is not evidence of poor property quality.",
      title: metadata.title,
    });
  }
  return sections;
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
      coordinates:
        home.coordinates === null || home.coordinates === undefined
          ? null
          : coordinates(home.coordinates, "home coordinates"),
      details: list(home.details ?? [], "home.details").map((item) => {
        const section = record(item, "home detail section");
        const level = text(section.level, "detail level") as HomeDetailSection["level"];
        if (
          !["property", "building", "neighborhood", "monitoring-station"].includes(
            level,
          )
        )
          throw new TypeError("detail level is unsupported");
        return {
          facts: list(section.facts, "detail facts").map((value) => {
            const item = record(value, "detail fact");
            return {
              label: text(item.label, "detail fact label"),
              unit: nullableText(item.unit ?? null, "detail fact unit"),
              value: detailValue(item.value, "detail fact value"),
            };
          }),
          level,
          limitation: nullableText(section.limitation ?? null, "detail limitation"),
          title: text(section.title, "detail title"),
        };
      }),
      displayName: nullableText(home.displayName, "home.displayName"),
      sources: list(home.sources, "home.sources").map(parseSource),
      stations: list(home.stations ?? [], "home.stations").map(parseStation),
      unavailableReason,
    };
  }
  if (home.overview === null) {
    if (unavailableReason === null)
      throw new TypeError("unavailable home requires a reason");
    return {
      addressId,
      contextNotes: [],
      coordinates: null,
      details: [],
      displayName: null,
      sources: [],
      stations: [],
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
    coordinates: coordinates(address.coordinates, "address coordinates"),
    details: collectDetails(overview),
    displayName: `${street} ${houseNumber}${houseLetter}${suffix}, ${postalCode} ${city}`,
    sources: collectSources(overview),
    stations: collectStations(overview),
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

function classification(
  value: unknown,
  allowed: ReadonlySet<string>,
  label: string,
): string {
  const result = text(value, label);
  if (!allowed.has(result)) throw new TypeError(`${label} is unsupported`);
  return result;
}

function scalar(value: unknown, label: string): number | string | null {
  if (value === null || typeof value === "string" || typeof value === "number") {
    return value;
  }
  throw new TypeError(`${label} must be a scalar or null`);
}

function parseInsight(value: unknown): ComparisonInsight {
  const insight = record(value, "insight");
  const addressIds = list(
    insight.address_ids ?? insight.addressIds,
    "insight.address_ids",
  ).map((addressId) => {
    if (!isUuid(addressId)) throw new TypeError("insight address must be a UUID");
    return addressId;
  });
  if (new Set(addressIds).size !== addressIds.length) {
    throw new TypeError("insight addresses must be unique");
  }
  return {
    addressIds,
    classification: classification(
      insight.classification,
      INSIGHT_CLASSIFICATIONS,
      "insight.classification",
    ),
    message: text(insight.message, "insight.message"),
    metricKey: text(insight.metric_key ?? insight.metricKey, "insight.metric_key"),
    ruleId: text(insight.rule_id ?? insight.ruleId, "insight.rule_id"),
  };
}

function pair(value: unknown, label: string): readonly [unknown, unknown] {
  const items = list(value, label);
  if (items.length !== 2) throw new TypeError(`${label} must contain two items`);
  return [items[0], items[1]];
}

function parseAudit(value: unknown): SourceAudit {
  const audit = record(value, "audit");
  const addressId = audit.address_id ?? audit.addressId;
  if (!isUuid(addressId)) throw new TypeError("audit.address_id must be a UUID");
  const fields = pair(audit.fields, "audit.fields");
  const values = pair(audit.values, "audit.values");
  return {
    addressId,
    classification: classification(
      audit.classification,
      AUDIT_CLASSIFICATIONS,
      "audit.classification",
    ),
    fields: [text(fields[0], "audit field"), text(fields[1], "audit field")],
    message: text(audit.message, "audit.message"),
    ruleId: text(audit.rule_id ?? audit.ruleId, "audit.rule_id"),
    values: [scalar(values[0], "audit value"), scalar(values[1], "audit value")],
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
  const insights = list(response.insights, "insights").map(parseInsight);
  const metricKeys = new Set(metrics.map((metric) => metric.key));
  if (
    insights.some(
      (insight) =>
        !metricKeys.has(insight.metricKey) ||
        insight.addressIds.some((addressId) => !ids.includes(addressId)),
    )
  ) {
    throw new TypeError("insight references must match comparison evidence");
  }
  const audits = list(response.audits, "audits").map(parseAudit);
  if (audits.some((audit) => !ids.includes(audit.addressId))) {
    throw new TypeError("audit address must match comparison homes");
  }

  return {
    audits,
    homes,
    insights,
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

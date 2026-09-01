# WoonLens UI/UX Specification

## 1. Purpose and Authority

This document defines the initial web-interface contract for WoonLens. It turns
the product scope, data rules, and agreed interaction decisions into testable UI
behaviour. It is authoritative for presentation and interaction; it does not
replace the product boundaries in [`PROJECT_SCOPE.md`](PROJECT_SCOPE.md), the
data contracts in [`DATA_SOURCE_API.md`](DATA_SOURCE_API.md), or architectural
decisions.

The first interface must feel like an independent housing-research tool rather
than a property-listing marketplace. It prioritizes official facts, provenance,
uncertainty, and understandable differences over promotion or persuasion.

## 2. Experience Principles

1. **Guest first.** A user can search, compare, inspect sources, and download
   the current result without creating an account.
2. **Neutral by design.** WoonLens reports observable differences. It does not
   score, rank, recommend, declare winners, or label a home as good or bad.
3. **Provenance is part of the value.** Source, data level, retrieval time,
   reference period, and applicable qualifications remain discoverable from
   the value they describe.
4. **Absence is not failure.** A missing provider record, a temporarily
   unavailable provider, and an unsupported comparison are distinct states.
5. **Live means transient.** Provider facts are fetched for the current request
   and are not presented as a stored WoonLens property profile.
6. **Progressive disclosure.** Essential facts appear first; definitions,
   identifiers, and complete source metadata remain available without
   overwhelming the initial view.
7. **Accessible from the start.** Accessibility is an acceptance criterion,
   not a later visual refinement.

## 3. Information Architecture

The initial public navigation contains:

- **Compare** — home, address selection, and the active comparison
- **How it works** — the live data journey and interpretation boundaries
- **Data sources** — provider, dataset, data-level, and attribution details
- **Privacy** — transient provider-data handling and guest/account boundaries
- **About** — purpose, limitations, and neutrality principles
- **GitHub** — the open-source repository

Authentication is not part of the initial guest interface. A future sign-in
entry may be added without reducing guest capability.

## 4. Primary Guest Journey

```text
Open Compare
  -> search for an official Dutch address
  -> select one explicit suggestion
  -> add it to the comparison tray
  -> repeat until two to five distinct homes are selected
  -> run the live comparison
  -> inspect overview and detailed sections
  -> inspect source and uncertainty details
  -> optionally change the selection or download JSON/PDF
```

The interface must not require uploads. Selecting a suggestion adds the home to
the tray without navigating to an intermediate property-detail page.

### 4.1 Address search

- The page has one dominant address-search field above a short product
  explanation.
- Suggestions appear as the user types and identify themselves as official
  address results.
- A typed string is not treated as a resolved home; the user must select a
  suggestion.
- Keyboard users can enter the field, move through suggestions, select one,
  and dismiss the list.
- Search relevance is never exposed as property quality.
- The interface does not silently replace or infer an address variant.
- An already-selected address cannot be added again.

### 4.2 Comparison tray

- The tray is persistently visible on wider layouts and available as an
  expandable bottom panel on mobile.
- Each selection has a stable number, formatted address, and remove action.
- The number matches the home marker and comparison-column identity.
- The tray displays the current count and the maximum of five.
- **Compare homes** is disabled until two valid, distinct addresses exist.
- At five selections, adding another address is prevented with an explanatory
  message; existing selections remain removable.
- Removing or replacing a home never triggers an implicit comparison request.

### 4.3 Short product introduction

The home page stays search-led. Beneath the search, three compact statements
explain the product:

- Official public sources
- Complete comparison without an account
- Live provider facts are not stored by WoonLens

This is not a long marketing landing page and does not include listing photos,
prices, testimonials, or promotional ranking claims.

## 5. Comparison Results

The result page begins with selected addresses, the live retrieval time, and
the actions **Change homes**, **Download JSON**, and **Download PDF**. Address
headers remain identifiable while the user moves through a long comparison.

The content order is:

1. **Overview**
2. **Property**
3. **Energy**
4. **Environment**
5. **Differences**
6. **Sources**

### 5.1 Overview

The overview gives a deliberately compact first reading for every home:

- Full address
- Usage purpose or housing type when supported by the source
- Construction year
- BAG registered area
- Energy label
- Air-quality station context summary
- Missing or unavailable-data indicators
- Retrieval time

Price, listing media, owner/resident data, user ratings, and a WoonLens score
are excluded.

### 5.2 Property

Property details may include BAG address, addressable-object, and building
identifiers; registered area; usage purposes; residential-unit and building
status; construction year; unit count when available; and main/secondary
address status. Technical identifiers are secondary details, not headline
facts.

### 5.3 Energy

Energy details may include energy class; registration, inspection, and validity
dates; building type and subtype; thermal-zone area; energy demand; primary
fossil energy; renewable-energy share; and calculated CO2 emissions.

BAG registered area and EP-Online thermal-zone area must use their source
definitions and must not be presented as equivalent measurements.

### 5.4 Environment

Environment contains separately labelled contextual data:

- CBS neighbourhood name, dataset year, selected population, housing, and
  energy indicators
- RIVM/Luchtmeetnet station, operator, pollutant, observation time, status, and
  distance from the selected address

Neighbourhood and station observations must not be worded or styled as exact
measurements of the property. Different pollutants may use different nearest
compatible stations.

### 5.5 Differences

Differences use factual, directional sentences such as:

> Home 2 has 18 m² more BAG registered area than Home 1.

> Home 2 was built 24 years later than Home 1.

> No EP-Online record was found for Home 1.

The UI must not use:

- Best/worst, winner/loser, recommended/not recommended, or equivalent labels
- A combined property score or automatic ordering by desirability
- Celebration, warning, green, or red styling to imply home quality
- Unsupported causal, health, financial, legal, valuation, or inspection advice
- Missing data as evidence of poor property quality

Color may separate home identities, categories, or system states, but meaning
must also be conveyed by text or shape.

### 5.6 Sources

Every displayed fact has an adjacent source-detail trigger. Activating it
reveals, when applicable:

- Provider and dataset or collection
- Source field and official identifier
- Property, neighbourhood, or monitoring-station data level
- Retrieval time and reference period
- Transformation or comparison rule
- Provisional, stale, unavailable, or other qualification
- Attribution and official source link when redistribution permits it

The complete Sources section groups the same evidence by provider. It does not
force users to inspect every detail to understand the main comparison.

## 6. Data and System States

Each provider-backed region manages its own state. One slow or failed provider
must not hide facts already available from another provider or collapse the
entire comparison page.

| State | User-facing treatment |
| --- | --- |
| Loading | A stable placeholder and provider-specific progress text |
| Record found | Value plus source-detail access |
| No record found | `No record found` and the provider name |
| Temporarily unavailable | `Currently unavailable`, a short explanation, and a provider-specific retry action |
| Unsupported/not comparable | Explanation of the definition or scope mismatch |
| Stale | Value remains qualified by its reference date and stale status |
| Provisional | Value remains qualified as provisional |
| Partial comparison | Available homes and providers remain usable; missing portions are identified |

Technical stack traces, request headers, credentials, signed URLs, raw provider
payloads, and internal exception names are never displayed. A retry repeats the
live request; it does not recover a stored provider result.

## 7. Map Contract

The map is supporting context, not the primary comparison mechanism.

- Selected homes use numbered markers matching the tray and comparison view.
- Relevant monitoring stations may be shown with their data level and distance.
- The map does not replace textual address or station identification.
- If the map cannot load, search, comparison, provenance, and downloads remain
  available.
- Route planning, travel-time scoring, neighbourhood ranking, and drawn
  neighbourhood boundaries are outside the first UI delivery.

## 8. Responsive Behaviour

### 8.1 Wider layouts

- Search content and the fixed comparison tray may sit side by side.
- Homes appear as side-by-side comparison columns.
- Home headers remain visible or readily recoverable during vertical movement.
- Dense source information expands locally rather than widening the main table.

### 8.2 Mobile layouts

- The address search remains near the top of the page.
- The selected-home tray becomes an expandable bottom panel.
- A desktop table is not merely scaled down.
- Under each fact, home values appear in a readable vertical sequence with
  stable numbers and labels.
- Source details open with touch and never require hover.
- Change, retry, JSON, and PDF actions remain reachable.

No essential page action depends on horizontal page scrolling.

## 9. Visual Language

The interface uses a modern, calm, evidence-led identity:

- Warm neutral page background
- Dark navy primary text
- Petrol green as the main accent
- Generous whitespace and restrained information density
- Lightly rounded surfaces with limited shadow
- Data, definitions, and sources instead of decorative property photography

Red and green are reserved for genuine system/error semantics where necessary,
not for ranking properties. The experience should remain understandable in
high-contrast, dark, and reduced-motion user settings.

## 10. Accessibility Contract

The target is WCAG 2.2 level AA. At minimum:

- All search, suggestion, tray, section, disclosure, retry, and download
  controls work by keyboard.
- Focus order follows reading order and visible focus indicators are retained.
- Text and interactive controls meet applicable contrast requirements.
- Information never depends on color alone.
- Touch targets are at least 44 by 44 CSS pixels where applicable.
- Inputs have programmatic labels, descriptions, and associated error messages.
- Dynamic search results, selection-count changes, and request completion are
  announced without excessive interruption.
- Headings, tables, lists, and disclosures use semantic structures.
- Reduced-motion preferences are respected.
- Loading placeholders do not cause disruptive layout movement.
- Downloads and maps have understandable text alternatives.

Automated accessibility checks support but do not replace keyboard and screen-
reader-oriented manual review.

## 11. Language and Content

The first interface language is English. User-facing strings are centralized so
Dutch can be introduced without rewriting feature components.

- Sentences are short, literal, and non-judgmental.
- Provider-specific jargon is explained at the point of use.
- Official Dutch terms may remain when legally or technically meaningful, with
  an English explanation.
- Dates, numbers, units, and plural forms use locale-aware formatting.
- Units come from normalized backend contracts and are not invented from a
  field name in the frontend.
- `No record found` and `Currently unavailable` are never interchangeable.
- `Measured 3.2 km away` makes station context explicit.
- `Last retrieved` describes retrieval time, not necessarily the source's
  measurement or reference time.

## 12. Privacy and Optional Accounts

Guest use is the default. The UI must not introduce an authentication wall,
forced registration dialog, automatic search history, or consent-by-use claim.

If accounts are later implemented, they may organize only explicit user-owned
address references, favourites, and named comparison lists. Opening a saved
item runs the live provider pipeline again. The interface must not imply that
official property facts, comparison results, environmental observations, or
generated reports were stored in the account.

JSON and PDF are generated for the active comparison and clearly display their
generation/retrieval time. WoonLens does not retain the generated download on
the server.

## 13. Frontend Architecture Direction

The planned frontend remains part of the WoonLens modular monolith deployment;
it does not introduce independent business microservices.

- **Next.js and TypeScript** for the web application and typed public contracts
- **Tailwind CSS** for design tokens and consistent responsive styling
- **Accessible headless components** for dialogs, disclosures, tooltips, and
  other complex controls
- **TanStack Query** for request, loading, retry, cancellation, and transient
  client-cache behaviour
- **MapLibre GL** for provider-independent map presentation
- **Vitest and Testing Library** for component and user-behaviour tests
- **Playwright** for browser-level guest comparison flows

Suggested feature-oriented structure:

```text
frontend/
├── app/
├── features/
│   ├── address-search/
│   ├── comparison/
│   ├── data-sources/
│   └── map/
├── components/
├── lib/
└── tests/
```

Feature components consume the public FastAPI contract. Provider-specific
payload interpretation remains in backend adapters and normalization logic.
Frontend client state is not permission to create durable provider-data
storage. Any client caching must remain request/session oriented, bounded, and
consistent with the product's live-data promise.

## 14. Verification Strategy

The UI implementation is complete only when evidence covers:

- Address autocomplete selection, keyboard operation, duplicate prevention,
  and two-to-five validation
- Desktop tray and mobile bottom-panel behaviour
- Complete guest comparison without authentication
- Per-provider loading, no-record, unavailable, partial, and retry states
- Neutral difference language and absence of ranking/score presentation
- Source detail, data-level, retrieval-time, reference-time, and distance labels
- Responsive comparison at representative desktop and mobile widths
- Automated accessibility checks plus manual keyboard review
- JSON/PDF availability and generation-time communication
- Map failure without loss of the textual comparison
- No analytics or logs containing unredacted address searches by default

Visual review must include empty, loading, partial, complete, and failure states;
a single ideal-data screenshot is insufficient acceptance evidence.

## 15. Deferred Decisions

The following require later issues or ADRs before implementation:

- Authentication provider and account-data retention/deletion details
- Exact component library and design-token implementation
- Production map style and tile-provider terms
- Dutch translation and locale negotiation
- Analytics, if any, with a privacy review before collection
- Shareable comparison links and their data-retention model


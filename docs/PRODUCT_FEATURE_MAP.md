# WoonLens Product Feature Map

## Product Purpose

WoonLens helps people compare between two and five Dutch homes using live facts
from official public sources. It explains differences, definitions, missing
values, source dates, and geographic data levels without producing an opaque
property score or storing provider data.

## Product Rules

- A comparison contains at least two and at most five homes.
- The complete comparison workflow works without an account.
- Provider responses and derived property facts are processed in memory and are
  not persisted, cached, logged, or retained in generated reports on the server.
- Official data is fetched again whenever a comparison runs.
- Accounts are optional and do not unlock additional official facts.
- Account storage is limited to explicit favourites and named comparison
  references created by the user.
- WoonLens does not keep automatic search history.
- JSON and PDF downloads are generated on demand and are not retained by the
  server.

## Guest User Journey

```text
Open WoonLens
  -> search for an official address
  -> add the first home to the comparison tray
  -> search for and add a second home
  -> optionally add up to three more homes
  -> run the live comparison
  -> inspect overview, property, energy, area, differences, and sources
  -> optionally download JSON or PDF
  -> leave without provider data being retained
```

The Compare action remains disabled until two valid, distinct addresses are
selected. The UI prevents more than five selections and allows removal or
replacement before rerunning the comparison.

## Signed-In User Journey

Signed-in users use the same live comparison pipeline. They may additionally:

- Add an address reference to favourites
- Save a two-to-five-address comparison list with a user-provided name
- Reopen, rename, or delete a saved comparison
- Add a favourite to the current comparison tray
- Remove a favourite
- Delete their account and saved organisation data

Opening a favourite or saved comparison triggers new official provider
requests. Earlier property facts and comparison results are not restored from
WoonLens storage.

## Primary Screens

Detailed interaction, responsive, content, accessibility, and frontend
requirements are defined in
[`UI_UX_SPECIFICATION.md`](UI_UX_SPECIFICATION.md).

### 1. Home and Search

Purpose: build a valid comparison set.

Components:

- Short product explanation
- Official address autocomplete
- Selected-home comparison tray
- Add, remove, and replace actions
- Selection count and two-to-five validation
- Compare action
- Optional sign-in entry that never blocks guest use

On mobile, the comparison tray is a bottom panel. On wider layouts, it may be a
fixed side panel.

### 2. Comparison Results

Purpose: understand meaningful differences between the selected homes.

Sections:

- Overview
- Property
- Energy
- Area
- Differences and Sources

Actions:

- Add or remove a home and rerun
- Download the current JSON or PDF result
- Save the comparison when signed in
- Sign in to save without hiding the current guest result

Important facts are visible by default. Provider identifiers, complete
provenance, and technical definitions are available through expandable detail.

### 3. Sign In and Registration

Purpose: enable optional organisation features.

Capabilities:

- Register
- Sign in
- Recover account access
- Continue without an account
- View the privacy explanation before creating an account

The authentication mechanism is a later technical decision. Account creation
must not imply consent to automatic search-history storage.

### 4. Saved Comparisons

Purpose: manage named address sets, not saved official data.

Capabilities:

- List saved comparison names and minimum address references
- Open and rerun with live data
- Rename
- Delete
- Clearly state that displayed facts may differ because data is freshly fetched

### 5. Favourites

Purpose: manage explicitly selected address references.

Capabilities:

- List favourites
- Add a favourite to the comparison tray
- Remove a favourite
- Select several favourites for a new comparison

## Comparison Information Architecture

### Overview

- Full address
- Construction year
- BAG registered area
- Usage purpose
- Building status
- Energy label
- Energy-label validity date
- Neighbourhood name

### Property

- BAG addressable-object and building identifiers
- Registered area
- Usage purposes
- Residential-unit status
- Building status
- Construction year
- Number of residential units where available
- Main or secondary address status

### Energy

- Energy class
- Registration, inspection, and validity dates
- Building type and subtype
- Thermal-zone area
- Energy demand
- Primary fossil energy
- Renewable-energy share
- Calculated CO2 emissions

### Area

Neighbourhood values are labelled as neighbourhood context:

- Neighbourhood name and dataset year
- Population and household count
- Population density
- Average residential WOZ value
- Average electricity delivery
- Average natural-gas consumption
- Homes with solar power

Monitoring values are labelled as station context:

- Station name, operator, and type
- Distance from the selected address
- Pollutant
- Measurement time window
- Provisional or ratified status when available

### Differences and Sources

- Differences between directly comparable values
- Definition differences such as BAG registered area versus EP-Online
  thermal-zone area
- Missing values and unavailable providers
- Stale or provisional status
- Property, neighbourhood, and station-level distinctions
- Official source link, dataset, retrieval time, and reference period
- Human-readable explanation for every classified difference

## Public Backend Use Cases

```text
GET  /api/v1/health
GET  /api/v1/addresses/suggest?q=...
GET  /api/v1/addresses/resolve?id=...
POST /api/v1/comparisons
POST /api/v1/comparison-downloads/json
POST /api/v1/comparison-downloads/pdf
```

The public comparison use case:

1. Validates two to five distinct address references.
2. Resolves official identifiers.
3. Calls required providers with bounded asynchronous I/O.
4. Normalizes provider responses in memory.
5. Applies comparison and explanation rules.
6. Returns the live result.
7. Discards provider payloads and derived facts when the request completes.

Downloads run the same live pipeline or operate on the current request result
without creating server-side report storage.

## Account Backend Use Cases

```text
GET    /api/v1/me
DELETE /api/v1/me

GET    /api/v1/favourites
POST   /api/v1/favourites
DELETE /api/v1/favourites/{id}

GET    /api/v1/saved-comparisons
POST   /api/v1/saved-comparisons
PATCH  /api/v1/saved-comparisons/{id}
DELETE /api/v1/saved-comparisons/{id}
POST   /api/v1/saved-comparisons/{id}/run
```

The account database may contain only:

```text
User
FavouriteAddressReference
SavedComparison
SavedComparisonAddressReference
```

The exact minimum address-reference schema, authentication method, consent,
retention, and deletion rules require decisions before account implementation.

The account database must not contain:

- BAG property facts
- EP-Online energy facts
- CBS values
- Luchtmeetnet measurements
- Provider responses
- Normalized comparison results
- Generated JSON or PDF files
- Automatic search history

## Delivery Sequence

### MVP 1 — Guest Live Comparison

Includes:

- Address search and selection
- Two-to-five comparison tray
- Live provider retrieval
- Overview, Property, Energy, Area, and Differences and Sources sections
- Missing, unavailable, stale, and definition-difference explanations
- Source attribution
- Non-retained JSON and PDF downloads

Requires no account database.

### MVP 2 — Optional Account Organisation

Includes:

- Registration, sign-in, recovery, and account deletion
- Explicit favourites
- Named saved comparison lists
- Live rerun of saved items
- Account-data privacy and deletion controls

Does not add property facts unavailable to guest users.

## Explicitly Excluded

- File, document, or property-listing uploads
- Property-listing scraping
- Automatic search-history storage
- Provider-response or comparison-result persistence
- Historical property timelines
- Price, bid, mortgage, or investment prediction
- Universal property scores or automatic best-home ranking
- Owner or resident personal information
- Legal, valuation, structural, or inspection conclusions

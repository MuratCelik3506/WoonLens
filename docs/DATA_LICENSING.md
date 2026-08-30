# Third-Party Data Licensing and Usage

**Last reviewed:** 2026-08-28

This document separates the license for WoonLens source code from the terms
that apply to external datasets and services. It is a project compliance note,
not legal advice.

## Code and data are licensed separately

The MIT License in this repository covers source code and original
documentation written for WoonLens. It does not relicense, transfer ownership
of, or override the terms of any third-party dataset.

The repository must not contain a bulk copy of upstream records unless the
specific dataset terms have been checked and redistribution is clearly allowed.

## Source summary

### PDOK Location API

- Official service: <https://api.pdok.nl/kadaster/location-api/v1?f=html>
- The service metadata identifies the license as Creative Commons Attribution
  4.0.
- Authentication and usage fees are not required.
- WoonLens responses identify PDOK, the Location API address collection,
  retrieval time, and license; they do not expose raw payloads or upstream
  detail links.

### Kadaster BAG through PDOK

- Official service: <https://api.pdok.nl/kadaster/bag/ogc/v2?f=html&lang=en>
- The service metadata identifies the dataset license as Public Domain Mark
  1.0.
- Authentication is not required and the service is provided without a usage
  fee.
- WoonLens should still record Kadaster/PDOK as the source, the retrieval time,
  and the relevant BAG identifiers for provenance.

### Statistics Netherlands (CBS)

- The implemented administrative-context sources are CBS Wijken en Buurten
  2026 and CBS Gebiedsindelingen, both exposed through PDOK under CC BY 4.0.
- WoonLens returns the dataset name, retrieval time, and license with the
  request-scoped result and does not redistribute boundary geometry.
- Official copyright terms: <https://www.cbs.nl/en-gb/about-us/website/copyright>
- Unless a specific item states otherwise, CBS website content is provided
  under Creative Commons Attribution 4.0.
- Reuse requires attribution to Statistics Netherlands (CBS).
- WoonLens must not imply that CBS endorses the application or a derived
  conclusion.
- The CBS logo and website design are not covered by the data attribution
  permission and must not be copied into the product.

Suggested report attribution:

```text
Source: Statistics Netherlands (CBS), dataset/table identifier, reference
period and retrieval date. Derived presentation by WoonLens; not endorsed by
CBS.
```

### EP-Online

- Official terms: <https://apikey.ep-online.nl/Home/TermsOfUse>
- An API key is personal and must not be shared with another person.
- The provided data may be used, subject to the service's restrictions.
- Directly supplying large quantities of individually identifiable records to
  third parties, such as redistributing part of the original dataset, is not
  allowed under the published terms.
- Indirect presentation of individual records in large numbers is described as
  permitted when it forms part of a housing purchase or rental website.

WoonLens policy:

- Every self-hosted user supplies their own API key.
- The key is stored only in a local `.env` file and is never included in code,
  logs, reports, screenshots, fixtures, issues, or pull requests.
- The repository does not distribute a bulk EP-Online export.
- Tests use synthetic or redacted fixtures rather than a redistributable cache
  of production responses.
- Reports show only the records required for the addresses explicitly queried
  by the user.

### RIVM Luchtmeetnet

- Download directory: <https://data.rivm.nl/data/luchtmeetnet/>
- Dataset documentation:
  <https://data.rivm.nl/data/luchtmeetnet/readme.pdf>
- Current-year measurements can be provisionally validated and are not the
  same as the ratified historical datasets in `Vastgesteld-jaar`.
- The reviewed documentation does not state a single general open-data license
  name for every downloadable file.

WoonLens must therefore treat RIVM data conservatively:

- Attribute RIVM and the participating monitoring-network data owner.
- Preserve whether a value is provisional or ratified.
- Store retrieval and export timestamps so later corrections can be detected.
- Do not bundle or redistribute a raw RIVM dataset in a release until the
  applicable terms for that exact dataset have been confirmed.

## Repository data policy

The following must not be committed:

- Personal API keys or access tokens
- Bulk EP-Online responses or exports
- Source datasets with unconfirmed redistribution permission
- Search histories or user-submitted address logs
- Personal information about residents or property owners
- Signed download URLs or authenticated request headers

Permitted test materials should be synthetic, heavily minimized, redacted, or
explicitly licensed for redistribution. A test fixture must state its origin
and whether it is synthetic or derived.

## Provenance requirements

Every normalized value and generated report should preserve, where available:

- Dataset and provider name
- Source endpoint, table, or collection identifier
- Original object identifier
- Reference period and source status
- Retrieval timestamp
- Transformation and validation rule
- Applicable attribution text

## Review requirement

Terms and service behavior can change. Review this document before the first
public release and whenever a new dataset, endpoint, bulk download, hosted
demo, or redistribution feature is introduced.

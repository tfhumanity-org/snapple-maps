# spec/ — Apple Maps, described from the outside

Clean-room functional specs of the Apple Maps client stack, written from static
analysis of one shipped build. Read [`../CLEANROOM.md`](../CLEANROOM.md) before
citing anything here: every requirement carries a confidence marker, and nothing
in this directory was observed at runtime.

**Build studied:** Maps 3.0 (`2972.20.6.12.47`), macOS 27.0.1 (`26A434`),
arm64e, captured 21 October 2026.

## The shape of the thing

The Maps you click is a thin Catalyst app. Almost nothing it does happens in its
own process.

```
                        ┌──────────────────────────────────────┐
                        │  Maps.app  (com.apple.Maps)          │
                        │  Catalyst, sandboxed, 83 entitlements│
                        └───────┬──────────────────────────────┘
                                │ in-process frameworks
     ┌──────────────┬───────────┼─────────────┬──────────────┬────────────┐
     ▼              ▼           ▼             ▼              ▼            ▼
 GeoServices    MapKit      MapsUI       VectorKit      MapsSync    Navigation
 (334 classes) (119)        (76)          (19)           (43)         (32)
 service calls  public      app UI      tile render    user data    guidance
 data model     map view    surfaces     engine         model        model
     │
     │ XPC
     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │  daemons, one concern each                                            │
 │                                                                       │
 │  geod ............. every server call, the tile store, configuration  │
 │  navd ............. an active navigation session, outliving the app   │
 │  mapssyncd ........ the user's own data, synced through CloudKit      │
 │  destinationd ..... where you are likely to go next                   │
 │  mapspushd ........ shared ETAs and trips, over the push transport    │
 │  geoanalyticsd .... batching and uploading analytics                  │
 └───────────────────────────────────────────────────────────────────────┘
                                │ HTTPS
                                ▼
                 Apple's map services (opaque from here)
```

The split is the point. The app can be killed and the navigation keeps running.
The tile cache survives the app. Analytics upload on their own schedule. Nothing
that matters is held only in the UI process.

## The patterns worth stealing

Numbered so the spec files and any future guide can cite them. `Pnn`.

| | Pattern | Where |
|---|---|---|
| **P01** | **Configuration is layered, and the layers are named.** Five sources stack in a fixed precedence, from a value compiled into the binary up to an explicitly selected test environment. Any value can be traced to the layer that produced it. | [01](01-configuration-and-experiments.md) |
| **P02** | **Bootstrap from a manifest, not from constants.** One hard-coded URL fetches a manifest describing every other service. Endpoints move without shipping a client. | [01](01-configuration-and-experiments.md) |
| **P03** | **The experiment bucket is an identifier with an expiry.** Assignment is a stored GUID with a timestamp and a maximum age, so cohorts roll over on their own rather than pinning a device forever. | [01](01-configuration-and-experiments.md) |
| **P04** | **One key type addresses everything addressable.** A single tagged union names standard tiles, imagery meshes, traffic, transit selections, contour lines, overlays and regional resources, with the tag in the low bits. | [02](02-map-data-tiles-and-offline.md) |
| **P05** | **The data set is versioned as a whole.** Tiles belong to an "active tile group"; moving to a new edition is an explicit, observable transition with begin and end notifications, not a cache that drifts. | [02](02-map-data-tiles-and-offline.md) |
| **P06** | **Offline is a subscription, not a download.** Regions are reference-counted subscriptions over tile batches, so two overlapping downloads share storage and eviction knows what is still wanted. | [02](02-map-data-tiles-and-offline.md) |
| **P07** | **Routes are requested abstractly and returned composed.** The request names waypoints and attributes; the response is a tree of legs, steps, lanes and guidance events the client renders without re-deriving. | [04](04-directions-and-navigation.md) |
| **P08** | **Server-authored, client-formatted strings.** Spoken and displayed guidance arrives as format templates plus typed arguments — distances, durations, maneuvers, prices — so the client applies locale and units. | [04](04-directions-and-navigation.md) |
| **P09** | **Navigation outlives its UI.** The session lives in a separate always-resident daemon; the app attaches to it. | [04](04-directions-and-navigation.md) |
| **P10** | **Sync the user's data, cache everything else.** The sync store separates owned records from cached server copies, and only the owned ones are authoritative. | [05](05-sync-and-user-data.md) |
| **P11** | **Contributions are signed anonymously.** User edits and reviews carry attestation certificates that prove a real device without identifying it. | [06](06-feedback-and-contributions.md) |
| **P12** | **Several identifiers, several lifetimes.** Not one device ID: a per-device-local session, an initial device session, an anonymous user identifier, feature-scoped session identifiers — each rotating on its own schedule, each carrying its own age. | [07](07-identity-privacy-and-analytics.md) |
| **P13** | **Uploads are held down, not merely scheduled.** The analytics pipeline separates what to send, when it may be sent, and a hold-down that suppresses bursts. | [07](07-identity-privacy-and-analytics.md) |
| **P14** | **One URL vocabulary, many front doors.** Custom schemes, universal links, App Intents and Spotlight all resolve into the same query-item grammar. | [08](08-entry-points-and-integration.md) |
| **P15** | **Appearance lives in data, not code.** A compiled stylesheet decides which features exist at which zoom, label sizes, traffic widths, even how far ahead a maneuver is drawn. The renderer executes those decisions. | [09](09-rendering.md) |
| **P16** | **Selectors compile to a traversal.** Style matching is a graph walk costing one step per feature attribute, not a scan over a rule list — which is what makes per-feature styling viable at map volumes. | [09](09-rendering.md) |
| **P17** | **Precompute what needs global context; refine what needs local.** Label positions are chosen server-side, where the region is visible, and adjusted on device, where the viewport is. | [09](09-rendering.md) |
| **P18** | **Choose where to be late.** Per-frame entity budgets and background label layout make the renderer deliberately behind — in places a person does not notice rather than places they do. | [09](09-rendering.md) |

## The files

| File | Covers |
|---|---|
| [`00-processes-and-frameworks.md`](00-processes-and-frameworks.md) | Bundle layout, the daemon set, Mach service surface, entitlements, which framework does what |
| [`01-configuration-and-experiments.md`](01-configuration-and-experiments.md) | The five configuration layers, the manifest bootstrap, experiments, environments, per-country configuration |
| [`02-map-data-tiles-and-offline.md`](02-map-data-tiles-and-offline.md) | Tile keys, the VMP4 container, the tile database, active tile groups, offline regions |
| [`03-places-and-search.md`](03-places-and-search.md) | The place data model, autocomplete, result refinement, categories |
| [`04-directions-and-navigation.md`](04-directions-and-navigation.md) | Directions requests, composed routes, guidance events, the navigation daemon, maneuver and error vocabularies |
| [`05-sync-and-user-data.md`](05-sync-and-user-data.md) | What syncs, the record set, CloudKit and key-value transports, history and collections |
| [`06-feedback-and-contributions.md`](06-feedback-and-contributions.md) | Report-a-problem, ratings and photos, anonymous attestation, submission lifecycle |
| [`07-identity-privacy-and-analytics.md`](07-identity-privacy-and-analytics.md) | Identifier model, location shifting, the analytics pipeline, upload policy |
| [`08-entry-points-and-integration.md`](08-entry-points-and-integration.md) | URL grammar, universal links, App Intents, suggestions and donations |
| [`09-rendering.md`](09-rendering.md) | Renderer architecture, map data types, tile chapters, the compiled stylesheet, style resolution, labels, the draw |

Each file follows the same structure: **1** Purpose & scope · **2** Concepts ·
**3** Requirements (`R-nn`, MUST/SHOULD, confidence) · **4** Algorithms
(pseudocode) · **5** Constants · **6** Rationale · **7** Design takeaways
(`NN#Tk`) · **8** Uncertainties.

Cite a requirement as `04#R12`, a takeaway as `04#T3`, a pattern as `P07`.

## What is not here

- **Rendering algorithms.** `09` specifies the renderer's structure — the data
  types, the tile chapters, the stylesheet format, style resolution, label
  composition and the shader set. It does not specify tessellation, geometry
  simplification, the collision test, the camera controller, or draping. That is
  now the largest gap.
- **The public MapKit API.** Documented by Apple; no point restating it. `00`
  records only how Maps.app itself sits on it.
- **Transit.** The data model is visible and substantial; it has not been worked
  through.
- **Server behaviour.** Out of reach by construction.
- **Version-to-version change analysis.** Needs two builds; one was read.

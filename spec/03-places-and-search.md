# 03 — Places and search

## 1 Purpose & scope

The place data model, how a query becomes results, and how a place is presented.
Covers autocomplete, result refinement, the category system, and the
server-driven place card layout.

Not covered: ranking, relevance, or anything else decided on the server.

## 2 Concepts

**A map item** is a place as the client holds it: an identity, a location, an
address, and attributes layered on from several sources.

**Autocomplete** is the as-you-type path. It is a distinct service from search,
with its own request shape, its own throttle budget (`01#R24`) and its own
result vocabulary.

**A refinement** is a filter or sort offered alongside a result set. The server
chooses which refinements exist for a given query; the client renders them.

**A place summary layout** is a server-authored description of how a place card
should be assembled. The client does not decide what a place card contains.

## 3 Requirements

### 3.1 The place identity

**R01 (observed).** A place MUST be identifiable by a stable identifier
independent of its coordinates, and that identifier MUST be expressible in a
URL (see `08`).

**R02 (observed).** A map item MUST be able to carry attributes from several
distinct sources, each modelled separately: address-book attributes, client
attributes, corrected-location attributes, routine attributes, and user values.

**R03 (derived).** Keeping attribute sources separate rather than merging them
MUST be read as a provenance requirement: the client can tell a server-supplied
address from one the user corrected from one derived from the user's own
contacts, which matters for both correctness and privacy.

**R04 (observed).** A place MUST be able to have child items and child places —
a venue containing tenants, a terminal containing gates.

**R05 (observed).** Addresses MUST be modelled structurally, with a distinct
sub-premise concept, not as a formatted string. A separate address-formatting
library with its own version is carried in the service framework to render them.

**R06 (derived).** A versioned address-formatting library MUST be read as
locale-specific address rendering being a hard enough problem to deserve its own
component with its own release cadence. Address order, which components are
shown, and which are omitted differ by country.

### 3.2 Categories

**R07 (observed).** The client MUST carry a shipped mapping from named
point-of-interest categories to numeric point-of-interest type identifiers. The
shipped mapping has 87 named categories.

**R08 (observed).** The mapping MUST be one-to-many: a single named category can
map to several numeric types. An airport category maps to three.

**R09 (derived).** The named categories MUST therefore be a stable public
vocabulary layered over a finer-grained, server-controlled type space. New types
can be introduced and folded into an existing category without a client change.

**R10 (observed).** The mapping document MUST additionally carry a set of
always-visible point-of-interest types — types that render regardless of the
current filter state.

**R11 (observed).** A separate shipped taxonomy MUST group categories into
coarse buckets for visited places, with ten buckets: services, dining, nature,
shopping, transit, travel, offices, community, health, and an explicit
unsupported bucket.

**R12 (derived).** An explicit *unsupported* bucket MUST be read as a closed
classification: every category resolves to a bucket, and the absence of a
mapping is itself a mapping, rather than a null that each caller handles
differently.

### 3.3 Autocomplete

**R13 (observed).** Autocomplete requests MUST be parameterised by a named
profile selecting which entry kinds are eligible. Profiles observed:

| Profile | Admits |
|---|---|
| All entries | Everything |
| All entries with browse | Everything, plus browse-style entries |
| Full entries only | Only complete entries, no query suggestions |
| Address only | Addresses |
| Point-of-interest address only | Addresses of places |
| Localities and landmarks | Cities, regions, landmarks |
| Collections only | Curated collections |
| Venue search | Within a venue |
| Brand profile search | A brand's own places |
| Offline region search | Restricted to downloaded data |
| Siri search | The assistant's query path |

**R14 (observed).** Requests MUST additionally carry an origination type stating
why the user is typing: a default, route planning, search along a route, or
adding a favourite.

**R15 (derived).** Origination and profile being separate dimensions MUST be
read as the server ranking differently for the same profile depending on intent
— typing a destination mid-route is not the same query as typing one into
search.

**R16 (observed).** Results MUST be able to be entries of several kinds,
including the user's current location, a frequently visited location, a recent
location, a marked location, and navigation origin or destination entries.

**R17 (derived).** Local entries (current, recent, frequent, marked) and server
entries MUST be merged into one result list, because the entry model
distinguishes a client-originated entry from a server-originated one over a
common base.

**R18 (observed).** Results MUST carry presentation instructions from the
server: a cell type — default, two-line, prominent query, prominent result, or
prominent result two-line — and a highlight type for matched text.

**R19 (derived).** The server therefore MUST control result prominence. "Put
this result at the top and make it big" is a server decision the client renders,
not a client heuristic.

**R20 (observed).** Results MUST be groupable into sections.

**R21 (observed).** Offline autocomplete MUST be a distinct state the client
knows about, not a failure mode.

### 3.4 Result refinement

**R22 (observed).** A result set MUST be able to carry refinements of several
structural kinds: a multi-select with elements, a toggle, a sort with elements,
a time refinement, an open-now option, and a section grouping them.

**R23 (observed).** Multi-select refinement criteria observed in the shipped
vocabulary include: cuisines, price, chains, amenities, all types, electric
vehicle charging network, charging speed, hike length, hike elevation gain, hike
type, and third-party accolades from three named guides.

**R24 (observed).** Sort criteria MUST include distance, rating and relevance.

**R25 (derived).** Because refinement criteria are an open server-driven
vocabulary rather than a client enum with a fixed set, a new filter dimension —
charging speed, say — can appear without a client release, provided it fits one
of the structural kinds in R22.

**R26 (derived).** This is the same pattern as R18: the client ships *shapes*,
the server ships *content*. It recurs throughout this stack.

### 3.5 The place card

**R27 (observed).** A place card's composition MUST be described by a
server-supplied layout: a summary layout with metadata, built from layout units,
lines and strings, paired with result-layout templates.

**R28 (observed).** The layout MUST be revisioned, and MUST support a
dynamic-context server override.

**R29 (observed).** Individual fields MUST be able to declare whether they can
appear in a place summary.

**R30 (derived).** Taken together, R27–R29 mean the place card is assembled from
a server-authored template against server-supplied fields, with the client
providing rendering primitives. The arrangement of a place card is not in the
client.

**R31 (observed).** A debug layout identifier MUST be carried, allowing a
specific layout to be identified in a bug report.

**R32 (observed).** Place requests MUST support vendor-specific refinement
parameters, and a result MUST be able to signal that it needs refinement rather
than returning an answer.

### 3.6 Lookup paths

**R33 (observed).** Distinct request types MUST exist, each with its own throttle
budget, for: search; forward geocoding; reverse geocoding; batch reverse
geocoding; spatial lookup; batch spatial event lookup; place lookup by
identifier; and place refinement (`01#R24`).

**R34 (observed).** Batch limits MUST be configurable separately for parameters
and results, for both place and event spatial lookup.

**R35 (derived).** Separate parameter and result caps MUST be read as protecting
against two different failure modes: a request too large to process, and a
response too large to return.

## 4 Algorithms

### 4.1 Serving a keystroke

```
on each keystroke, debounced:
    profile     <- the profile for this field (see R13)
    origination <- why this field is being typed into (see R14)

    local  <- entries from recents, frequents, marked locations,
              favourites, and the current location, filtered by profile
    if offline:
        local <- local, plus entries from downloaded regions only
        mark the result set offline
        return local

    remote <- autocomplete request(query, profile, origination, context)
              # subject to the global autocomplete throttle (01#R24)

    merge local and remote over the common entry base
    apply server-supplied section grouping
    render each entry with its server-supplied cell type and highlight type
```

### 4.2 Assembling a place card

```
given a place and a layout revision:
    layout <- the server-supplied summary layout for this place
    if a dynamic-context override applies:
        layout <- the override

    for each layout unit in layout:
        for each line in the unit:
            for each string slot in the line:
                field <- the place field named by the slot
                if field is absent, or declares it cannot appear in a summary:
                    skip the slot
                else:
                    render it
        if the unit produced nothing:
            omit the unit
```

The fallback behaviour when a layout references a field the client does not
understand is not established.

## 5 Constants

| Constant | Value |
|---|---|
| Named point-of-interest categories | 87 |
| Visited-place taxonomy buckets | 10 (including an explicit unsupported bucket) |
| Autocomplete parameter profiles | 11 observed |
| Autocomplete origination types | 4 observed |
| Result cell types | 5 observed |
| Refinement structural kinds | 6 (multi-select, toggle, sort, time, open options, section) |
| Sort criteria | distance, rating, relevance |

## 6 Rationale

Everything in this file is one idea applied repeatedly: the client ships
structure, the server ships content. Cell types, refinement criteria, place card
layouts and point-of-interest categories are all cases where the client knows
the *kinds* of thing that can appear and the server decides which ones do.

The payoff is that a new cuisine filter, a new accolade partner, a new place
card arrangement or a new point-of-interest type is a server change. The cost is
that the client is hard to reason about in isolation — you cannot read the
binary and know what a place card looks like — and that every server-driven
vocabulary needs a client fallback for values it does not recognise. The debug
layout identifier in R31 exists because of exactly this cost.

The separation of autocomplete from search is worth noting on its own.
Autocomplete runs per keystroke, so it gets its own global throttle, its own
restricted profiles, and an offline mode. Treating it as "search with a shorter
query" would make every one of those a special case.

## 7 Design takeaways

**03#T1.** Ship shapes, not content. Define the structural kinds the UI can
render and let the server choose instances. The release cadence of your
vocabulary stops being the release cadence of your app.

**03#T2.** When you do that, ship a debug identifier alongside. Server-driven
layout is unreviewable in the binary, so the only way to discuss a specific
rendering is to name it.

**03#T3.** Keep a stable public category vocabulary over a finer private type
space, mapped one-to-many. The public names stay stable for years while the
underlying taxonomy churns.

**03#T4.** Make your classification total. An explicit "unsupported" bucket is
one branch; a null is a branch in every caller.

**03#T5.** Separate "what kind of query" from "why is the user asking". The same
query text from route planning and from search deserves different answers, and
you cannot recover intent from the text.

**03#T6.** Keep attribute provenance in the model. Merging a user's correction,
their contact card and the server's answer into one address field destroys
information you will need.

**03#T7.** Give the typeahead path its own everything — its own service, its own
rate budget, its own result kinds, its own offline state. It has different
latency, volume and failure characteristics from search.

**03#T8.** Cap batch requests on both input and output. They fail differently.

## 8 Uncertainties

- The numeric point-of-interest type space is only visible through the shipped
  mapping; its full extent and encoding are unknown.
- How the client behaves when a server-driven vocabulary returns a value it does
  not recognise is not established, for cell types, refinement criteria or
  layout fields.
- The relationship between the two shipped resources — the category mapping and
  the visited-places taxonomy — is assumed rather than traced.
- Ranking and merge order between local and server autocomplete entries is
  unknown; 4.1 asserts that a merge happens, not how it is ordered.
- Whether place card layouts are cached, and keyed on what, was not determined.
- The place identifier's structure and stability guarantees are not established.

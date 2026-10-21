# 08 — Entry points and integration

## 1 Purpose & scope

Every way something outside Maps can ask Maps to show, find or do something.
Covers the URL grammar, universal links, custom schemes, App Intents, document
types, and the prediction and donation path.

Not covered: the public MapKit API, which Apple documents.

## 2 Concepts

**The URL grammar** is one query-item vocabulary shared across custom schemes
and web links. Everything resolves into it.

**A universal link** is an HTTPS URL on a Maps-owned host that opens the app.

**An App Intent** is a structured, typed action the system or the assistant can
invoke, with entities and enumerations rather than a URL.

**A donation** is the app telling the system about something the user did, so
the system can predict and suggest later.

## 3 Requirements

### 3.1 Schemes and hosts

**R01 (observed).** The app MUST register seven URL schemes. Four are public:
a maps scheme, a map scheme, a map-item scheme, and a map-item-handles scheme.
Three are declared private: an account-authentication scheme, a bulletin scheme,
and a punch-in-hint scheme.

**R02 (derived).** The private schemes MUST be read as internal navigation
between system components rather than a public interface — the bulletin scheme
is how a submission notification opens the app at the right place (`06#R26`).

**R03 (observed).** A navigation scheme MUST additionally be recognised,
separate from the registered schemes.

**R04 (observed).** Web entry MUST be supported on a primary host, a China
host, two short-form hosts, and a URL-shortener host, plus separate hosts for
collections and guides.

**R05 (observed).** URL shortening MUST be a throttled service request type in
its own right (`01#R24`), with the tightest short-window budget in the global
scope.

### 3.2 The path vocabulary

**R06 (observed).** Paths MUST select the surface to open:

| Path | Opens |
|---|---|
| `/place` | A place |
| `/search` | A search |
| `/directions` | A route |
| `/guides` | A curated guide |
| `/look-around` | Ground-level imagery |
| `/frame` | A map framed on a region |
| `/car/destinations` | Vehicle destinations |
| `/biz` | A business surface |
| `/report-a-problem` | The correction flow (`06`) |
| `/all` | An aggregate surface |

### 3.3 The query-item vocabulary

**R07 (observed).** Query items MUST cover the following concerns. Names are
given because they are the interface.

**Query and framing**

`q` (query), `near`, `hnear` (human-readable near), `ll` (latitude/longitude),
`sll` (search latitude/longitude), `spn` (span), `sspn` (search span), `z`
(zoom), `t` (map type), `center`, `span`, `coordinate`, `map`, `lat`, `lon`,
`cd`.

**Directions**

`saddr` (source address), `daddr` (destination address), `dirflg` (directions
flag), `destination`, `destination-place-id`, `source-place-id`, `waypoint`,
`waypoint-place-id`, `avoid`, `transit-preferences`, `mode`.

**Place identity**

`placeid`, `place-id`, `auid`, `cid`, `address`.

**Presentation and camera**

`presentation`, `cam`, `trackingmode`, `showfavorites`, `lineid`.

**Provenance and attribution**

`lsp`, `cp`, `cpid`, `_provider`, `ug`, `pg`, `pp`, `user`, `curated`,
`_explore`, `_city`.

**Internal and extension parameters**

`_ext`, `_extc`, `_col`, `_colc`, `_ei`, `_eic`, `_mvs`, `_mvsc`, `_mp`,
`user_session_entity`, `tester`.

**Specific surfaces**

`parked-car`, `reported-incident-type`.

**R08 (observed).** Several parameters MUST appear in pairs whose second member
ends in `c`. These pair a value with a companion, consistently across five
different parameter families.

**R09 (inferred).** The companion is most plausibly a checksum, signature or
context token validating the value it accompanies. This was not confirmed.

**R10 (observed).** Contact-sourced addresses MUST be expressible directly, with
parameters for both the legacy address-book person and address identifiers and
the modern contacts framework person and address identifiers.

**R11 (derived).** Carrying both generations MUST be read as compatibility
debt kept deliberately: links created years ago still resolve.

**R12 (observed).** Tracking mode MUST be expressible, with at least a
follow mode and a follow-with-heading mode.

**R13 (observed).** A tester parameter MUST exist in the vocabulary.

### 3.4 Document types

**R14 (observed).** The app MUST export two uniform type identifiers: a
directions request document, and a navigation trace file.

**R15 (observed).** The app MUST declare itself the handler for the trace file
type, as a viewer.

**R16 (derived).** A navigation trace being a first-class, double-clickable
document type MUST be read as a diagnostic workflow: a recorded drive can be
captured, sent, and replayed by opening it.

### 3.5 App Intents

**R17 (observed).** The app MUST ship App Intents metadata declaring five
actions, seven entities, six queries and nine enumerations. Two of the five
actions are test actions.

**R18 (observed).** The three production actions MUST be: showing places,
starting navigation, and updating navigation.

**R19 (observed).** Entities MUST be: a place, a current location, a navigation
session, operating hours, an operating time range, parking location data, and a
rating.

**R20 (observed).** Queries MUST address: the current location; a navigation
session; parking location data; and places, by descriptor, by descriptors, and
by string.

**R21 (derived).** Three distinct place queries MUST be read as three distinct
resolution strategies: a single structured descriptor, a batch of descriptors,
and free text. The assistant resolves differently depending on what it has.

**R22 (observed).** Enumerations MUST be:

| Enumeration | Cases |
|---|---|
| Transportation type | driving, walking, transit, cycling, any |
| Navigation preferences | avoid highways, avoid tolls, avoid busy roads, avoid hills, avoid stairs, disable bus, disable subway, disable train, disable ferry |
| Incident | accident, hazard, speed check, roadwork, road closure, traffic |
| Operating status | normal hours, special hours, temporarily closed, permanently closed |
| Price range | inexpensive, moderate, expensive, high |
| Rating descriptor | percentage, out of five |
| Place attribute | phone number, address, postal code, price range, rating, business hours, structured attribute |
| Place union value | place, current location |

**R23 (observed).** Enumeration cases MUST carry localised titles and
synonyms — an accident case carries an alternative phrasing, a hazard case
another.

**R24 (derived).** Shipping synonyms with the schema MUST be read as the
vocabulary being for speech recognition as much as for display: the assistant
must match what a user says, which is not always the canonical case name.

**R25 (observed).** Enumerations MUST declare the assistant-defined schema they
conform to, with a domain and a version.

**R26 (derived).** A versioned shared schema under a maps domain MUST be read as
a cross-application contract: any application implementing the maps domain
speaks the same incident and transport vocabulary, so the assistant can route an
intent to whichever one the user prefers.

**R27 (observed).** The navigation transport enumeration MUST include an *any*
case, which the directions service's own transport list (`04#R03`) does not.

**R28 (derived).** An *any* case MUST be read as intent-level deferral: the user
did not say how they want to travel, and the choice is made later — by the
transport mode prediction path (3.6) rather than by the intent.

**R29 (observed).** The transit preferences in the navigation preferences
enumeration MUST be expressible as disabling individual modes — bus, subway,
train, ferry — matching the transit options in the directions request.

### 3.6 Prediction and donation

**R30 (observed).** A dedicated daemon MUST own predicted destinations,
exposing four separate Mach services: predictions, donations, a signal pipeline,
and sources (`00#R11`).

**R31 (derived).** Four services MUST be read as four distinct roles: consumers
read predictions, producers donate, a pipeline carries signals, and sources
enumerate where predictions come from.

**R32 (observed).** The daemon MUST perform transport mode prediction, with
distinct input and output types.

**R33 (observed).** Prediction signals MUST be persisted in the sync store in
both per-trip and aggregate form (`05#R14`), so the model travels with the user.

**R34 (observed).** The daemon MUST observe the sync store directly, and MUST
hold a connection to the service framework.

**R35 (observed).** The navigation daemon MUST donate a parked car location both
to the system's live entity surface and to Spotlight (`04#R56`).

**R36 (observed).** The app MUST hold entitlements for the signal pipeline and
for the routine subsystem's locations of interest, map hints, predictions and
vehicle location, including deletion of a location of interest.

**R37 (derived).** An explicit deletion entitlement MUST be read as the user
being able to remove a significant location from the system's model, not merely
hide it.

**R38 (observed).** The app MUST declare support for Spotlight continuation and
a user activity type, and MUST declare a watch counterpart identifier
(`00#R17`), enabling handoff.

**R39 (observed).** The app MUST declare an application shortcut item for
opening a new window, and MUST query exactly one external scheme, belonging to a
weather provider.

## 4 Algorithms

### 4.1 Resolving an incoming URL

```
on open(url):
    if url.scheme is one of the private schemes:
        route internally (notification target, auth callback, hint)
        stop

    if url.scheme is http or https:
        if url.host is not a recognised Maps host:    reject
        if url.host is the shortener host:
            expand it first                            # throttled (01#R24)

    surface <- path (R06), defaulting by which parameters are present
    items   <- parse query items (R07)

    for each item with a companion parameter:
        if the companion is present and does not validate the value:
            drop the value                             # inferred

    resolve place references in order of precision:
        explicit place identifier
          > contact address reference
          > coordinate
          > free-text query with a framing hint

    apply framing: centre, span or zoom, map type, tracking mode
    present the surface
```

### 4.2 Starting navigation from an intent

```
intent: start navigation
    destination <- a place entity, or the current location entity
    transport   <- transportation type enumeration case

    if transport is "any":
        transport <- ask the prediction daemon for the predicted
                     transport mode, given the destination and context

    preferences <- navigation preferences cases, mapped onto
                   the per-mode options of a directions request (04#R05)

    build a directions request (04 §3.1) and validate it locally (04 §4.1)
    hand the resulting route to the navigation daemon
    return a navigation session entity, so a later update intent
      can address this session
```

Returning a session entity is what makes the update action addressable: the
assistant holds a handle to the running navigation rather than a global "the
current one".

## 5 Constants

| Constant | Value |
|---|---|
| Registered URL schemes | 7 (4 public, 3 private) |
| Recognised web hosts | 7 observed |
| Path surfaces | 10 observed |
| Query item names | ~60 observed |
| Value/companion parameter families | 5 |
| Exported document types | 2 |
| App Intents actions | 5 (3 production, 2 test) |
| App Intents entities | 7 |
| App Intents queries | 6 |
| App Intents enumerations | 9 |
| Prediction daemon services | 4 |

## 6 Rationale

One vocabulary behind every door is the whole design. A custom scheme, a web
link, a shared link, a notification tap and an assistant request all converge on
the same query items, so a feature gains an entry point by naming a parameter
rather than by implementing a route.

The cost is visible in the vocabulary itself: around sixty parameters, two
generations of contact identifiers, five value/companion pairs, and a handful of
underscore-prefixed internal parameters that are clearly not meant for anyone
outside. This is what a public URL grammar looks like after a decade of
compatibility.

App Intents are the modern alternative, and the contrast is instructive. The URL
grammar is stringly-typed, unversioned and permanently compatible. The intents
schema is typed, versioned, shared across a domain, and carries localised
synonyms for speech. One is a door anyone can walk through; the other is a
contract.

The *any* transport case is the small detail worth keeping. It is an explicit
representation of "the user did not say", carried through to a component whose
job is to decide. Most systems would default to driving at the parse layer and
lose the information that no choice was made.

## 7 Design takeaways

**08#T1.** Converge every entry point on one vocabulary. New surfaces then cost
a parameter, not a parser.

**08#T2.** Accept that a public URL grammar is permanent. Both generations of
contact identifier are still there because links outlive schemas.

**08#T3.** Pair a value with a companion token if the value can be forged. Doing
it consistently across every family is what makes it reviewable.

**08#T4.** Represent "not specified" explicitly and carry it to whoever can
decide. Defaulting at the parse layer destroys the information that there was no
choice.

**08#T5.** Ship synonyms with your intent vocabulary. The canonical case name is
rarely what a person says.

**08#T6.** Version your intent schema and share it across a domain. That is what
lets the assistant route the same request to a different application.

**08#T7.** Return a handle from a long-running intent. "Update the navigation"
needs to address a specific session, not the global current one.

**08#T8.** Make your diagnostic recording a document type. A trace you can
attach to a bug report and double-click is worth more than one that needs a tool.

**08#T9.** Separate donation, prediction, signals and sources into their own
interfaces. They have different callers, different trust levels and different
privacy stories.

**08#T10.** Let the user delete from the prediction model, not just hide. An
entitlement for deletion is a design position.

## 8 Uncertainties

- The value/companion pairing (R09) is inferred. Its construction is unknown.
- The meaning of individual provenance parameters is not established; they are
  grouped here by shape and naming, not by traced use.
- The map type and directions flag parameters' value spaces were not recovered.
- Several short literals observed near the tracking mode values could not be
  attributed to a parameter and are omitted rather than guessed at.
- Whether the China hosts carry a different parameter vocabulary was not
  determined.
- The prediction daemon's model, inputs and update cadence are not covered; only
  its interfaces and persisted signal shapes.
- The punch-in-hint scheme's purpose is inferred from its name alone.

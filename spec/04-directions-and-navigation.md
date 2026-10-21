# 04 — Directions and navigation

## 1 Purpose & scope

How a route is requested, what comes back, and how turn-by-turn guidance is
produced from it. Covers the directions request, the composed route structure,
the guidance event model, server-authored formatted strings, route matching, and
the navigation daemon.

Not covered: routing itself, which happens on the server.

## 2 Concepts

**A directions request** names waypoints and the attributes the client wants
back. It does not describe a route.

**A composed route** is the response: a fully structured object tree the client
renders without re-deriving anything. "Composed" is the shipped vocabulary and
is the key idea in this file.

**A guidance event** is something that should be said or shown at a point along
the route. Events are attached to the route, not computed from it.

**A formatted string** is a server-authored template plus typed arguments. The
client applies locale, units and number formatting.

**Route matching** is deciding where on the route the user actually is.

## 3 Requirements

### 3.1 The request

**R01 (observed).** A directions request MUST carry at least two waypoints. This
is validated client-side before the request is sent.

**R02 (observed).** A request MUST carry route attributes, and MUST be rejected
locally if they are missing.

**R03 (observed).** A request MUST carry a transport type. Transport types
observed: driving, walking, cycling, transit, and ferry.

**R04 (observed).** A transport mode MUST be set unless a reroute context is
provided. A reroute carries its mode implicitly from the route it is replacing.

**R05 (observed).** Per-mode options MUST be modelled separately: automobile
options, cycling options, walking options, transit options, and fare options.

**R06 (observed).** Cycling and walking MUST additionally carry persisted user
preferences, and cycling MUST carry vehicle specifications.

**R07 (derived).** Cycling vehicle specifications being distinct from cycling
preferences MUST be read as the route depending on the bicycle — an e-bike's
range and a cargo bike's gradient tolerance are properties of the vehicle, not
of the rider's taste.

**R08 (observed).** Waypoints MUST be able to carry an electric-vehicle stop,
and routes MUST be able to carry charging station information and charge
location details.

**R09 (observed).** Requests MUST be able to express avoidance, and a distinct
error exists for an avoidance that cannot be satisfied for the chosen vehicle
type.

### 3.2 Request failure

**R10 (observed).** Directions failures MUST be enumerated. Observed failure
causes:

| Failure | Meaning |
|---|---|
| No pedestrian roads | No walkable network between the waypoints |
| Maximum distance exceeded | The request is too long to route |
| Anchor limit exceeded | Too many fixed points constrain the route |
| Electric vehicle request invalid | The EV parameters do not form a valid request |
| Offline data insufficient | The downloaded data cannot answer this |
| Vehicle type avoidance failed | The avoidance cannot be honoured for this vehicle |
| Transition from driving disabled | A mode change out of driving is not permitted |
| Path decoding failed | The returned geometry could not be decoded |

**R11 (observed).** Failures MUST be able to carry a problem detail identifying
the waypoint index at fault.

**R12 (derived).** A per-waypoint failure MUST be read as a requirement to tell
the user *which* stop is the problem on a multi-stop route, not merely that the
route failed.

**R13 (derived).** "Offline data insufficient" being a first-class failure MUST
be read as offline routing running locally against downloaded data rather than
failing at the network layer. The client knows the difference between "no
network" and "the data you have does not cover this".

### 3.3 The composed route

**R14 (observed).** A route response MUST be a structured tree. Observed levels:
the route; legs; segments; steps; and within steps, lane information with
per-lane direction information.

**R15 (observed).** Walking and transit MUST have their own segment and step
types, and transit MUST additionally model trip segments and trip steps
distinctly from route steps.

**R16 (derived).** Mode-specific step types MUST be read as a refusal to force
one step shape to carry a transit boarding, a walking connection and a motorway
merge. The cost is more types; the benefit is that no step has fields that are
meaningless for its mode.

**R17 (observed).** A route MUST carry anchor points as an ordered list, and
MUST carry an elevation profile.

**R18 (observed).** Routes MUST be persistable, with distinct persistent-data
representations for the route geometry and for the route request.

**R19 (derived).** Persisting the request alongside the route MUST be read as
supporting resumption: a stored route handle can be re-requested rather than
replayed, which matters when traffic has changed.

**R20 (observed).** A resume-route handle MUST exist as a first-class storable
object.

### 3.4 Guidance events

**R21 (observed).** Guidance MUST be carried as events attached to the route,
each with a distance from the start of the route and an associated step index.

**R22 (observed).** Events MUST be divided into positional events and
conditional events.

**R23 (derived).** Positional events fire at a place; conditional events fire
when something is true. "In 500 metres, turn left" is positional; "traffic ahead
is heavier than expected" is conditional. Keeping them in separate lists lets
the client evaluate conditions only for the small set that has them.

**R24 (observed).** Events MUST carry a reference coordinate used for computing
distance strings, distinct from the event's own position.

**R25 (derived).** A separate reference coordinate MUST be read as the distance
spoken to the user being measured to a different point than the event's anchor —
you are told the distance to the junction, while the instruction is anchored
where it must be *said*.

**R26 (observed).** Events MUST carry spoken information distinctly from
displayed strings, and MUST support secondary strings.

**R27 (observed).** Events MUST declare whether they support a maneuver and
whether they support a maneuver chain.

**R28 (derived).** Maneuver chains MUST be read as consecutive maneuvers
collapsed into one instruction — "turn left, then immediately right" — which the
server decides and flags rather than the client inferring from step proximity.

**R29 (observed).** Events MUST exist for getting on route and returning to
route, and for arrival at a charging station.

**R30 (observed).** The maneuver vocabulary MUST be fine-grained. Observed
distinctions include: arrival at destination, and separately arrival on the left
and on the right; end of navigation distinct from end of directions; starting a
route with a U-turn; resuming a route with a U-turn; U-turn when possible;
U-turn at a roundabout; roundabout exits enumerated individually at least to the
nineteenth; motorway off-ramps left and right; changing motorway left and right;
waypoint stops left and right; and a plain continue.

**R31 (derived).** Individually enumerated roundabout exits to the nineteenth
MUST be read as the vocabulary being a closed enum rather than a parameterised
one. This is a deliberate trade: an enum is exhaustively translatable and
testable, a parameter is not.

**R32 (observed).** Events MUST carry an enumerated direction, a driving side,
and a junction type.

**R33 (observed).** Arrival parameters MUST carry an on-route arrival range and
off-route arrival bounds as separate quantities.

**R34 (derived).** Two arrival geometries MUST be read as the client needing to
decide arrival differently depending on whether the user is still on the route.

### 3.5 Formatted strings

**R35 (observed).** Displayed and spoken strings MUST arrive as a format string
with typed arguments rather than as finished text.

**R36 (observed).** Argument types MUST include: a number with a value; a
maneuver with a maneuver type; a countdown with countdown data and per-countdown
format strings; a price with a currency and an amount; a URL; and an integer
value.

**R37 (observed).** Number formatting MUST be controllable per argument by
minimum and maximum fraction digits, and MUST carry a flag permitting or
forbidding unit conversion.

**R38 (derived).** A per-argument "allow unit conversion" flag MUST be read as
the server distinguishing a quantity that should be shown in the user's units
from one that must not be converted — a speed limit sign reads in the posted
unit regardless of the user's preference.

**R39 (observed).** Duration formats MUST distinguish short units from medium
units.

**R40 (observed).** Every format argument MUST be able to carry a fallback
string, and the client treats a missing fallback as an error.

**R41 (derived).** A required fallback MUST be read as a protocol-level
guarantee that the client can always render something, even for an argument type
it does not understand. This is the fallback mechanism that `03` notes is
missing from the other server-driven vocabularies.

**R42 (observed).** Format strings MUST support an inline markup form delimiting
named spans, so parts of a string can be styled or substituted individually.

**R43 (observed).** The unit vocabulary MUST extend beyond the obvious:
kilometres per hour, Scandinavian miles, and astronomical units are all present.

### 3.6 Route matching

**R44 (observed).** Distinct road matching and route matching MUST both exist.

**R45 (derived).** Road matching places the user on the road network; route
matching places them on the chosen route. They are different questions — a user
driving parallel to their route is matched to a road but is off-route.

**R46 (observed).** Road geometry MUST carry direction validity: valid in both
directions, positive line direction, and negative line direction.

**R47 (observed).** Tile-local road graphs MUST carry connectivity across tile
boundaries explicitly: connected feature indexes within the same tile, and
adjoining-tile junction information.

**R48 (derived).** Explicit cross-tile junction information MUST be read as the
road graph being traversable without loading neighbouring tiles first — the
boundary carries enough to continue, which is what makes offline and
low-bandwidth routing tractable.

**R49 (observed).** Roads MUST carry an internal name distinct from any
displayed name.

### 3.7 The navigation daemon

**R50 (observed).** An active navigation session MUST live in a dedicated daemon
configured to be kept alive (`00#R12`), separate from the app.

**R51 (observed).** The daemon MUST expose a recent-locations service in
addition to its main service.

**R52 (observed).** Navigation state MUST be shareable, with a shared
navigation state object and a listener interface.

**R53 (observed).** The daemon MUST maintain a route hypothesis, separate from
an active route.

**R54 (derived).** A route hypothesis MUST be read as predicted or speculative
routing — a guess at where the user is going, maintained whether or not
navigation is running (see `08` on predicted destinations).

**R55 (observed).** The daemon MUST support per-client event monitoring, with
configuration keys bounding both monitored events and events per client.

**R56 (observed).** The daemon MUST resolve vehicle events and donate a parked
car location, both to the system's live entity surface and to Spotlight.

**R57 (observed).** Route preloading MUST exist as an explicit strategy, with
separate strategies for navigation routes and transit routes.

**R58 (observed).** Updatable ETAs MUST be a distinct long-running operation,
taking a request, traits and an audit token, with separate callbacks for the
request being sent, completion, and error.

**R59 (derived).** An audit token on the ETA call MUST be read as the daemon
attributing the request to the calling process for privacy accounting, not
merely for routing the reply.

**R60 (observed).** Transit MUST have its own update path: a route update
request and response, a route updater, and a separate vehicle position updater.

### 3.8 Offline and mode transitions

**R61 (observed).** Alerts MUST exist for an offline-to-online transition
producing a new route, and for rerouting while offline, separately for electric
vehicles, e-bikes and licence-plate-restricted routing.

**R62 (derived).** A distinct alert for "you are online again and there is now a
better route" MUST be read as offline routing producing a usable but
acknowledged-as-inferior result, which the client upgrades when it can.

## 4 Algorithms

### 4.1 Validating a request before sending

```
validate(request):
    if count(waypoints) < 2:              reject: too few waypoints
    if route_attributes is missing:       reject: missing attributes
    if transport_type not in known set:   reject: invalid transport type
    if transport_mode unset and reroute_context is absent:
                                          reject: mode required
    # per-mode options and user preferences are attached here
```

Every one of these is a local rejection. A malformed request never reaches the
network and never spends throttle budget.

### 4.2 Rendering one guidance event

```
given event, locale, unit preference:
    template  <- event.spoken or event.displayed format string
    arguments <- event.format arguments

    for argument in arguments:
        if the client does not understand argument.type:
            if argument.fallback is absent:  error
            emit argument.fallback
            continue

        switch argument.type:
            number:    format value with [min, max] fraction digits
                       if allow_unit_conversion: convert to the user's units
            maneuver:  look up the phrase for maneuver type,
                       respecting driving side and enumerated direction
            countdown: select the countdown format string for the
                       remaining distance band, measured to
                       event.reference_coordinate
            price:     format amount in currency
            url:       validate, then emit as a link span

    substitute into template, honouring named spans for styling
```

### 4.3 Deciding the user is off-route

```
continuously, from location updates:
    road_match  <- match the location onto the road network
    route_match <- match the location onto the active route

    if route_match is confident:
        advance the active step index
        fire positional events whose distance-from-start is now reached
        evaluate conditional events
        continue

    if road_match is confident but route_match is not:
        the user is on a road, but not this route
        -> reroute, carrying a reroute context (so the mode is implicit)

    if neither is confident:
        hold; do not reroute on a single bad fix
```

The confidence thresholds and the hold duration are not visible in the static
evidence; the structure is inferred from the two matchers existing separately.

## 5 Constants

| Constant | Value |
|---|---|
| Minimum waypoints | 2 |
| Transport types | driving, walking, cycling, transit, ferry |
| Enumerated roundabout exits | at least 19 |
| Enumerated failure causes | 8 observed |
| Arrival geometries | on-route range, off-route bounds |
| Guidance event lists | positional, conditional |
| Duration unit styles | short, medium |

## 6 Rationale

The composed route is the central decision. The server returns a tree the client
walks, not a geometry the client interprets. Lane guidance, maneuver phrasing,
roundabout exit numbering, chained maneuvers and arrival side are all decided
where the road data lives. The client's job is rendering, timing and matching.

This is why the maneuver vocabulary is an enum rather than a parameterised
description. If the server says "take the third exit", the client must have a
phrase for it in every supported language, reviewed by a translator who saw the
specific case. A closed enum makes that set finite and testable. Nineteen
roundabout exits is the price of that guarantee, and it is a cheap price.

Formatted strings are the counterweight. Localised number formatting, unit
conversion and currency belong on the device, because they depend on settings
the server should not need to know. Splitting at "the server authors the
sentence, the client formats the quantities" puts each decision where the
information is — and the mandatory fallback means the split degrades safely.

Separating road matching from route matching is a small structural choice with a
large behavioural consequence: it is what lets the system distinguish "lost" from
"driving on the service road next to the motorway", which is the difference
between a helpful reroute and an infuriating one.

## 7 Design takeaways

**04#T1.** Return a composed answer, not raw material. If the client has to
re-derive lane guidance from geometry, every client derives it differently and
none of them matches what the data author intended.

**04#T2.** Keep the instruction vocabulary a closed enum. It is the only way to
guarantee every case has been translated and seen by a human.

**04#T3.** Split "author the sentence" from "format the quantities" and put the
second on the device. Locale, units and currency are device settings; a server
that formats them needs to know too much.

**04#T4.** Make the fallback mandatory in the protocol. An argument type the
client does not understand should still render, and the only reliable way to get
that is to refuse to encode one without a fallback.

**04#T5.** Give each mode its own step type. One universal step accumulates
fields that are meaningless for most of its instances.

**04#T6.** Separate positional triggers from conditional ones. Evaluating
conditions against everything on a long route is work you do not need to do.

**04#T7.** Measure the distance you *say* from a different point than the one
you anchor to. They are different questions and conflating them is why some
systems say "in 50 metres" too late.

**04#T8.** Carry cross-boundary connectivity in each tile. A graph that needs
its neighbours loaded before it can be traversed cannot work offline.

**04#T9.** Distinguish matching to the network from matching to the plan.
"On a road but not your road" is a state that deserves its own handling.

**04#T10.** Validate locally and reject before the network. Every error caught
in the request builder is a round trip, a rate-limit slot and a failure state
you never have to design.

**04#T11.** Put the session in a process that cannot be reclaimed, and let the
UI attach to it. Guidance that stops when a window closes is not guidance.

**04#T12.** Acknowledge a degraded answer and upgrade it. An offline route that
announces itself as provisional, and a later alert offering a better one, beats
silently serving the worse route.

## 8 Uncertainties

- The maneuver vocabulary is sampled, not enumerated. Roundabout exits are
  observed to at least nineteen; the true ceiling is unknown.
- Route matching (4.3) is a reconstruction. Thresholds, hysteresis and the
  reroute trigger are not visible.
- The relationship between the route hypothesis and predicted destinations
  (`08`) is asserted, not traced.
- What the conditional events actually condition on is unknown.
- The "search along route" abbreviation that appears in several offline alert
  names was not resolved and is not relied on here.
- Transit routing is substantially larger than its treatment here; the data
  model covers stations, halls, access points, lines, systems, incidents,
  artwork, shields, brands, payment methods and vehicle positions, none of which
  is specified.
- Whether elevation profiles are returned for all modes or only cycling and
  walking was not determined.

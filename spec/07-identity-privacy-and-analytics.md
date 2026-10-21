# 07 — Identity, privacy and analytics

## 1 Purpose & scope

The identifiers Maps uses, what it does to a location before sending it, and how
usage data is collected and uploaded. Covers the session identifier model,
coarse location, regional coordinate shifting, and the analytics pipeline.

Per [`../CLEANROOM.md`](../CLEANROOM.md), this file describes the *shape and
policy* of analytics collection. It does not enumerate event names.

Not covered: what the server does with any of it.

## 2 Concepts

**A session identifier** is a rotating value attached to requests so related
requests can be correlated for a bounded time without a durable identity.

**Coarse location** is a deliberately degraded position, produced when the user
has not granted precise location or when the request does not need it.

**Location shifting** is a regional coordinate transform, applied where the
local mapping datum differs from the global one.

**The analytics pipeline** is a daemon-resident collect-aggregate-upload path,
running on its own schedule (`00#R13`).

## 3 Requirements

### 3.1 The identifier model

**R01 (observed).** There MUST be several identifiers with different lifetimes,
not one. Distinct identifiers observed in the wire vocabulary:

| Identifier | Scope |
|---|---|
| Device-local session identifier | A session, local to this device |
| Initial device session identifier | The device's first session |
| Anonymous identifier | An anonymous subject |
| Anonymous user identifier | An anonymous user, distinct from the above |
| Anonymous session identifier | An anonymous session |
| Feature session identifiers | Per-feature, e.g. a table-booking session |

**R02 (observed).** A session identifier MUST be accompanied by its age in
seconds on the wire.

**R03 (derived).** Sending the *age* rather than a creation timestamp MUST be
read as deliberately avoiding a stable absolute value: an age is a relative
quantity that cannot be used to re-link sessions across a rotation boundary the
way a fixed creation time could.

**R04 (observed).** The wire vocabulary MUST carry whether an identifier has
rotated, and separately whether it had previously rotated.

**R05 (derived).** Two rotation flags MUST be read as distinguishing "this is
the first request after a rotation" from "this identifier has rotated at least
once in its history" — which lets the server tell a genuinely new device from
one whose identifier just turned over.

**R06 (observed).** A notification MUST be published when the short session
resets, so in-process consumers can discard derived state at the same boundary.

**R07 (derived).** Rotation therefore MUST be a system-wide event rather than a
per-caller decision. If one component kept correlating across the boundary, the
rotation would achieve nothing.

**R08 (observed).** An analytics identifier MUST be stored in the sync store
(`05#R10`) and therefore travels between the user's devices.

**R09 (derived).** A synced analytics identifier and a per-device session
identifier serving different purposes MUST be read as a deliberate layering:
cross-device aggregate analysis at one level, bounded per-device correlation at
another, with the account at neither.

**R10 (observed).** A request counter MUST exist as a modelled object, with the
app holding a dedicated entitlement for it.

**R11 (inferred).** The request counter is most plausibly a per-interval quota
or accounting mechanism complementing the throttle document (`01#R20`). Not
confirmed.

### 3.2 Coarse location

**R12 (observed).** Location precision MUST be classified into four states:
precise, coarse, not authorised, and unknown.

**R13 (observed).** The protocol MUST carry an explicit client capability
indicating the client can handle coarse location.

**R14 (derived).** A capability flag MUST be read as coarse location being a
negotiated behaviour: a server will not return coarse-location-shaped answers to
a client that cannot interpret them.

**R15 (observed).** Coarse locations MUST be classified by how they were
produced: snapped to a grid, snapped to data, or unknown.

**R16 (derived).** "Snapped to data" MUST be read as snapping to a meaningful
region — an administrative area or a known polygon — rather than an arbitrary
grid cell. A coarse-location polygon type exists in the vocabulary.

**R17 (observed).** Grid snapping MUST be governed by a configured zoom level,
which fixes the cell size.

**R18 (observed).** Grid cells MUST be merged in longitude above configured
latitude thresholds, with a separate, more extreme threshold.

**R19 (derived).** Two merge thresholds MUST be read as compensating for
convergence of the meridians: a fixed-zoom cell is far narrower in metres near
the poles than at the equator, so cells are merged once, then merged more
aggressively further north or south, keeping the *area* a coarse location
conceals roughly constant.

**R20 (observed).** A representative point MUST be chosen for a coarse cell,
and randomisation MUST be configurable in three ways: whether grid-snapped
locations are randomised at all; whether the representative point is always
randomised; and the distance over which randomisation happens.

**R21 (derived).** Randomising the representative point MUST be read as
defeating the obvious attack on grid snapping: without it, every coarse location
in a cell reports the identical point, so observing that exact point twice
proves the two observations came from the same cell, and the cell centre is
trivially recoverable.

**R22 (observed).** A prompt MUST exist to request precise location, and a
separate prompt presents coarse location options.

**R23 (observed).** An explicit signal MUST exist recording that a coarse
location was used.

### 3.3 Location shifting

**R24 (observed).** A location shifting subsystem MUST exist, described in the
configuration surface as polynomial.

**R25 (observed).** Shift functions MUST be fetched from a configured URL, be
region-scoped, carry a version, and be applicable within a configured radius.

**R26 (observed).** Shift functions MUST be cached in their own database,
governed by: a maximum cache age in seconds; a maximum cache count; a minimum
number to keep; and a persistence-enabled flag.

**R27 (derived).** A minimum-to-keep floor alongside a maximum count MUST be
read as guaranteeing the device retains some shift capability even under cache
pressure. Losing every shift function would make the map wrong, not merely slow.

**R28 (observed).** The cache MUST support explicit operations to flush, prune
and list it, and the subsystem MUST be able to be enabled or disabled.

**R29 (observed).** Two distinct service paths MUST exist for shifting, and the
shift must be applicable in both directions — a coordinate obtained locally must
be convertible for the server, and a coordinate from the server must be
convertible for display.

**R30 (observed).** An allowlist MUST exist permitting specified callers to skip
the location authorisation check when shifting.

**R31 (derived).** That allowlist MUST be read as shifting sometimes being
needed for a coordinate the caller already holds — transforming a coordinate the
user typed is not a location access, and requiring authorisation for it would be
both wrong and a bad user experience.

**R32 (observed).** The region in which shifting applies MUST itself be
configuration, not compiled in.

### 3.4 The analytics pipeline

**R33 (observed).** Analytics MUST be collected into a dedicated daemon with its
own database, storage layer and cache path.

**R34 (observed).** The daemon MUST start at load and run on a repeating
interval (`00#R13`), independent of whether Maps is running.

**R35 (observed).** Submission from a client MUST be able to be lazy — an
interface exists for deferring the construction of an event's payload.

**R36 (derived).** Lazy construction MUST be read as avoiding the cost of
building an event that sampling or configuration will discard. The decision to
collect is made before the payload is built.

**R37 (observed).** The pipeline MUST aggregate before uploading, with distinct
aggregators for counts and for network events, and a daily counts queue.

**R38 (observed).** Daily settings MUST be queued alongside daily counts.

**R39 (derived).** Recording settings state daily MUST be read as the pipeline
needing the configuration context in which counts were produced — a count of a
feature's use is uninterpretable without knowing whether the feature was enabled.

**R40 (observed).** Upload MUST be decomposed into at least five collaborators:
a configuration provider, a file writer, a time provider, a hold-down, and the
uploader itself.

**R41 (derived).** A *hold-down* distinct from a time provider and a
configuration provider MUST be read as suppression of bursts being a separate
concern from scheduling. Scheduling says when upload is due; hold-down says when
it is nonetheless not allowed.

**R42 (derived).** Injecting a time provider MUST be read as the pipeline being
testable against a simulated clock, which for a system whose entire behaviour is
intervals and expiries is the only way to test it.

**R43 (observed).** Stored analytics MUST expire, with an explicit operation to
delete all expired records.

**R44 (observed).** The pipeline MUST expose separate XPC interfaces for
clients, for the daemon, and for a debug panel.

**R45 (observed).** A fuzzing component MUST exist within the analytics
namespace.

**R46 (inferred).** That component most plausibly perturbs values before upload
— coordinates, counts, or both. Its mechanism was not determined and no privacy
property should be inferred from its existence.

**R47 (observed).** A portal component MUST exist within the analytics
namespace; its role was not determined.

**R48 (observed).** Log messages MUST be queued through the same element queue
as counts.

**R49 (observed).** A dedicated analytics entitlement MUST be held by the app
to submit at all.

## 4 Algorithms

### 4.1 Producing a coarse location

```
coarsen(precise_location):
    cell <- the grid cell containing precise_location
            at the configured coarse grid zoom level

    if |cell.latitude| > extreme latitude merge threshold:
        merge cell with its longitudinal neighbours, aggressively
    else if |cell.latitude| > latitude merge threshold:
        merge cell with its longitudinal neighbours

    if a known data polygon better describes this area:
        point <- a representative point of that polygon
        type  <- snapped to data
    else:
        point <- a representative point of the (possibly merged) cell
        type  <- snapped to grid

    if randomise grid-snapped locations is enabled
       or always randomise representative point is enabled:
        point <- displace point by up to the configured
                 representative point randomisation distance

    return point, type
```

The merge step is what keeps the concealed *area* roughly constant with
latitude. Without it, a coarse location in northern Scandinavia would conceal a
fraction of what the same grid conceals at the equator.

### 4.2 Shifting a coordinate

```
shift(coordinate, direction):
    if location shifting is disabled:            return coordinate
    if coordinate is outside the shift-enabled region:
                                                 return coordinate

    function <- cached shift function whose region covers coordinate
                and whose radius admits it

    if function is absent:
        if the caller is on the authorisation-check allowlist:
            fetch without an authorisation check
        else:
            fetch, subject to location authorisation
        store it, honouring the maximum cache count
        and the minimum-to-keep floor

    return apply(function, coordinate, direction)
```

### 4.3 From event to upload

```
a client wants to record something:
    if configuration or sampling says this is not collected:
        return without building the payload        # lazy construction

    enqueue a queue element

the daemon, continuously:
    counts         <- aggregate count elements
    network events <- aggregate network event elements
    daily          <- counts for the day, plus the settings state
                      in which they were produced

the daemon, on its repeating interval:
    if hold-down says not now:
        stop
    if the upload configuration provider says not now:
        stop

    write an upload file from the aggregates
    upload it
    on success, drop what was uploaded

separately, on its own schedule:
    delete all expired stored analytics
```

## 5 Constants

| Constant | Value |
|---|---|
| Location precision states | precise, coarse, not authorised, unknown |
| Coarse location types | snapped to grid, snapped to data, unknown |
| Latitude merge thresholds | two, standard and extreme |
| Randomisation controls | 3 (grid-snapped, always-representative, distance) |
| Shift cache bounds | max age (s), max count, minimum to keep |
| Shift cache operations | flush, prune, list |
| Upload collaborators | config provider, file writer, time provider, hold-down, uploader |
| Distinct identifier kinds | 6 observed |

## 6 Rationale

The identifier model is the clearest statement of intent in this stack. There is
no single device identifier in the Maps request path. Instead there are several
identifiers with different scopes and lifetimes, a rotation that is announced
system-wide so every component resets together, and an age rather than a
timestamp on the wire. Each of those individually is a small thing; together
they bound how long any two requests can be linked.

Coarse location is the most completely specifiable privacy mechanism here, and
the configuration surface shows the attacks it was designed against. Grid
snapping alone leaks: every location in a cell reports the same point, so the
cell is recoverable and repeat visits are detectable. Randomising the
representative point closes that. A fixed grid alone also leaks differentially
by latitude, concealing far less near the poles; the two merge thresholds close
that. Neither fix is obvious from the outside, and both are configuration rather
than constants, which means they were tuned.

Location shifting is unusual in being a *correctness* mechanism that looks like
a privacy one. Where the local mapping datum differs from the global one, an
unshifted coordinate is simply in the wrong place. The design consequence worth
noting is the minimum-to-keep floor: a cache that can be fully evicted would
leave a device unable to put itself on its own map.

The analytics pipeline's shape — lazy construction, aggregate-before-upload,
daily settings captured alongside daily counts, and a hold-down distinct from
scheduling — describes a system optimised for not collecting, not sending, and
being interpretable later. The injected time provider is the tell that it is
meant to be tested.

## 7 Design takeaways

**07#T1.** Use several identifiers with different lifetimes rather than one.
Each answers a different question, and none of them has to answer all of them.

**07#T2.** Send an age, not a timestamp. A creation time is a stable value that
survives rotation; an age is not.

**07#T3.** Make rotation a broadcast event. A rotation that one component
ignores is not a rotation.

**07#T4.** Randomise the representative point of any spatial generalisation. A
deterministic representative turns a coarse location back into a precise one
under repetition.

**07#T5.** Adjust spatial generalisation for latitude. A fixed grid conceals
wildly different areas at different latitudes, so the privacy guarantee you
describe is not the one you ship.

**07#T6.** Negotiate degraded modes with a capability flag. A client that cannot
interpret a coarse answer should not receive one.

**07#T7.** Give a cache whose absence breaks correctness a minimum-to-keep
floor, not just a maximum.

**07#T8.** Build analytics payloads lazily. The decision not to collect should
cost nothing.

**07#T9.** Record the configuration alongside the counts. Usage numbers without
the settings that produced them cannot be interpreted a quarter later.

**07#T10.** Separate hold-down from scheduling. "It is due" and "it is allowed"
are different predicates, and merging them makes backpressure impossible to
reason about.

**07#T11.** Inject the clock. A system that is entirely intervals and expiries is
untestable against the real one.

## 8 Uncertainties

- The fuzzing component's mechanism (R46) is unknown. Nothing in this file
  should be read as a claim about differential privacy or any formal guarantee.
- The analytics portal component's role is unknown.
- The request counter's purpose (R11) is inferred.
- Rotation intervals are not visible; only that rotation happens, is flagged and
  is broadcast.
- The shipped coarse grid zoom level and the latitude merge thresholds were not
  read; only that they are configuration keys.
- The two shifting service paths are distinguished only by name; which is which
  was not determined, and the directionality in 4.2 is inferred from the pair
  existing.
- The relationship between the synced analytics identifier and the anonymous
  contribution credential (`06`) is not traced.
- Whether the analytics pipeline collects location at all, and at what
  precision, is not established here.

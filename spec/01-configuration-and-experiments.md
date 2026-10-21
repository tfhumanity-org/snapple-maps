# 01 — Configuration, experiments and request throttling

## 1 Purpose & scope

How the client decides what to talk to, what it is allowed to do, and which
behaviours are switched on. Covers the layered configuration system, the
manifest bootstrap, experiment assignment, environment selection, per-country
configuration, and the client-side request throttler.

Not covered: what the server decides, or the contents of any live manifest.

## 2 Concepts

**A default** is a named configuration value. The system carries on the order of
440 of them in the geo-services namespace alone. Keys are stable across builds;
values are not.

**A layer** is a source of defaults. Five of them stack, and the stack is named
in the shipped binary rather than being an implementation detail — any value can
be attributed to the layer that produced it.

**The manifest** is a server document, fetched from a hard-coded URL, that
describes where everything else lives and which resources are current.

**An environment** selects a whole set of endpoints at once: production,
staging, QA, development, or an explicitly configured custom one.

**A throttle bucket** is a request-count allowance over a window, keyed by
calling application and request type.

## 3 Requirements

### 3.1 The configuration layers

**R01 (observed).** Configuration MUST be resolved from five named sources. In
increasing order of authority:

1. **Default (baked-in)** — the value compiled into the shipping binary.
2. **Resource manifest** — values carried by the manifest document.
3. **Network defaults** — values fetched from the defaults configuration
   service.
4. **Remote configuration** — remotely administered overrides.
5. **Custom environment** — an explicitly configured environment, which
   replaces endpoints wholesale.

**R02 (derived).** Because the layer identities are present in the binary as
distinct named sources rather than merged on read, the system MUST be able to
report which layer supplied any given value. A debug configuration surface
exists for exactly this.

**R03 (observed).** A sanitised-version marker MUST exist for the defaults
store, allowing a client to detect that a stored defaults set predates a schema
change and discard it.

**R04 (observed).** Configuration changes MUST be observable: a listener
interface exists, and configuration failures carry their own error domain.

**R05 (observed).** The application MUST hold an entitlement granting
configuration access across all domains, plus separate entitlements to fetch the
manifest, to read and to set experiments, and to set any default. These are
distinct permissions; reading configuration and overriding it are not the same
privilege.

### 3.2 Bootstrap

**R06 (observed).** The client MUST carry exactly one hard-coded dynamic
configuration URL, on a dedicated host, whose path ends in a device-query
template placeholder substituted at request time.

**R07 (observed).** The client MUST additionally carry a defaults configuration
endpoint in two variants — a standard one and a *carry* variant on a parallel
host — and a country-code endpoint on a third host.

**R08 (derived).** The repeated *carry* host naming across configuration and two
location-service endpoints MUST be read as a second deployment ring addressed by
hostname rather than by path or parameter. Its selection criteria are not
visible from the client.

**R09 (observed).** Two template placeholders MUST be supported in configured
URLs: a device query and an environment query. Substitution is textual.

**R10 (observed).** Requests MUST carry client identity in dedicated headers:
an application identifier, the application version split into major and minor
headers, and the operating system name, version and build as three further
headers.

**R11 (derived).** Splitting version into separate major and minor headers, and
OS identity into three, MUST be read as server-side routing and gating on those
values — a server that only logged them would take one string.

### 3.3 Services named in configuration

**R12 (observed).** The configuration surface MUST name discrete services as
independently configurable units. Those visible include: an authentication token
exchange; proactive routing; a background reverse geocoder; a batch reverse
geocoder; a background dispatcher; an experiment request service; and a
polynomial location-shifting service (see `07`).

**R13 (derived).** Background and batch variants of reverse geocoding being
separately configurable from the foreground path MUST be read as separate
throttling, priority and possibly endpoint treatment for work the user is not
waiting on. The throttler defaults (3.5) confirm the separation.

### 3.4 Experiments

**R14 (observed).** Experiment assignment MUST be held as a stored bucket GUID
accompanied by a timestamp and an expiry interval.

**R15 (derived).** Assignment therefore MUST roll over on its own: once the
stored GUID is older than the expiry interval, a new bucket is drawn. A device
is not pinned to a cohort indefinitely.

**R16 (observed).** Experiment state MUST be persisted in its own database,
alongside a protobuf-encoded experiments document, with a separate debug
database for internal use.

**R17 (observed).** The experiment service MUST be governed by three intervals:
a maximum refresh interval, an execute-within interval, and a failure retry
interval.

**R18 (derived).** An *execute-within* interval distinct from a refresh interval
MUST be read as deadline scheduling rather than periodic polling: the refresh is
due within a window, letting the system coalesce it with other work, rather than
firing at a fixed time.

**R19 (observed).** Experiments MUST be addressable individually by identifier,
and the entitlement set distinguishes fetching all experiments from setting
them.

### 3.5 Request throttling

**R20 (observed).** The client MUST throttle outbound service requests locally,
before they are sent, using a defaults document shipped inside the GeoServices
framework.

**R21 (observed).** Throttle buckets MUST be keyed by scope, then by request
type, then by window length. Scopes observed:

- `app:<bundle identifier>` — limits for one named calling application.
- `global` — limits applied across all callers for a request type.
- `default` — the fallback for callers with no entry of their own.

**R22 (observed).** Two window lengths MUST be supported per bucket: a **short**
window of 60 seconds and a **long** window of 600 seconds. A bucket may define
either or both.

**R23 (observed).** The `default` scope MUST distinguish two aggregate buckets:
`all`, the ceiling across every request type, and `any`, the ceiling for a
single request type with no specific entry. In the shipped document the `all`
ceiling is substantially higher than the `any` ceiling, so a caller may spend
its budget across several request types but not pour it all into one.

**R24 (observed).** Request types MUST be identified by a numeric code. Codes
visible in the shipped throttle document, with the roles its own comments give
them:

| Code | Request type |
|---|---|
| `0x20001` | Country code update |
| `0x20301` | Search |
| `0x20302` | Forward geocode |
| `0x20304` | Reverse geocode |
| `0x20307` | Place refinement |
| `0x2030a` | Autocomplete |
| `0x20317` | Place lookup by identifier |
| `0x20324` | Batch spatial event lookup |
| `0x20b24` | Spatial lookup |
| `0x20b27` | Batch reverse geocode |
| `0x20b2d` | URL shortening |

**R25 (observed).** Per-application allowances MUST vary by two orders of
magnitude according to the caller's purpose. The photo analysis daemon's
aggregate allowance is the largest in the document; the knowledge-construction
daemon is held to a handful of geocodes per hour.

**R26 (derived).** The throttler MUST therefore be read as a fairness and
cost-control mechanism across the whole operating system, not as abuse
prevention for Maps. Maps itself has no entry in the shipped document and falls
to the default scope.

### 3.6 Per-country configuration

**R27 (observed).** A country configuration object MUST exist as a distinct
configurable unit, and a country-code endpoint is carried separately from the
manifest.

**R28 (derived).** Determining the user's country MUST be a server round trip
rather than a purely local decision, since it has its own endpoint, its own
request type code, and its own throttle entry in the geo daemon's scope.

**R29 (observed).** The country-code update MUST be throttled with both windows
— six per minute, thirty per ten minutes — which is far tighter than any other
daemon-scoped entry.

## 4 Algorithms

### 4.1 Resolving one configuration value

```
resolve(key):
    value <- baked_in_default(key)

    if manifest_has(key):
        value <- manifest_value(key)

    if network_defaults_has(key):
        value <- network_defaults_value(key)

    if remote_configuration_has(key):
        value <- remote_configuration_value(key)

    if a custom environment is selected and it has(key):
        value <- custom_environment_value(key)

    return value, with the identity of the layer that last wrote it
```

### 4.2 Experiment refresh

```
on wake, on configuration change, and periodically:
    if now - bucket_guid_timestamp > bucket_guid_expire_interval:
        draw a new bucket GUID
        store it with the current timestamp

    if now - last_experiment_refresh > experiment_max_refresh_interval:
        schedule a refresh due within execute_within_interval
        # deadline, not deadline-exact: the scheduler may coalesce

on refresh failure:
    retry no sooner than failure_retry_interval
```

### 4.3 Admitting a request

```
admit(caller, request_type):
    for scope in [ "app:" + caller, "global", "default" ]:
        bucket <- lookup(scope, request_type) or lookup(scope, "any")
        aggregate <- lookup(scope, "all")

        for window in [ short (60 s), long (600 s) ]:
            if bucket defines window and count(bucket, window) >= allowed:
                reject
            if aggregate defines window and count(aggregate, window) >= allowed:
                reject

    record the request against every bucket it was checked against
    admit
```

Order of scope evaluation is inferred; the shipped document's structure requires
that some such order exists but does not state it.

## 5 Constants

| Constant | Value |
|---|---|
| Short throttle window | 60 s |
| Long throttle window | 600 s |
| Default scope, all types, short / long | 200 / 1500 requests |
| Default scope, any one type, short / long | 50 / 400 requests |
| Global autocomplete, short / long | 100 / 800 requests |
| Global URL shortening, short / long | 10 / 100 requests |
| Country code update (geo daemon), short / long | 6 / 30 requests |
| Configuration layers | 5 |
| Geo-services default keys | ~440 |
| URL template placeholders | device query, environment query |
| Client identity headers | 6 |

## 6 Rationale

A client that hard-codes endpoints ships a new binary to move a service. A
client that hard-codes nothing cannot start. The compromise here is one
hard-coded manifest URL and a layered stack above it, which lets everything
except the bootstrap move at server speed.

Naming the layers rather than merging them is a debugging decision with a real
cost: five lookups per value instead of one. It buys the ability to answer "why
is this on for this device", which for a system shipped to a billion devices is
worth more than the lookups.

The throttler is the clearest piece of design in this file. It is a shared
resource governor: every system client that wants a geocode asks the same daemon,
and the daemon holds a shipped, readable, per-caller budget. The limits encode a
judgement about what each caller is for — a photo library scanning a backlog gets
a large batch budget, a knowledge daemon doing speculative work gets almost
nothing.

## 7 Design takeaways

**01#T1.** Name your configuration layers and keep them distinct through the
read path. "Which layer set this?" is the question you will actually need to
answer at 2am, and you cannot answer it after a merge.

**01#T2.** Hard-code exactly one URL. Everything else comes from what that one
returns. The size of your "cannot be changed without a release" surface is a
design choice, and it can be one line.

**01#T3.** Make cohort assignment expire. A stored bucket with a timestamp and a
maximum age self-heals; a permanent hash of a device identifier accumulates a
population you can never rebalance.

**01#T4.** Separate "refresh is due" from "refresh now". An execute-within window
lets the scheduler coalesce your work with everyone else's, which on a battery
is the difference between a radio wake and a free ride.

**01#T5.** Throttle in the shared daemon, not in each caller. One governor with
a shipped, inspectable budget beats every client implementing its own backoff,
and it makes the per-caller policy reviewable as a document.

**01#T6.** Give background and batch variants of an operation their own
configuration and their own budget. Work nobody is waiting for should not
compete with work somebody is.

**01#T7.** Split a version number across headers if you intend to route on it.
One opaque string invites string comparison at the far end.

## 8 Uncertainties

- The precedence order in R01 is the order the layer names appear in the binary
  and is the natural reading, but it was not confirmed against the resolution
  code.
- What selects the *carry* deployment ring is unknown.
- Whether the device-query placeholder expands to a structured parameter set or
  an opaque token was not determined.
- The request type code space is only partly mapped: eleven codes are named by
  the shipped document's own comments; the encoding of the remainder, and
  whether the high bits form a service group, is not established.
- Scope evaluation order and whether a rejected request counts against its
  buckets are both inferred.
- Nothing here says how the client behaves when throttled: whether it queues,
  fails, or degrades is not visible.

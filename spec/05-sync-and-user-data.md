# 05 — Sync and user data

## 1 Purpose & scope

What Maps keeps about you, where it keeps it, and how it reaches your other
devices. Covers the record set, the sync transport, retention and cleanup, and
the separation between owned and cached data.

Not covered: what the server stores, and the contents of any actual record.

## 2 Concepts

**The sync store** is a Core Data store, mirrored to CloudKit in the user's
private database, owned by a dedicated daemon (`00#R11`).

**An owned record** is something the user made: a favourite, a collection, a
review, a report.

**A cached record** is a server copy held locally for speed or offline use. The
model keeps the two apart.

**A key-value store** is the separate, small, eventually-consistent transport
used for a handful of lightweight settings-like collections.

## 3 Requirements

### 3.1 Transport

**R01 (observed).** The sync store MUST be a Core Data store backed by the
system's CloudKit-mirroring persistent container, not a hand-written sync
protocol.

**R02 (derived).** Schema migration, change tracking, conflict resolution and
retry therefore MUST be the framework's, not the daemon's. The daemon's own
logic is retention, cleanup and the service interfaces — which is what its
configuration surface shows.

**R03 (observed).** The store MUST observe container events and distinguish
retryable failures, with a configurable initial and maximum retry interval.

**R04 (observed).** The daemon MUST additionally receive push notifications on
its own push topic (`00#R11`), so a change on another device wakes it rather
than waiting for a poll.

**R05 (observed).** The daemon MUST run a periodic activity handler, separate
from push-driven work.

**R06 (observed).** The data model MUST be versioned on disk, with the current
model and at least one earlier version shipped alongside it.

**R07 (observed).** Four distinct Mach services MUST be exposed — a general
service, a store, a cache, and the push endpoint — so a caller binds only the
surface it needs (`00#R15`).

**R08 (observed).** A separate, small set of iCloud key-value identifiers MUST
be used alongside the main store, covering history, bookmarks, recents, and
weather, in addition to the app's primary key-value store (`00#R17`).

**R09 (derived).** Two transports MUST be read as a deliberate split by size and
consistency need: key-value for small, settings-like collections that should
converge quickly, Core Data for the record set that needs schema, relationships
and query.

### 3.2 The record set

**R10 (observed).** The model MUST contain on the order of 37 entity types.
They fall into groups:

**Things the user made**

| Entity | Holds |
|---|---|
| Collection, collection item | A user's list and its members |
| Collection place item, collection transit item | Typed members of a list |
| Favourite item | A favourite |
| User route | A route the user saved |
| Incident report | A reported traffic incident |
| Report-a-problem record | A submitted correction (see `06`) |
| Reviewed place | A place the user has reviewed |
| Vehicle | A registered vehicle |

**Where the user has been**

| Entity | Holds |
|---|---|
| History item | The base of the history hierarchy |
| History place item, search item, directions item | Typed history entries |
| History EV directions item, multi-point route, transit item, ride-share item | Further typed history entries |
| History marked location, history curated collection | Dropped pins and viewed guides |
| Visit, visited location | Places the user has been |

**Identity and credentials**

| Entity | Holds |
|---|---|
| Analytics identifier | The analytics identity (see `07`) |
| Anonymous credential | The credential used for anonymous contribution (see `06`) |
| Community identifier | The contributor identity |
| Contact handle | A contact reference |
| Server evaluation status | Server-side status of submitted content |

**Cached server data**

| Entity | Holds |
|---|---|
| Cached curated collection | A guide |
| Cached map item storage | A place |
| Cached user review | A review |
| Cached vehicle | Vehicle data from the server |

**Derived signals**

| Entity | Holds |
|---|---|
| Transport mode prediction trip signals | Per-trip features |
| Transport mode prediction aggregate signals | Accumulated features |
| Shared trip blocked item | A blocked trip-sharing counterparty |
| Mixin map item | A place attached to another record |

**R11 (derived).** The cached entities being named as caches, separately from
their owned counterparts, MUST be read as an authority rule: a cached review is
a copy of what the server says, a reviewed place is the user's own act. They can
disagree, and the model does not let that ambiguity hide.

**R12 (observed).** History MUST be a typed hierarchy over a common base, with
at least nine distinct history entry types.

**R13 (derived).** Typed history MUST be read as history being re-playable
rather than merely displayable: a stored directions item carries enough to
re-request the route, which is what makes a history entry actionable.

**R14 (observed).** Transport mode prediction signals MUST be stored in two
forms, per-trip and aggregate, and MUST sync.

**R15 (derived).** Syncing the aggregate signal and not only the prediction MUST
be read as the model travelling with the user: a new device inherits the
accumulated evidence rather than starting cold. The prediction is computed in
the prediction daemon (`08`); the evidence lives here.

### 3.3 Retention

**R16 (observed).** Retention MUST be configured per record class, in days, with
separate keys for at least: favourite expiry; orphaned map item expiry;
transaction history expiry; transport mode prediction expiry; and a visit
cleanup threshold.

**R17 (observed).** Cleanup MUST be individually switchable per class, with
separate flags for: expired favourites; orphaned map items; cached curated
collections; transaction history; and transport mode predictions.

**R18 (derived).** A separate enable flag and interval per class MUST be read as
retention policy being operable without a release — a cleanup that turns out to
be too aggressive can be disabled for one class without touching the others.

**R19 (observed).** Cached map items MUST be refreshed on a configurable
interval in days, independently of their expiry.

**R20 (observed).** Map items MUST be able to be stamped with a date, under a
configuration flag.

**R21 (derived).** R19–R20 together mean a cached place has two clocks: when it
was last refreshed, and when it expires. A place can be stale without being
evicted, which is what lets the map show something immediately while it
revalidates.

**R22 (observed).** An *orphaned* map item class MUST exist, with its own
expiry — a cached place no record refers to any more.

**R23 (derived).** Orphan collection MUST be read as the map item cache being
reference-counted against the records that mention it, in the same spirit as
offline tile subscriptions (`02#R32`).

### 3.4 Operational controls

**R24 (observed).** An initial sync check MUST be separately enableable.

**R25 (observed).** A sync-date setup threshold MUST exist, governing when the
store establishes its sync baseline.

**R26 (observed).** The store MUST carry a server request handling policy as a
configuration value.

**R27 (observed).** Object fetch batch size MUST be configurable.

**R28 (observed).** Migration helpers MUST exist for at least: migrating the
source of favourite items; externalising visited-place map items; and forcibly
unregistering faults.

**R29 (derived).** A shipped flag to force-unregister Core Data faults MUST be
read as a workaround for a specific failure mode, retained behind a switch —
the kind of control that exists because something once went wrong in the field
and could not be fixed remotely any other way.

**R30 (observed).** A search-preparation step MUST be separately switchable,
indicating the store builds an index for local search over the user's own
records.

**R31 (observed).** The daemon MUST hold a token with a creation timestamp and a
time-to-live, distinct from the account credential.

**R32 (observed).** Launch retry MUST be bounded by configurable initial and
maximum intervals.

## 4 Algorithms

### 4.1 Periodic maintenance

```
on the periodic activity handler, and after a sync settles:

    if cleanup of expired favourites is enabled:
        delete favourites older than the favourite expiry, in days

    if cleanup of orphaned map items is enabled:
        for each cached map item:
            if no record references it
               and it is older than the orphan expiry:
                delete it

    if cleanup of cached curated collections is enabled:
        delete cached guides past their retention

    if cleanup of transaction history is enabled:
        delete transaction history older than its expiry

    if cleanup of transport mode predictions is enabled:
        delete prediction signals older than their expiry

    delete visits older than the visit cleanup threshold

    if map item refresh is enabled:
        for each cached map item older than the refresh interval:
            re-request it and stamp it with the current date
```

Every branch is independently switchable. That is the design, not an accident of
the pseudocode.

### 4.2 Reading a place the user saved

```
given a favourite:
    record <- the owned favourite record          # authoritative
    item   <- the cached map item it references   # may be stale or absent

    if item is absent:
        re-request the place by identifier
    else:
        render item immediately
        if item is older than the refresh interval:
            re-request in the background and restamp

    never let the cached copy override what the record says
    about the user's own act of saving it
```

## 5 Constants

| Constant | Value |
|---|---|
| Entity types | ~37 |
| History entry types | 9 observed, over a common base |
| Mach services exposed | 4 |
| Key-value identifiers | 5 (primary, plus history, bookmarks, recents, weather) |
| Shipped model versions | 2 |
| Retention keys | per class, in days |
| Retry bounds | initial and maximum interval, configurable |

## 6 Rationale

Using the platform's CloudKit-mirroring container rather than a bespoke protocol
is the decision that shapes everything else. It gives schema migration, change
tracking and conflict resolution for free, and it means the daemon's own code is
almost entirely about retention — which is why the configuration surface is
nearly all expiry intervals and cleanup switches.

The owned/cached split is the second decision worth noting. Most of what Maps
shows about a place comes from the server, and most of what the user cares about
is their own act of saving it. Modelling these as different entities means a
cache miss degrades to "we are fetching that" rather than "your favourite is
gone".

Per-class retention switches look like clutter until you consider the failure
mode they prevent. A cleanup policy that deletes too much, shipped in a binary
to a billion devices, cannot be undone. The same policy behind a configuration
flag can be turned off from the server that afternoon.

## 7 Design takeaways

**05#T1.** Use the platform's sync container if there is one. The interesting
work in a sync daemon is retention, not transport, and a bespoke transport means
you own migration and conflicts forever.

**05#T2.** Name your caches as caches in the schema. If a cached copy and an
owned record share an entity type, every reader has to decide which one is
authoritative, and they will not all decide the same way.

**05#T3.** Give every retention policy its own interval *and* its own switch.
Deletion is the one operation you cannot take back, and a server-side off switch
is the only remedy you will have.

**05#T4.** Give a cache two clocks. "Stale" and "expired" are different states,
and conflating them means either showing nothing or showing something wrong.

**05#T5.** Reference-count your caches and collect orphans. The same mechanism as
offline tiles (`02#T5`), for the same reason: "can I delete this" should have an
exact answer.

**05#T6.** Make history typed and re-playable, not a list of strings. A history
entry that can regenerate the thing it records is a feature; one that can only
be displayed is a log.

**05#T7.** Sync the evidence, not just the conclusion. A model that travels with
accumulated signals gives a new device a warm start.

**05#T8.** Wake on push, sweep on a timer. Either alone is wrong: push alone
misses cleanup, a timer alone makes other devices feel dead.

## 8 Uncertainties

- The shipped values of every retention interval are unknown; only the keys were
  read.
- Conflict resolution behaviour is assumed to be the platform's default and was
  not verified.
- What is stored in each key-value identifier, and why those four are not in the
  main store, was not determined.
- Whether history is capped by count as well as by age is unknown.
- The relationship between the sync store's community identifier and the
  anonymous credential (see `06`) is not traced.
- The entity list was recovered from the daemon's symbol surface rather than by
  parsing the shipped managed object model; attribute-level detail,
  relationships and indexes are not covered.
- The server request handling policy's possible values are unknown.

# 00 — Processes and frameworks

## 1 Purpose & scope

How the Apple Maps client is divided into processes, which framework owns which
concern, and what the app is permitted to reach. This is the map of the
territory; the other files assume it.

Scope is the macOS client of Maps 3.0 (`2972.20.6.12.47`) on macOS 27.0.1
(`26A434`), arm64e. Server behaviour is out of scope throughout.

## 2 Concepts

**The app** is a Mac Catalyst application: an iOS application binary running on
macOS through the UIKit-on-AppKit bridge. It is sandboxed and holds a large
entitlement set that opens specific holes in that sandbox.

**Frameworks** are loaded into the app's own address space. Most of the Maps
stack ships inside the dyld shared cache and has no standalone file on disk.

**Daemons** are separate processes, started on demand by launchd, reached over
XPC through named Mach services. Each owns state that must outlive the app.

**geod** is the gateway daemon. It is not a launchd daemon in the usual sense:
it is an XPC service packaged inside the GeoServices framework, with a separate
small launchd daemon alongside it whose only job is to expose a cache-deletion
service to the system.

## 3 Requirements

### 3.1 The application

**R01 (observed).** The application bundle MUST be identified as `com.apple.Maps`
and declare the travel application category. Its executable is a universal
Mach-O with two arm64e variants and no x86-64 slice.

**R02 (observed).** The app MUST declare itself a Mac idiom Catalyst
application, supporting multiple scenes, with a minimum system version equal to
the host OS major version of the build it ships with.

**R03 (observed).** The app MUST run sandboxed, with the hardened-process
protections enabled, including checked allocations in soft mode. Soft mode means
allocation checks report rather than terminate — a protection being rolled out,
not yet enforced.

**R04 (observed).** The app MUST declare exactly two background modes: audio,
for spoken guidance, and remote notifications, for shared-ETA and trip updates.
There is no background location mode in the application's own declaration;
continuous location belongs to the navigation daemon.

**R05 (observed).** The app MUST ship a plug-in bundle providing its AppKit-side
integration and a diagnostic app extension. It carries no embedded frameworks of
its own; everything it links is a system framework.

**R06 (observed).** The app bundle MUST carry, alongside localisation tables:
a compiled asset catalogue; an App Intents metadata bundle; a compiled on-device
web bundle; cycling guidance layout descriptions as JSON, separately for the Mac
and phone idioms and separately for planning, details and navigation; a bookmarks
property list; and a proactive-data test fixture.

That last one is a test fixture shipped in the production bundle. It is
harmless, and it is the kind of thing that survives because nobody owns deleting
it.

### 3.2 Framework division of labour

**R07 (observed).** The app MUST bind its Objective-C classes from system
frameworks at load time. Counting the classes bound per library gives the
weight of each dependency:

| Library | Classes bound | Owns |
|---|---:|---|
| GeoServices | 334 | Service calls, the data model, configuration, tiles |
| UIKit | 171 | Catalyst UI substrate |
| MapKit | 119 | The map view and its annotations/overlays |
| MapsUI | 76 | Maps-specific UI surfaces (place cards, action bars) |
| Foundation | 76 | — |
| MapsSync | 43 | The user's own records |
| Navigation | 32 | The navigation session model |
| MapsSuggestions | 31 | Predicted destinations, donations |
| Intents | 26 | Siri and App Intents |
| MapsSupport | 22 | Shared app-level support |
| VectorKit | 19 | The rendering engine |
| GeoAnalytics | 7 | Analytics submission |

**R08 (derived).** GeoServices MUST be understood as the centre of the stack,
not a utility library. It is bound more than twice as heavily as MapKit and
carries the request/response model, the place and route data model, the
configuration system, the tile store and the URL grammar.

**R09 (derived).** VectorKit's small binding count MUST NOT be read as a small
role. The app hands rendering to MapKit, which drives VectorKit; the app itself
touches the renderer only where it needs direct control. The framework is one of
the largest in the stack by code size.

**R10 (observed).** The app's own binary MUST contain 2,709 Objective-C class
definitions, 1,295 protocol definitions and 180 category definitions,
referencing roughly 4,000 distinct class names and 47,000 distinct selectors. The app is thin relative to the stack beneath it,
but it is not small.

### 3.3 The daemon set

**R11 (observed).** The following processes MUST exist, each registered with
launchd under its own label and exposing named Mach services:

| Process | Concern | Lifecycle |
|---|---|---|
| `geod` | Every server call, the tile store, configuration, experiments | XPC service inside GeoServices.framework, started on demand |
| `com.apple.geodMachServiceBridge` | Exposes cache deletion to the system | Starts at load, pressured-exit enabled |
| `com.apple.navd` | The active navigation session | Kept alive |
| `com.apple.maps.destinationd` | Predicted destinations and donations | On demand |
| `com.apple.Maps.mapspushd` | Shared trips and ETAs over the push transport | Starts at load |
| `com.apple.Maps.mapssyncd` | The user's synced records | On demand, launch events |
| `com.apple.geoanalyticsd` | Analytics batching and upload | Starts at load, plus an interval timer |

**R12 (observed).** `navd` MUST be configured to stay alive, unlike every other
process in the set. Navigation must not be subject to on-demand teardown.

**R13 (observed).** `geoanalyticsd` MUST be the only process in the set
configured with a repeating start interval. Analytics upload is time-driven,
independent of app activity.

**R14 (observed).** Every daemon in the set except the service bridge MUST
enable pressured exit, allowing the system to reclaim them under memory
pressure. Combined with transaction support, this means each daemon declares
when it is mid-work and therefore unsafe to kill.

**R15 (observed).** `mapssyncd` MUST expose four distinct Mach services —
a general service, a store interface, a cache interface, and a push endpoint —
rather than one. Callers bind the narrowest surface they need.

**R16 (observed).** `mapspushd` MUST expose endpoints both for app-facing work
(a shared-trip service, a media service, an iCloud service, a GeoServices
bridge) and for push-transport wake-up, including a high-priority wake path for
ETA updates.

### 3.4 What the app is permitted to reach

**R17 (observed).** The app MUST hold 83 entitlements. They fall into groups:

- **Map services.** Configuration access across all domains; manifest fetch;
  experiment read and write; tile-group switching; request counting; database
  shrink; user-initiated request permission; a general utility entitlement.
- **Location.** An effective-bundle identity for location attribution, and a
  location simulation entitlement.
- **Routine and prediction.** Locations of interest, including deletion; map
  hints; predictions; vehicle location.
- **Personal data.** Contacts, calendars, photos under the private TCC
  allowances; the address-book, calendar and location sandbox permissions.
- **Messaging and sharing.** The private messaging service dedicated to Maps,
  with a high-priority variant; trip-sharing receipt; Find My friendship,
  location and settings services.
- **Analytics and feedback.** The analytics daemon; a radar-filing service.
- **Storage.** The Maps application group, also declared restricted; direct
  storage access to the sync and weather containers; the iCloud key-value store
  plus four additional key-value identifiers covering history, bookmarks,
  recents and weather.
- **Device identity.** Device identifier and SPI access through the activation
  daemon; attestation access; a keychain group.
- **Wi-Fi.** Private Wi-Fi access including ANQP queries and a power control
  entitlement — used for positioning, not for networking.

**R18 (observed).** The app MUST additionally declare a list of 54 Mach services
it may look up by global name as sandbox exceptions. This list is the true IPC
surface: it names not only the Maps daemons but also launch services, contacts
and event suggestion daemons, the personalisation portrait services, the call
services daemon, the payment daemon, Siri activation, the recents daemon, and
the Wi-Fi daemon.

**R19 (derived).** The app SHOULD be read as privileged far beyond a third-party
application. A reimplementation built on public API cannot reach most of this,
and the gap is structural rather than a matter of approval.

**R20 (observed).** The app MUST declare a sandbox-profile exception entitlement
alongside its file-path exceptions. Where a system application needs a hole that
the declarative entitlement vocabulary cannot express, it carries a profile
fragment instead.

### 3.5 Framework resources on disk

**R21 (observed).** Although the framework binaries live in the shared cache,
their resource directories MUST remain on disk and are readable without any
cache extraction. Notable contents:

- **GeoServices** — a category taxonomy and a point-of-interest type mapping,
  both JSON; a throttler defaults property list; a wallet category styling map;
  a geoid separation model.
- **VectorKit** — compiled Metal shader libraries; ground-settings descriptions
  for day and night; generic road-shield style sets at five size classes in 1×
  and 2×; puck, arrow and balloon artwork; a non-tiled asset description; a map
  inspector service description.
- **GeoKit** — a time-zone hit map with its metadata, a time-zone equivalence
  table, per-offset artwork in day and skyglow variants, and a Core Data model.
- **Navigation** — three audio files: a turn-left tone, a turn-right tone, and
  an approach tone.
- **MapsSync** — the Core Data model describing the synced record set.

**R22 (derived).** The geoid separation model shipping in both GeoServices and
VectorKit MUST be read as both needing to convert between ellipsoidal and
mean-sea-level altitude without a round trip to the other.

## 4 Algorithms

### 4.1 Resolving a framework image for analysis

```
given a framework path under /System/Library/PrivateFrameworks:
    if the path resolves to a regular file:
        it is a real binary; thin it and read it directly
    else:
        # the symlink dangles: the image lives in the dyld shared cache
        the image is still addressable by its original path
        use the system dyld inspection tool to read its sections
        note: name sections that the cache coalesces across images
              (Objective-C class and method names) come back empty;
              the C string section does not
```

This is why `tools/extract/` has two string extractors rather than one.

### 4.2 Which process answers a given need

```
need a map tile, a place, a route, a search, any server answer
    -> geod

need turn-by-turn guidance to continue when the app is gone
    -> navd

need the user's favourites, collections, history, reviews, reports
    -> mapssyncd

need "where is this person likely going"
    -> destinationd

need to publish or receive an ETA or a shared trip
    -> mapspushd

need to record that something happened
    -> geoanalyticsd
```

## 5 Constants

| Constant | Value |
|---|---|
| Bundle identifier | `com.apple.Maps` |
| Application group | `group.com.apple.Maps` (also declared restricted) |
| Keychain access group | `apple` |
| Primary key-value store | `com.apple.Maps` |
| Additional key-value stores | history, bookmarks, recents, weather |
| Watch counterpart | `com.apple.NanoMaps` |
| User activity type | `com.apple.Maps` |
| Private messaging service | `com.apple.private.alloy.maps` |
| Asset type permitted | geo polygon data assets |
| Entitlement count | 83 |
| Mach lookup exceptions | 54 |
| Classes bound from GeoServices | 334 |

## 6 Rationale

The division is not arbitrary. Each daemon owns state with a lifetime longer
than a window:

- A route in progress must survive the app being killed, so it lives in a
  process configured never to be torn down on demand.
- The tile store is expensive to rebuild and shared between every client of the
  map, so it lives behind the one process that talks to the server.
- Synced records must reconcile whether or not anyone is looking at them.
- Analytics must upload on a schedule unrelated to usage, or the sample is
  biased toward people who leave the app open.

The entitlement list is the honest measure of how much of Maps is reachable
from outside Apple. Most of it is not.

## 7 Design takeaways

**00#T1.** Put state in the process whose lifetime matches the state, not the
process that happens to create it. "Navigation keeps running when the app dies"
is a product requirement that falls out of the process split for free.

**00#T2.** Give each daemon one named service per caller shape rather than one
service with a wide interface. The sync daemon's four services let a cache
client bind a cache interface and nothing else.

**00#T3.** Declare transactions and allow pressured exit. A daemon that can say
"I am mid-work" can also be killed safely the rest of the time, which is most of
the time.

**00#T4.** Count the symbols a binary imports per library before reading any
code. It is cheap, it is exact, and it ranks the dependencies honestly — the
ranking here contradicts the obvious guess that MapKit is the centre.

**00#T5.** Keep resources outside the binary. Every shipped resource directory
in this stack is readable and diffable without touching the code, which is how
shields, taxonomies and audio get changed without a code review.

**00#T6.** When one process is the only one allowed to talk to the network, the
privacy story becomes auditable. Everything else in the stack asks it.

## 8 Uncertainties

- The two arm64e variants in the universal binary are not explained here. The
  second carries a platform suffix and is assumed to target a newer pointer
  authentication variant; this was not verified.
- The mapping from each entitlement to the feature that needs it is inferred
  from names. Several — the Wi-Fi power control entitlement in particular — have
  no obvious consumer in the static evidence.
- The in-bundle web bundle is compiled and was not decoded. What renders in a
  web view inside Maps is unknown.
- The division of labour between MapsUI and the app's own UI classes is asserted
  from naming, not traced.
- Whether `geod` is a single process serving all clients or one instance per
  client was not determined; the XPC service packaging allows either.

# 02 — Map data, tiles and offline

## 1 Purpose & scope

How map data is addressed, packaged, stored, versioned and retained — including
how a region is taken offline. Covers the tile key, the vector tile container,
the tile database, the active data edition, the resource manifest, and the
offline subscription model.

Not covered: rendering (see the gap note in `INDEX.md`), and the server side of
tile production.

## 2 Concepts

**A tile key** addresses one unit of map data. One key type addresses every
kind, not just square map tiles.

**A tile group** (or edition) is a coherent version of the whole data set.
Tiles belong to one; mixing editions is not allowed.

**The resource manifest** describes which editions and resources are current.
It is fetched with a token and refreshed on an interval.

**A subscription** is a standing request for a set of tiles to be present
locally — the mechanism behind an offline region.

**A tileset** is a group of tiles within a subscription, sized and evicted as a
unit.

## 3 Requirements

### 3.1 The tile key

**R01 (observed).** Map data MUST be addressed by a single tagged union, 128
bits wide, consisting of a 7-bit tag, a 1-bit flag, and a 120-bit variant body.

**R02 (derived).** Every variant MUST occupy exactly 120 bits. This was checked
by summing the declared field widths of all fourteen variants; each sums to 120.
The union is therefore fixed-size and directly comparable, hashable and storable
as a 16-byte value with no padding or indirection.

**R03 (observed).** One variant — the quad-identifier variant — MUST itself
contain a nested union of three alternatives. Each of those three alternatives
is exactly 32 bits wide, so the nesting does not disturb R02.

**R04 (derived).** A nested union whose alternatives are all the same width MUST
be read as the same discipline applied one level down: the inner choice is free,
because it cannot change the size of anything containing it.

**R05 (observed).** The variants MUST cover, with the roles their shipped names
give them:

| Variant | Addresses |
|---|---|
| Standard tile | Ordinary map data tiles |
| Quad-ID tile | Data addressed by a 64-bit quad identifier rather than x/y |
| S2 tile | Data addressed on the S2 sphere-cell scheme |
| Live tile | Data with a time dimension — traffic and similarly volatile layers |
| Regional resource | Per-region resources that are not tiles |
| Identified resource | A resource named by a 64-bit identifier plus two bytes |
| Contour lines | Terrain contour data |
| Tile overlay | Overlay layers above the base map |
| Transit line selection | A selected transit line |
| Road selection | A selected road |
| Polygon selection | A selected polygon feature |
| Aerial imagery tile | 3D aerial imagery |
| Ground imagery mesh | Street-level imagery geometry |
| Imagery metadata | Metadata for the imagery products |

Three of these carry an internal codename in the shipped type name; they are
described by function here (see [`../CLEANROOM.md`](../CLEANROOM.md)).

**R06 (observed).** Most variants MUST share a common field shape of six fields
with widths 6, 26, 26, 14, 4 and 4 bits. The standard tile variant prefixes a
further 40-bit field to this shape.

**R07 (inferred).** The two 26-bit fields MUST be plane coordinates. 2²⁶ values
per axis admits a tile pyramid up to zoom level 26, which matches the depth the
map offers. Field semantics beyond this were not confirmed and should not be
relied on.

**R08 (observed).** The three selection variants — transit line, road, polygon —
MUST share an identical shape: a 6-bit field, two 25-bit fields, and a 64-bit
identifier. Selection highlighting is one mechanism with three feature types.

### 3.2 The vector tile container

**R09 (observed).** Vector tiles MUST be carried in a container format
identified by a four-character tag, decoded by a codec layer shared between the
service framework and the renderer.

**R10 (observed).** The decoder MUST reject: data whose header cannot be read;
data that is not in the container format; a tile exceeding a maximum parse size;
and a tile carrying no embedded tile key.

**R11 (derived).** Because a tile carries its own key, the container MUST be
self-describing: a decoded tile can be validated against the key it was
requested under, and a tile found on disk can be identified without its
filename.

**R12 (observed).** The container MUST carry a history count, which the decoder
validates. A versioned or incremental structure is implied; its semantics were
not determined.

**R13 (observed).** A separate asset decoder MUST exist in the same codec layer,
distinct from the tile decoder. Non-tiled assets are described by a shipped JSON
resource in the renderer's bundle, which names each asset and gives it a 64-bit
identifier — the assets addressed by the identified-resource variant of the tile
key (`R05`, `09#R92`).

**R14 (observed).** The container's payload MUST be divided into independently
compressed chapters, each carrying an identifier, a start and end byte offset,
and an uncompressed length. The chapter vocabulary is specified in `09#R20`;
the tile key (`R01`) says where a tile is, and the map data type (`09#R11`) says
what it carries.

### 3.3 The tile database

**R15 (observed).** Tiles MUST be stored in a local database whose path and
maximum size in bytes are both configuration keys.

**R16 (observed).** The store MUST be SQLite-backed, and the client MUST hold a
distinct entitlement permitting it to shrink that database.

**R17 (observed).** The store MUST publish notifications for: a full reset; the
beginning of an edition update; the end of an edition update; and an edition
upgrade. Edition transitions are observable events with explicit boundaries, not
background drift.

**R18 (observed).** A data-set change MUST be able to flush the tile cache, and
a separate configuration key forces a flush on version change.

**R19 (observed).** Cache entries MUST carry invalidation metadata as four
distinct keys: a version, a timestamp, a time-to-live, and a set of version
domains.

**R20 (derived).** Version *domains* in the plural MUST be read as independent
invalidation scopes — a change to one class of data need not invalidate
everything else cached under the same edition.

**R21 (observed).** A default resource time-to-live MUST exist as a
configuration key, so resources without their own TTL still expire.

### 3.4 The active tile group

**R22 (observed).** The current edition MUST be recorded as an "active tile
group", persisted as a protobuf-encoded document.

**R23 (observed).** The client MUST support overriding the active tile group
through configuration, and separately disabling automatic updates to it. The
application holds a dedicated entitlement to change tile groups.

**R24 (derived).** Taken together, R19–R20 mean an engineer can pin a device to
a specific data edition, which is what you need to reproduce a map data bug
against the edition that produced it.

### 3.5 The resource manifest

**R25 (observed).** The manifest MUST be fetched from a configurable URL, and
the client records the last URL used and the environment it belongs to.

**R26 (observed).** Manifest requests MUST carry a request token, stored with a
timestamp and an expiration interval.

**R27 (observed).** A manifest update interval MUST exist as a configuration
key, independent of the token expiry.

**R28 (observed).** The tile loader MUST publish a notification when regional
resources are updated, distinct from the edition notifications.

### 3.6 Offline regions

**R29 (observed).** Offline map data MUST be modelled as *subscriptions* over
batches of data, not as downloads of files. The wire protocol carries: a batch
reference; a request for batches; a request for the size of batches; a key-value
data reference; a layer version; request and response metadata; and performance
metrics.

**R30 (observed).** A subscription MUST persist, at minimum: a primary key; a
download state; per-subtype data states; a data version; an import-completed
flag; timestamps; and a size per tileset.

**R31 (observed).** Subscriptions MUST be queryable by the data they reference,
including queries for subscriptions referencing old tiles and the oldest N
tiles.

**R32 (derived).** Eviction MUST therefore be reference-aware: the store can ask
"what still wants this tile" before discarding it, so two overlapping offline
regions share storage and neither can delete the other's data.

**R33 (observed).** A subscription MUST be able to report that it is waiting,
with a reason, and one named waiting reason is a minimum battery level.
Downloads are suspended on low battery rather than failed.

**R34 (observed).** Subscriptions MUST be able to expire, with separate storage
and fetch paths for expired subscriptions.

**R35 (observed).** The protocol MUST carry an explicit client-revision
capability indicating that the client can handle offline data, and a component
type indicating whether a region supports offline maps at all.

**R36 (observed).** Offline region components MUST include an area, an
identifier, a set of quad nodes, a size, and an update manifest.

**R37 (derived).** Quad nodes as the area representation MUST be read as regions
being defined by a quadtree cover rather than a bounding box, which is why two
regions can share data exactly rather than approximately.

**R38 (observed).** A downloaded region MUST have a state indicating the device
is outside it, distinct from unknown. The client knows the difference between
"you have left this region" and "no idea".

### 3.7 Constrained-network updating

**R39 (observed).** A distinct update mode MUST exist for constrained networks,
configured by: whether it is enabled for a given tile type; a maximum size of
tiles to update; and a maximum count of stale tiles to update.

**R40 (derived).** Bounding both bytes and tile count MUST be read as protecting
two different budgets — a data allowance and a request allowance — which do not
have the same shape.

## 4 Algorithms

### 4.1 Evicting tile data

```
need to reclaim N bytes:
    candidates <- oldest tiles by last use

    for tile in candidates:
        holders <- subscriptions referencing tile
        if holders is empty:
            delete tile
        else:
            skip                      # an offline region still wants it

    separately, on their own schedule:
        delete failed tiles older than the failure retention window
        delete data belonging to superseded editions of each tileset
```

### 4.2 Moving to a new data edition

```
manifest refresh returns a new active tile group:

    if automatic tile group updates are disabled:
        stop

    publish edition-update-begin
    record the new active tile group
    if the configuration says a version change forces a flush:
        flush the tile cache
    else:
        invalidate only the version domains the manifest marks changed
    publish edition-update-end
    publish edition-upgrade
```

### 4.3 Taking a region offline

```
user selects a region:
    cover <- quadtree nodes covering the region
    create a subscription recording the cover, a data version, state "waiting"

    ask the service for the batches covering the cover, and their total size
    present the size to the user

    while batches remain:
        if battery below minimum:
            set state waiting, reason minimum battery level
            wait
        if the network is constrained:
            bound this pass by max update size and max stale tile count
        fetch the next batch
        import it, recording per-subtype data state

    mark import completed
```

## 5 Constants

| Constant | Value |
|---|---|
| Tile key width | 128 bits (7-bit tag, 1-bit flag, 120-bit body) |
| Tile key variants | 14, each 120 bits |
| Coordinate field width | 26 bits per axis (admits zoom ≤ 26) |
| Selection variant shape | 6 + 25 + 25 + 64 bits |
| Cache invalidation keys | version, timestamp, TTL, version domains |
| Constrained-update bounds | max bytes, max stale tile count |

## 6 Rationale

One key type for everything addressable is the load-bearing decision. Because a
traffic layer, a 3D mesh, a selected road and an ordinary map tile are all the
same 16-byte value, one cache, one eviction policy, one request pipeline and one
subscription mechanism serve all of them. The cost is a union that must be kept
in sync across every variant, and a 40-bit field in the standard variant that
exists because standard tiles needed more room than the shared shape allows.

Offline as subscription rather than download is the second decision that pays.
Downloading a region as a file makes two overlapping regions cost twice. Making
it a reference-counted subscription over shared batches makes the overlap free
and makes eviction answerable — "can I delete this" has an exact answer instead
of a heuristic.

Explicit begin/end notifications around an edition change exist because the
alternative is a map that is half one edition and half another while a user
looks at it. Making the transition a bracketed event lets every layer above
decide whether to hold, reload, or ignore.

## 7 Design takeaways

**02#T1.** If several resource kinds share a cache, a fetch pipeline and an
eviction policy, give them one key type. Fixed-width and padding-free means it
can be a value, which means it can be a dictionary key, a database column and a
network field without serialisation.

**02#T2.** Make every variant of a tagged union the same width on purpose, and
check it. Here all fourteen sum to 120 bits — that is a design constraint, not
a coincidence, and it is what makes the key storable as a plain 16-byte value.

**02#T3.** Put the key inside the payload. A tile that carries its own key can
be validated against what you asked for and identified after you have lost the
filename.

**02#T4.** Version your cache in domains, not globally. One global version means
every change costs a full refetch.

**02#T5.** Model local copies as subscriptions, not downloads. Reference counting
turns "is it safe to delete this" from a guess into a query, and makes
overlapping requests free.

**02#T6.** Cover regions with a quadtree, not a rectangle. Exact sharing between
overlapping regions needs an exact common vocabulary of pieces.

**02#T7.** Give a stalled download a *reason*, not just a state. "Waiting:
battery below minimum" is a UI string, a metric and a support answer; "waiting"
is none of them.

**02#T8.** Bound constrained-network work by both size and count. They protect
different budgets and neither bound implies the other.

**02#T9.** Let an engineer pin the data version. A map bug you cannot reproduce
against the edition that produced it is a bug you cannot fix.

## 8 Uncertainties

- Field semantics within the 120-bit bodies are largely unknown. Only the
  26-bit coordinate reading is argued, and it is inferred.
- The 40-bit prefix on the standard variant has no identified meaning.
- The container's history count is observed but unexplained.
- Whether the tile database is one SQLite file or several was not determined.
- The eviction algorithm in 4.1 is a reconstruction from the names of the
  queries the store supports, not from its logic.
- Nothing here establishes the actual retention limits: the maximum byte size is
  a configuration key whose shipped value was not read.
- How offline regions interact with edition changes — whether a downloaded
  region is invalidated by a new edition or updated in place — is unknown,
  though the presence of an offline update manifest component suggests the
  latter.

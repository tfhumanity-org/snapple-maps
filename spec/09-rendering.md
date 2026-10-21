# 09 — Rendering

## 1 Purpose & scope

How a tile becomes pixels. Covers the renderer's architecture, the map data
types, what a vector tile actually contains, the compiled stylesheet format and
how a style is resolved for a feature, label composition and placement, and the
draw itself.

This is the file `INDEX.md` previously named as the largest gap. It is no longer
the largest gap, but it is still the least complete file here: the renderer is
by a wide margin the biggest component in the stack, and what follows is its
structure rather than its algorithms.

Three subsystems carry internal codenames in their shipped type names — the
3D/globe renderer, the ground-level imagery renderer, and the style language.
They are described by function (see [`../CLEANROOM.md`](../CLEANROOM.md)).

## 2 Concepts

**A map data type** names a kind of tile payload. There are 78 of them. The
tile key (`02#R01`) says *where*; the data type says *what*.

**A chapter** is a named, independently compressed section of a tile. A tile is
a container of chapters, not a blob.

**A stylesheet** is a compiled, bit-packed binary artifact. The source language
it is compiled from does not ship.

**A style** is a set of property values resolved for one feature at one zoom in
one display mode.

**A label part** is one renderable piece of a label — a text run, an icon, a
shield, a border. Labels are composed from parts.

**A logic** is a system in the renderer's entity-component-system: a unit of
per-frame work over the entities that have the components it cares about.

**A frame graph** is the per-frame plan of render passes and their
dependencies, rebuilt each frame rather than fixed.

## 3 Requirements

### 3.1 Architecture

**R01 (observed).** The renderer MUST be organised as an entity-component-system
with a task graph, using a third-party task-flow library for scheduling.

**R02 (observed).** Per-frame work MUST be divided into 23 named logics.
Observed, grouped by what they do:

| Group | Logics |
|---|---|
| Deciding what data is needed | tile selection, tile dependency, loading status |
| Turning data into a scene | style, elevation, draping, pending scene, non-tiled asset |
| Lighting and geometry | lighting, mesh renderable, renderable collection |
| Overlays and furniture | overlays, route overlay, puck, grid |
| Imagery and specialised modes | ground-level imagery scene, hiking, three for augmented reality |
| Queries and labels | scene query, label external mesh |
| Diagnostics | display-link verification |

**R03 (observed).** Higher-level stages MUST be organised as eight named
modules: frame graph construction, encoding, mesh rendering, camera control,
camera collision, globe lighting, interactive frame, and a legacy layout module.

**R04 (observed).** Several modules MUST have an associated graph — frame graph
construction, camera control, camera collision, globe lighting — indicating
these stages are themselves dependency graphs rather than straight-line code.

**R05 (observed).** The frame graph MUST be *built* each frame, as a distinct
named stage, before encoding.

**R06 (derived).** Rebuilding the pass graph per frame MUST be read as the
render pipeline being data-dependent: which passes exist depends on what is on
screen — whether there are buildings, whether ambient occlusion is on, whether
the globe is visible — rather than being a fixed sequence with disabled stages.

**R07 (observed).** The renderer MUST support asynchronous rendering and
continuous layout as separately controlled behaviours, and MUST distinguish
heavy frames from light frames.

**R08 (observed).** Per-frame work MUST be explicitly budgeted, with configured
caps on entity updates per frame and on entities reorganised per frame.

**R09 (derived).** Per-frame entity budgets MUST be read as amortisation: a
large scene change is spread across frames rather than producing one long frame.

**R10 (observed).** A legacy renderer path MUST exist alongside the current one,
as must a legacy layout module.

### 3.2 Map data types

**R11 (observed).** The map data type vocabulary MUST contain 78 values. They
divide into raster types, vector types, 3D imagery types, ground-level imagery
metadata, and two road-data types.

**R12 (observed).** Raster types MUST cover, among others: standard, and
separately a standard base, a standard background and standard labels;
satellite, with separate polar, night, polar-night, compressed-texture and
digitisation variants; hybrid, with separate roads, labels, and roads-and-labels
variants; terrain; vegetation; hillshade, with a separate parks variant;
coastline masks; a colour-balanced variant; and a downsampled variant.

**R13 (derived).** Standard raster being split into base, background and labels
MUST be read as raster map rendering being composited from layers at display
time, so labels can be swapped for a different language or suppressed without
re-fetching the imagery underneath.

**R14 (observed).** Vector types MUST cover, among others: standard; roads and
separately a road network; buildings, with a second-generation variant; points
of interest, with a second-generation variant and an update variant; land cover;
contours; topographic data; tracks; venues; transit; traffic, in at least nine
variants including a skeleton, a skeleton with historical data, a static
variant, and three variants specifically for compositing onto raster maps;
speed profiles; road and polygon selection; coverage; region metadata; and
street-level landmarks and points of interest.

**R15 (observed).** 3D imagery MUST have two generations of data type, the first
carrying a mesh and two texture encodings, the second carrying a different
representation plus a surface model.

**R16 (derived).** Separate `_V2` data types alongside their predecessors for
buildings, points of interest, traffic and 3D imagery MUST be read as format
migration being handled by adding a type rather than versioning one: old clients
keep requesting the old type, and the two coexist in the same tile pyramid.

**R17 (observed).** A dedicated traffic *skeleton* type MUST exist, separate
from traffic itself, and MUST have a variant carrying historical data.

**R18 (derived).** A skeleton separate from traffic data MUST be read as the
road geometry traffic is drawn on being fetched and cached independently of the
volatile traffic values painted onto it — which is what lets traffic refresh
frequently without refetching geometry.

### 3.3 Tile contents

**R19 (observed).** A vector tile MUST be a container of independently
addressed, independently compressed chapters, each with an identifier, a start
and end byte offset, and an uncompressed length.

**R20 (observed).** The chapter vocabulary MUST contain 64 named chapters.
Grouped by role:

| Role | Chapters |
|---|---|
| Geometry primitives | vertices, point features, polygon features, line features, lines extended, compressed polygons, a point-features addendum |
| Line and polygon detail | two line-width chapters, line point characteristics, polygon point characteristics |
| Buildings | building features, building meshes, border building meshes, high-resolution buildings, low-resolution buildings, low-resolution border buildings |
| Terrain | elevation raster, digital terrain raster, material raster, hiking hill-shade raster, contour lines in feet and in metres, plus global contour chapters for each |
| Labels | labels, annotation labels, label languages, label localisations, label placement metadata, point label annotations, polygon point label positions |
| Networks | road network, connectivity, address ranges, transit network, transit systems |
| Live and volatile | live features, live-feature metadata, two traffic skeleton chapters |
| 3D imagery | 3D data, buildings, landmark buildings, landmarks, asset metadata, metadata |
| Places | venues, storefronts, running tracks, point-of-interest updates |
| Zoom overrides | point-of-interest, transit and venue minimum-zoom overrides |
| Styling | two style attribute raster chapters |
| Housekeeping | global, coverage, region metadata, tile references, supplemental feature identifiers, geoid segments, coastline features, wrapping coastline features |

**R21 (derived).** A chaptered container MUST be read as enabling partial
decode: a pass that needs only labels decompresses the label chapters and leaves
the geometry packed.

**R22 (observed).** Label placement metadata MUST be a chapter of the tile.

**R23 (derived).** Precomputed placement metadata shipping *inside the tile*
MUST be read as label placement being partly solved server-side, where the
global context is available, and refined on device against the actual viewport.
Polygon point label positions being a separate chapter supports this: where to
put a label inside a park or a lake is computed once, offline, not per frame.

**R24 (observed).** Label languages and label localisations MUST be separate
chapters from labels themselves.

**R25 (derived).** Separating text from the feature it labels MUST be read as
one tile serving every language, with the renderer selecting a localisation at
draw time — consistent with the dual-language label support in 3.7.

**R26 (observed).** Minimum-zoom overrides MUST be shippable per tile, separately
for points of interest, transit and venues.

**R27 (derived).** Per-tile zoom overrides MUST be read as density management:
the zoom at which a feature class appears is globally styled but locally
adjustable, so a dense city and an empty region can differ without two
stylesheets.

### 3.4 The compiled stylesheet

**R28 (observed).** A stylesheet MUST be a compiled binary artifact carrying a
version, organised into compressed chapters in the same manner as a tile
(`R19`), including a dedicated property-information chapter.

**R29 (observed).** The format MUST be bit-packed with data-dependent field
widths. The encoder MUST write, and the decoder MUST read, an explicit bit count
for each of at least: property identifiers; property set indices; style counts;
conditional style counts; zoom style counts; condition counts; condition
attribute counts; attribute values; attribute value counts; feature attributes;
client attributes; inheritance list lengths; node indices; node child counts;
chunk sizes; end-chain counts; and end-chain lengths.

**R30 (derived).** Every count in the format therefore MUST be stored in the
minimum number of bits the actual data requires, determined at compile time.
This is a size optimisation with a real cost — nothing in the file can be read
without reading the widths first — and it tells you the artifact is large enough
for that trade to be worth making.

**R31 (observed).** Property values MUST be typed, with at least these
encodings: boolean; unsigned 8-bit; signed 16-bit; signed 32-bit; unsigned
64-bit; float; float pair; colour gradient, read as two halves; and fixed-point
in the forms 8.8, 12.4, 6.2, 5.3 and 8.0, plus normalised forms spanning −1 to 1,
0 to 1, and 0 to 2.55.

**R32 (derived).** A 0-to-2.55 normalised form MUST be read as an 8-bit value
interpreted as hundredths — a multiplier or brightness factor stored in one byte
with two decimal places of precision.

**R33 (observed).** The decoder MUST validate bit counts per type and reject a
property whose declared width does not suit its declared type.

**R34 (observed).** A stylesheet MUST carry a debug flag.

### 3.5 Style resolution

**R35 (observed).** Styles MUST be matched through a graph of nodes with
children, node indices, terminal and undefined node markers, and chains, stored
in chunks.

**R36 (derived).** A matching graph rather than a rule list MUST be read as
selector matching being compiled into a traversal: shared selector prefixes
become shared paths, so matching a feature costs a walk proportional to its
attribute count rather than a scan proportional to the rule count.

**R37 (observed).** A condition MUST be a set of attributes with permitted
values. Attributes MUST be drawn from two spaces: feature attributes, which come
from the tile, and client attributes, which do not.

**R38 (derived).** Client attributes MUST be read as the device's own state
participating in selector matching — display mode, navigation state, selection,
time of day — so "this road, while navigating, at night" is a selector rather
than client code.

**R39 (observed).** A style MUST be able to inherit from other styles, with an
inheritance list of configurable length and an inherited style index.

**R40 (observed).** A style MUST resolve through two further levels before
reaching property values: conditional styles, and within those, zoom styles.

**R41 (observed).** A zoom style MUST carry a minimum zoom, a maximum zoom, and
a property set index.

**R42 (derived).** Resolution therefore MUST proceed feature → matching graph →
style → conditional style → zoom style → property set. Zoom is resolved last,
which means a conditional style carries a *band* of zoom-dependent appearances
rather than the style being re-matched at each zoom.

**R43 (observed).** A stylesheet MUST declare a number of modes and a per-style
mode support flag.

**R44 (derived).** Modes MUST be read as the top-level display variants —
standard, satellite, hybrid, transit and their night counterparts — with a style
declaring which it participates in, so one artifact carries every mode.

**R45 (observed).** Style attributes MUST additionally be shippable as a raster
chapter in the tile, in two generations (`R20`).

**R46 (derived).** A style attribute *raster* MUST be read as per-pixel rather
than per-feature styling input — ground appearance varying continuously across
a tile, which no per-feature attribute could express.

**R47 (observed).** A currency style attribute table MUST ship as a resource,
mapping ISO currency codes to small integers.

**R48 (derived).** That table MUST be read as the attribute space being wider
than geometry: a feature's currency is a selectable attribute, which is how a
price-bearing label styles itself by region.

### 3.6 Global style properties

**R49 (observed).** A stylesheet MUST carry global properties alongside
per-feature styles. Each is optional, encoded as a presence flag followed by the
value. Observed groups:

| Group | Properties |
|---|---|
| Level of detail | global scale, offset |
| Zoom ranges | vector roads, buildings, polygons, land cover, points of interest, venues, traffic; ground cover; standard, satellite, hybrid and background rasters; raster traffic |
| Changeover zooms | building changeover, raster polygon changeover, navigation map zoom level transition |
| Labels | height, height curve, height curve limit, font expansion, halo size, icon scale, spacing, alternate-text-position disable |
| Navigation labels | maximum road signs, road sign height, and road sign heights at five size classes |
| Traffic | visibility, fill colour, secondary colour, gradient mask colour, minimum and maximum width, secondary width with its own minimum and maximum, pill middle length, pill spacing |
| Traffic incident zooms | minimum zoom per incident type, for nine types |
| Night rendering | realistic night brightness, shield night brightness, realistic shield night brightness |
| Geometry | minimum line triangle width, arrow height |
| Navigation guidance | maneuver distances at seven bands; route sinuosity at four bands |
| Imagery | tile limit satellite scale |

**R50 (derived).** Maneuver distance bands and route sinuosity thresholds living
in the *stylesheet* MUST be read as presentation decisions rather than routing
ones: how far ahead a maneuver is drawn, and how a curve is classified for
drawing, are styling choices the data team can tune without a release.

**R51 (observed).** Traffic MUST be drawn as a pill-like form, with configurable
middle length and spacing, and MUST have primary and secondary strokes with
independent widths.

**R52 (observed).** Labels MUST have a *height curve* with a limit, separate
from a label height.

**R53 (derived).** A curve rather than a scalar MUST be read as label size
varying non-linearly with zoom or distance, clamped at a limit.

### 3.7 Labels

**R54 (observed).** A label MUST be composed from parts. The part vocabulary
contains 31 types, including: plain text, horizontal text, curved text, line
text with an auxiliary run, icons, captioned icons, icon lists, images, borders,
arrows, shields, transit pill icons, transit shield icons, transit transfer
annotations, navigation road signs, navigation shields, navigation route ETA, an
animated cross-fade part, external icon and external mesh parts, an explicit
null part, a world-space part, a ground-level-imagery road part, and eight parts
specific to augmented-reality walking guidance.

**R55 (derived).** An explicit null part MUST be read as absence being
representable in a layout, so a part slot can be empty without collapsing the
layout.

**R56 (observed).** Several labelers MUST exist for different contexts,
including a general map labeler, a navigation labeler, an ETA labeler, and
labelers for ground-level imagery and augmented-reality walking.

**R57 (observed).** Labels MUST be placed with collision detection, with a
collision priority per label and a recorded collided state.

**R58 (observed).** Alternate text positions MUST be supported, and MUST be
disableable from the stylesheet (`R49`).

**R59 (derived).** Alternate positions MUST be read as the placement algorithm
trying several candidate offsets for a label before conceding to a collision,
with the stylesheet able to forbid this per stylesheet.

**R60 (observed).** Label layout MUST be able to run on a background thread,
controlled by a setting, and MUST have a maximum label count.

**R61 (derived).** Background layout MUST be read as placement being too
expensive for the frame: labels lag the camera by design, which is why they
settle after a pan rather than during it.

**R62 (observed).** Labels MUST be z-ordered against other content by explicit
named relationships: above or beneath overlays, above external overlays, above
fog, and above the location puck.

**R63 (observed).** Text MUST be rendered from signed distance fields, with
shader variants for plain glyphs, glyphs with halos, supersampled glyphs,
coloured text, colour glyphs with normal halos, and three-dimensional glyph
variants including a low-precision form, a low-precision haloed form, and a
ray-marched form.

**R64 (derived).** Signed distance field text MUST be read as the mechanism
behind arbitrary rotation and scaling of map labels without re-rasterising, and
the halo variants as the standard legibility treatment over varied ground.

**R65 (observed).** Labels MUST support dual-language display, with both a count
override and a country override.

**R66 (observed).** Per-language text metrics MUST be carried.

**R67 (observed).** Label styles MUST be queried, with diagnostics for missing
styles and for logging style queries.

**R68 (observed).** Road shield styles MUST ship as resources at five size
classes — a default, small, medium, large and extra-large — each in 1× and 2×
scale variants.

**R69 (observed).** Features MUST carry a minimum zoom, and labels MUST carry
their own minimum zoom separately, alongside a minimum-zoom rank.

**R70 (derived).** A separate label minimum zoom MUST be read as a feature being
drawable before it is labelled: the road appears, the name arrives later.

### 3.8 The draw

**R71 (observed).** The shader set MUST contain 207 distinct families, each
compiled into vertex and fragment variants where applicable.

**R72 (observed).** Shaders MUST be specialised by function constants, with the
renderer declaring per-shader requirements for constant data, texture and device
data identifiers, and a bit set of function constants.

**R73 (derived).** Function-constant specialisation MUST be read as one shader
source producing many pipeline variants at build time, which is how 207 families
cover a far larger space of actual pipeline states.

**R74 (observed).** Precompiled Metal shader libraries MUST ship as resources:
one of roughly 3 MB and a second common library of roughly 60 KB.

**R75 (observed).** The renderer MUST support bindless mesh rendering through
argument buffers for 3D imagery, behind a setting, with shared argument buffers
for meshes and for splats.

**R76 (observed).** 3D imagery MUST have a splat-based rendering path, with
shaders for clearing, intermediate resolve, and separate final colour and depth
resolves.

**R77 (derived).** A splat path with separate colour and depth resolves MUST be
read as a point-based or Gaussian-splat representation for photogrammetric
imagery, distinct from the textured-mesh path that coexists with it.

**R78 (observed).** Two post-processing chains MUST exist — a standard one and
one for 3D imagery — sharing a structure: split frame, downsample
circle-of-confusion, foreground blur, background blur, tent blur, composite.

**R79 (observed).** The standard chain MUST additionally contain screen-space
ambient occlusion with its own blur and upsample passes, and a depth downsample.
The 3D imagery chain MUST not.

**R80 (derived).** Circle-of-confusion downsampling followed by separate
foreground and background blurs MUST be read as a depth-of-field effect — the
blur applied to distant map content when the camera is pitched.

**R81 (observed).** Buildings MUST have a large dedicated shader family set,
distinguishing flat, diffuse, specular and fogged treatments; tops, facades and
pointy roofs; depth-only variants; and shadows.

**R82 (observed).** The globe MUST have dedicated shaders for atmosphere, stars,
an earth corona, a textured surface, a pole-textured blend, and an end-of-world
shader.

**R83 (observed).** Route lines MUST have their own family set, including a
single-pass variant, a patterned variant, a dotted variant, a traffic-coloured
variant, an arrow, a mask, and an alpha reset.

**R84 (derived).** An alpha reset and a mask pass for route lines MUST be read
as the route being drawn with a stencil or alpha technique so that overlapping
segments do not double-blend — which is what stops a route doubling back on
itself from appearing darker.

**R85 (observed).** Venue interiors MUST have dedicated shaders for walls, wall
tops, wall end caps, wall shadows, horizontal and vertical 3D strokes, and
open-to-below shadows.

### 3.9 Shipped render resources

**R86 (observed).** Ground appearance MUST be configured by shipped JSON, in
separate day and night documents that differ at every entry.

**R87 (observed).** That document MUST key settings by zoom level, with 24
entries: individual zoom levels, plus four entries covering zoom *ranges* at the
low end.

**R88 (observed).** Per-zoom settings MUST include a ground elevation scale and
a normals sharpness bias. In the shipped day document the elevation scale falls
by more than an order of magnitude from the lowest zoom to zoom 16, and the
normals sharpness bias falls with it.

**R89 (derived).** Exaggerating terrain elevation at low zoom and relaxing it
when zoomed in MUST be read as deliberate cartographic exaggeration: real relief
is invisible at continental scale and distracting at street scale.

**R90 (observed).** The low-zoom range entries MUST carry four climate-class
colour adjustments in hue, saturation and value — very hot, arctic, very dry and
very wet — and MUST NOT carry elevation settings.

**R91 (derived).** Climate-class HSV adjustment MUST be read as the ground
colour of the low-zoom map being modulated by climate rather than painted into
the imagery: the shipped very-dry adjustment is a large negative hue shift with
a value lift, which is how deserts are made to read as deserts.

**R92 (observed).** Non-tiled assets MUST be declared by a shipped JSON document
listing models, material maps and materials, each named and carrying a 64-bit
identifier.

**R93 (derived).** That document MUST be read as the manifest for assets fetched
by identifier rather than by position — matching the identified-resource variant
of the tile key (`02#R05`). The shipped document declares the location puck
model and its regular and occluded materials.

**R94 (observed).** Four tile selection strategies MUST exist: a flat selector,
a non-flat selector, a consistent-zoom selector, and an offline region selector.

**R95 (derived).** Separate flat and non-flat selectors MUST be read as tile
selection differing between the planar map and the globe, where a frustum covers
a curved surface and the set of visible tiles is not a rectangle.

## 4 Algorithms

### 4.1 A frame

```
camera updates (controller graph, then collision graph)

tile selection logic:
    strategy <- flat | non-flat | consistent-zoom | offline-region
    visible  <- tile keys covering the frustum at the chosen zoom
tile dependency logic:
    for each visible tile, the data types it needs for the current mode
    request what is missing; report through loading status

for each arrived tile:
    decode only the chapters this frame needs
    style logic:
        for each feature, resolve a style (4.2)
    elevation and draping logic:
        place flat geometry onto terrain
    mesh renderable logic:
        build or update meshes; respect the per-frame entity budget

label layout (on a background thread; results lag the camera):
    (4.3)

lighting logic, globe lighting module
renderable collection:
    gather what is actually visible this frame

build frame graph:
    passes and their dependencies, from what the scene contains
encode:
    for each pass, set pipeline states from the shaders'
    function-constant requirements, then draw

post-processing chain:
    split frame
    downsample circle-of-confusion (and depth, standard chain only)
    screen-space ambient occlusion, blur, upsample (standard chain only)
    foreground blur, background blur, tent blur
    composite
```

### 4.2 Resolving a style for one feature

```
attributes <- feature attributes from the tile
            + client attributes from device state
              (mode, navigation, selection, time of day)

node <- root of the style matching graph
for each attribute in the graph's traversal order:
    node <- child of node matching (attribute, value)
    if node is undefined:   no style; the feature is not drawn
    if node is terminal:    break

style <- the style at node
for each inherited style index in style's inheritance list:
    merge in the inherited style's properties first

if style does not support the current mode:
    the feature is not drawn in this mode

conditional <- the conditional style whose conditions the
               attributes satisfy
zoom_style  <- the zoom style of conditional whose
               [min zoom, max zoom] contains the current zoom
properties  <- property set at zoom_style's property set index

apply global properties: level-of-detail scale and offset,
    the zoom range for this feature class, any per-tile
    minimum-zoom override
```

The traversal order of attributes through the graph is not established; the
structure requires that one exists.

### 4.3 Laying out labels

```
candidates <- label features in view, with:
                precomputed placement metadata from the tile
                precomputed polygon label positions where applicable
                a minimum zoom, a minimum-zoom rank, a collision priority

discard candidates below their label minimum zoom
sort by collision priority

for each candidate, highest priority first:
    text <- select the localisation for the display language
            (and a second language if dual-language is enabled,
             subject to the country and count overrides)
    parts <- compose the label from its parts: text runs, icons,
             shields, borders
    size  <- from label height and the label height curve,
             clamped at the curve limit, scaled by icon scale
             and font expansion

    positions <- [ the precomputed position ]
    if alternate text positions are not disabled by the stylesheet:
        positions <- positions + candidate offsets

    for position in positions:
        if the label's bounds at position collide with nothing
           already placed:
            place it; stop
    otherwise:
        mark collided; do not draw

    stop when the maximum label count is reached

emit glyph meshes and icon meshes, z-ordered by the configured
relationships to overlays, fog and the puck
```

Candidate generation, the exact collision test and the alternate-offset set are
not visible in the static evidence; the structure is reconstructed from the
vocabulary.

## 5 Constants

| Constant | Value |
|---|---|
| Map data types | 78 |
| Tile chapter types | 64 |
| Shader families | 207 |
| Per-frame logics | 23 |
| Renderer modules | 8 |
| Label part types | 31 |
| Style resolution levels | style → conditional style → zoom style → property set |
| Stylesheet fixed-point forms | 8.8, 12.4, 6.2, 5.3, 8.0 |
| Stylesheet normalised forms | −1 to 1, 0 to 1, 0 to 2.55 |
| Maneuver distance bands | 7 |
| Route sinuosity bands | 4 |
| Traffic incident types with a minimum zoom | 9 |
| Navigation road sign size classes | 5 |
| Shield style size classes | 5, each at 1× and 2× |
| Ground settings zoom entries | 24 (20 levels, 4 low-zoom ranges) |
| Climate classes | 4 |
| Tile selection strategies | 4 |
| Precompiled shader libraries | 2 (~3 MB, ~60 KB) |

## 6 Rationale

The dominant idea is that almost nothing about appearance is in the code. The
stylesheet decides which features exist at which zoom, how labels are sized,
how wide a traffic pill is, how far ahead a maneuver is drawn, and how a curve
is classified for drawing. The tile decides where labels prefer to sit and what
languages they come in. Two JSON documents decide how much terrain relief is
exaggerated and how desert ground is tinted. The renderer is a machine for
executing those decisions.

The cost of that is the stylesheet format. Bit-packing every count to its
minimum width, with the widths themselves written into the file, is only worth
doing for an artifact that is both large and shipped constantly — and the fact
that it was done tells you the stylesheet is on the hot path of the update
system, not a build-time constant.

Compiling selectors into a matching graph rather than evaluating a rule list is
the same trade in a different place. Map features arrive by the hundred thousand
per frame; matching each against a list of rules is not viable, so the match is
compiled to a traversal whose cost depends on the feature, not on how many rules
the cartographers wrote.

Splitting label placement between server and device is the subtlest decision
here. The server has the global context to decide that this park's label belongs
at this point, and the device has the viewport. Shipping placement metadata in
the tile and refining it on device gets both, at the cost of a chapter and a
format commitment. It is also why labels are stable as you pan: the preferred
position was decided once, not recomputed from what happens to be on screen.

The per-frame budgets and background label layout are the admission that none of
this fits in a frame. The renderer is built to be *late* in controlled ways —
entities update over several frames, labels settle after the camera stops — and
to be late in places a person does not notice rather than places they do.

## 7 Design takeaways

**09#T1.** Put appearance in data and ship the data. If a designer cannot change
a width, a zoom threshold or a colour without a release, your release cadence is
your design cadence.

**09#T2.** Compile your style language. The authored form and the shipped form do
not have to be the same artifact, and the shipped one should be optimised for
the decoder, not the author.

**09#T3.** Compile selectors into a matching graph. A rule list costs
O(rules) per object; a traversal costs O(attributes). At map-feature volumes
that is the difference between viable and not.

**09#T4.** Let device state participate in selector matching. Night, navigation
and selection as *client attributes* keep conditional appearance in the
stylesheet instead of scattering it through render code.

**09#T5.** Chapter your container and compress per chapter. A consumer that
needs labels should not pay to decompress building meshes.

**09#T6.** Precompute what needs global context, refine what needs local
context. Label positions are the canonical example: the server knows the region,
the device knows the viewport, and neither can do the other's half.

**09#T7.** Separate the text from the thing it labels. One tile then serves
every language, and the language becomes a draw-time choice.

**09#T8.** Give global rules a local override. A per-tile minimum-zoom override
is how one stylesheet serves both Tokyo and open desert.

**09#T9.** Add a type rather than versioning one, when old clients must keep
working. Parallel `_V2` data types let two formats coexist in one pyramid.

**09#T10.** Separate the stable skeleton from the volatile values painted on it.
Traffic geometry and traffic levels have different refresh rates and should not
share a cache entry.

**09#T11.** Build the pass graph per frame. Which passes exist depends on what
is on screen; a fixed pipeline with disabled stages pays for what it does not
draw.

**09#T12.** Budget per-frame work explicitly and spread the rest. A visible
amortisation beats an invisible hitch.

**09#T13.** Choose where to be late. Labels settling after a pan is a decision;
a dropped frame during one is not.

**09#T14.** Specialise shaders with function constants rather than branching.
One source, many pipeline states, no runtime cost for the variants you did not
take.

**09#T15.** Exaggerate on purpose, and put the exaggeration in a file. Terrain
relief that is honest at every zoom is useless at most of them; the
zoom-indexed scale factor is the whole mechanism, and it is eleven lines of JSON.

## 8 Uncertainties

- This file describes structure, not algorithms. Tessellation, geometry
  simplification, the actual collision test, the camera controller's behaviour
  and the draping of flat geometry onto terrain are all named and none is
  specified.
- The attribute traversal order in 4.2 is asserted to exist, not established.
- The relationship between the matching graph's chunks and end chains is not
  understood; both are observed in the format and neither is explained.
- The stylesheet's property *identifiers* were not recovered — only the global
  properties, which are named in the decoder's diagnostics. The per-feature
  property vocabulary is therefore unknown.
- The source style language does not ship and nothing here describes it.
- Mode identities (R44) are inferred from the raster and vector data type names,
  not read from the stylesheet.
- The two generations of style attribute raster are observed; what differs
  between them is unknown.
- How the two 3D imagery generations are selected between at runtime is unknown.
- The shield style resource format was not decoded; only its size classes.
- Whether the legacy render path is still reachable in shipping configurations
  was not determined.
- Nothing here is observed at runtime. Every pass ordering in 4.1 is inferred
  from names and dependencies, and the real frame graph is built from data this
  method cannot see.

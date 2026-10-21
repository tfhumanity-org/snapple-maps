# 06 — Feedback and contributions

## 1 Purpose & scope

How a user corrects the map, rates a place, adds a photo, or reports an
incident — and how that reaches Apple without identifying them. Covers the
feedback model, the contributions service, anonymous attestation, and the
submission lifecycle.

Not covered: moderation, or what happens to a submission after it arrives.

## 2 Concepts

**Report a problem** is the correction path: this road is one-way, this place
has closed, this address is wrong.

**Contribution** is the additive path: ratings, photos, place enrichment.

**A community identifier** is a contributor identity held in the sync store
(`05#R10`), distinct from the user's Apple Account.

**Anonymous attestation** is a certificate proving the submission comes from a
genuine device, without saying which one.

## 3 Requirements

### 3.1 Scale and shape

**R01 (observed).** The feedback model MUST be substantial: 103 of the 334
service-framework classes the app binds (`00#R07`) belong to it, and the app
carries a further 126 contribution-related Objective-C names of its own — 93
classes and 33 delegate protocols.

**R02 (derived).** Feedback MUST therefore be read as a first-class subsystem
of comparable weight to search or routing, not a bolted-on form. Close to a
third of the app's binding against its principal framework is feedback.

**R03 (observed).** Feedback MUST be structured as a common envelope plus a
per-surface correction type. Observed surfaces, each with its own feedback and
corrections types:

| Surface | Corrects |
|---|---|
| Point of interest | A place's details |
| Address | An address |
| Directions | A route or its instructions |
| Search | A search result set |
| Street | Road attributes |
| Locality | A place name or boundary |
| Transit point of interest | Transit-specific place details |
| Ground-level imagery | Street-level imagery |
| Curated collection | A guide |
| Point-of-interest image | A submitted photo |
| Incident | A traffic incident |

**R04 (observed).** A common context and common corrections type MUST exist
alongside the per-surface ones, carrying what every submission needs.

**R05 (observed).** Specific correction types MUST exist for: a corrected
coordinate; a corrected label; a corrected search; an edited access point;
business hours; address fields; and instruction corrections.

**R06 (derived).** A dedicated *instruction correction* type MUST be read as
guidance phrasing being correctable independently of the road data that produced
it — "the sign says Exit 14B, you said Exit 14" is a different report from "this
turn is wrong".

### 3.2 Server-driven forms

**R07 (observed).** Feedback forms MUST be server-driven: a dynamic form type
exists, with layout form configuration, layout configuration parameters, and
component query parameters.

**R08 (derived).** This is the same client-ships-shapes pattern as `03#T1`. A
new correction field, or a different question order for a different country, is
a server change.

**R09 (observed).** Query parameters MUST be separable into feedback query
parameters, request parameters, submission parameters and component query
parameters — four distinct parameter objects.

**R10 (derived).** Separating *request* from *submission* parameters MUST be
read as a two-phase interaction: the client asks what to collect, then sends
what it collected.

### 3.3 Identity and attestation

**R11 (observed).** Submissions MUST be able to carry anonymous attestation
certificates, held alongside an anonymous signature, and the client distinguishes
an anonymous identifier, an anonymous user identifier and an anonymous session
identifier.

**R12 (observed).** Attestation certificate handling MUST be governed by two
separate flags: whether to cache certificates for community-identifier write
requests, and whether to send them.

**R13 (derived).** Separate cache and send flags MUST be read as attestation
being rollable out and back independently of certificate acquisition — the
client can be collecting certificates before it starts attaching them.

**R14 (observed).** A submission MUST be able to fail specifically because
attestation failed, and separately because attestation was not found. These are
distinct states.

**R15 (observed).** The contributor identity MUST be a community identifier
stored in the sync store, with an anonymous credential stored beside it
(`05#R10`).

**R16 (derived).** A synced anonymous credential MUST be read as contributor
continuity across the user's devices without the contribution carrying an
account identity — the user's reputation follows them, the submission does not
name them.

**R17 (observed).** A de-anonymisation field MUST exist in the wire vocabulary.

**R18 (inferred).** That field is most plausibly a user-initiated opt-in —
attaching a name to a review — rather than a server capability. This was not
confirmed and should not be relied on.

**R19 (observed).** The app MUST carry an informed-consent presentation and a
community-acknowledgement presentation with options, as distinct UI surfaces.

**R20 (derived).** A separate informed-consent surface MUST be read as
contribution being an explicit opt-in with a stated scope, not a side effect of
using the app.

### 3.4 The contributions service

**R21 (observed).** Contributions MUST be handled by a dedicated service, on its
own host family, reached over HTTPS and separate from the main map services.

**R22 (observed).** That service MUST be addressable in four environments —
production, staging, QA and development — selected by hostname.

**R23 (observed).** The service MUST be used at least to: fetch submission state
by submission identifier; update photo attribution preferences; and carry
general submission traffic.

**R24 (observed).** Submission status MUST be synchronised by the push daemon
(`00#R11`), not polled by the app.

**R25 (derived).** Status synchronisation living in the push daemon MUST be read
as submissions being long-lived: a correction may be adjudicated days later, and
the result arrives whether or not the app is running.

**R26 (observed).** Notifications about submissions MUST exist as a modelled
type with their own log events, and the app MUST be able to be opened to a
submission by a private URL scheme (`08`).

**R27 (observed).** Problem status MUST be a first-class request and response
pair, independent of the submission itself.

### 3.5 Photos

**R28 (observed).** Photo submission MUST carry image upload parameters and
return an upload result, modelled separately from the feedback envelope.

**R29 (observed).** Photo metadata and client image information MUST be modelled
separately from the image itself.

**R30 (observed).** Photo attribution preferences MUST be user-controllable,
with a preferences type and an explicit update type.

**R31 (observed).** Third-party photo sharing MUST be a separate preference with
its own update type.

**R32 (derived).** Two independent photo preferences — how you are credited, and
whether your photo may be shared onward — MUST be read as consent being
unbundled: agreeing to contribute a photo is not agreeing to it appearing
elsewhere.

**R33 (observed).** The app MUST support browsing nearby and additional photos
as a feed, with availability checks before offering to add one.

### 3.6 Ratings and enrichment

**R34 (observed).** Ratings MUST be modelled as a rating value with category
ratings, and a scorecard with its own update type.

**R35 (inferred).** The scorecard is most plausibly the contributor's own
standing — how many submissions, how many accepted. Not confirmed.

**R36 (observed).** Place enrichment MUST exist as a distinct contribution kind,
with an enrichment update, an enrichment image, and a place context, surfaced
inline on the place card rather than through the correction flow.

**R37 (derived).** Inline enrichment MUST be read as a deliberately lower-friction
path than report-a-problem: "is there outdoor seating?" asked in place, versus a
form.

**R38 (observed).** A fraud notification parameter set MUST exist in the
feedback vocabulary.

**R39 (observed).** Feedback MUST be collectible for navigation specifically,
with a directions feedback collector, and distinct feedback types for spoken
guidance, sign guidance, junction views, steps, electric-vehicle steps and
traffic reroutes.

**R40 (derived).** Per-guidance-element feedback types MUST be read as the
navigation feedback path being automatic or near-automatic rather than a form —
these are the units a system would report on itself, not ones a user would
choose between.

**R41 (observed).** A visible tile set MUST be part of the feedback vocabulary.

**R42 (derived).** Submitting what was on screen MUST be read as giving the
report its context: a complaint about a missing road is answerable only if you
know which data the user was looking at.

## 4 Algorithms

### 4.1 Making a correction

```
user chooses "report an issue" on some surface:

    surface  <- point of interest | address | directions | search | street |
                locality | transit | ground imagery | collection | image |
                incident

    form     <- request the dynamic form for (surface, place, locale, country)
                # layout, fields and order are server-authored

    present the form
    if the user has not contributed before:
        present informed consent; stop if declined

    corrections <- the per-surface corrections object the form produced
    context     <- common context + per-surface context
                   + the visible tile set at the time of the report

    if sending attestation certificates is enabled:
        certificates <- cached certificates, or acquire them
        if none:
            fail with "attestation not found"
        attach certificates and signature

    submit(corrections, context, community identifier)
       -> submission identifier

    record a report record in the sync store, so the user's other
    devices know they reported it
```

### 4.2 Learning the outcome

```
the push daemon receives a submission status change:
    fetch status for the affected submission identifiers
      from the contributions service
    update the stored server evaluation status in the sync store
    if the status warrants telling the user:
        post a notification
        tapping it opens the app by private URL scheme to that submission
```

The app is not involved. A correction submitted and then never reopened still
gets its answer.

## 5 Constants

| Constant | Value |
|---|---|
| Feedback classes bound from the service framework | 103 of 334 |
| Contribution names in the app | 126 (93 classes, 33 protocols) |
| Feedback surfaces | 11 observed |
| Parameter objects | 4 (query, request, submission, component query) |
| Service environments | 4 (production, staging, QA, development) |
| Independent photo consents | 2 (attribution, third-party sharing) |

## 6 Rationale

The weight of this subsystem is the finding. Close to a third of the app's
binding against its principal framework, and 126 contribution-related names of
its own, is not a feedback form — it is a crowdsourcing platform with a map in front of it.

The identity design is the interesting part. There are three identities in play:
the Apple Account, which the submission never carries; a community identifier,
which gives a contributor continuity and syncs across their devices; and an
attestation certificate, which proves a real device without naming it. Together
they let Apple rate-limit, reputation-score and reject fraudulent contributions
without being able to attribute one to a person. The two separate flags around
certificate handling, and the distinct "attestation not found" failure, show a
mechanism that was rolled out carefully.

The navigation feedback types are the giveaway for a second, quieter path.
Nobody chooses "junction view feedback" from a menu. Those types exist so the
system can report on its own guidance, with the visible tile set attached, which
is how a routing error becomes reproducible against the data that caused it.

## 7 Design takeaways

**06#T1.** Separate the identity that gives continuity from the identity that
proves authenticity, and let neither be the account. Reputation and anti-abuse
do not require knowing who someone is.

**06#T2.** Split "acquire the credential" from "send the credential" behind two
flags. You will want to deploy the first long before the second.

**06#T3.** Make "attestation missing" a different failure from "attestation
rejected". One is a client problem you can retry; the other is not.

**06#T4.** Drive the form from the server. Correction fields differ by country,
by surface and by what the data team currently needs; none of that should wait
on a release.

**06#T5.** Ask what to collect, then send it. Two phases let the server decline
to ask for something it cannot currently use.

**06#T6.** Attach the context the user saw. A report about missing data is
unactionable without knowing which data was on screen.

**06#T7.** Unbundle consent. "Credit me" and "share this onward" are different
questions and deserve different switches.

**06#T8.** Deliver outcomes through the daemon, not the app. A submission
adjudicated three days later should still reach the user.

**06#T9.** Give your own system a feedback channel with the same plumbing as the
user's. Per-element guidance feedback is how a routing team finds out that an
instruction is wrong before a user bothers to say so.

## 8 Uncertainties

- The scorecard's meaning (R35) and the de-anonymisation field's purpose (R18)
  are both inferred.
- The attestation scheme is identified by its abbreviation in the shipped
  vocabulary; the underlying cryptographic construction was not determined, and
  nothing here should be read as a claim about its unlinkability properties.
- Whether navigation feedback is automatic, prompted, or opt-in is not
  established; R40 is an inference from the shape of the types.
- The fraud notification parameters' trigger and effect are unknown.
- How submissions are rate-limited is not visible; the throttle document (`01`)
  has no entry for them.
- The relationship between the contributions service and the main map services —
  whether a submission also reaches the latter — was not traced.
- Nothing here establishes retention: how long a submission, its photos or its
  status are kept.

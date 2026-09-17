# Portrait attractiveness for men — scene-direction research

Research pass for writing text-to-image scene prompts for an **identity-locked** portrait
generator (Nano Banana Pro via the Gemini app, this repo's `facecard.py`). Face, bone
structure, and hair come from pinned reference photos and are never described in prompt
text (see `prompts/identity_lock.txt`). Every finding below is filtered to what lives
entirely in **scene direction** — lighting setup, camera geometry, posture, expression
coaching, clothing fit, and framing — i.e., things a real photographer/stylist could tell
a real person to do without touching their face.

Evidence is tiered on purpose:
- **[Craft]** = professional photography/styling practitioner consensus (not peer-reviewed,
  but this is the accepted body of technique real photographers and tailors use).
- **[Research]** = peer-reviewed psychology/vision-science, cited with authors/year/journal.
- Where the research is genuinely contested or contradicts the craft convention, that's
  called out explicitly rather than flattened into a false-confidence tip — see
  **§8 Key tensions** especially for camera/head angle.

---

## 1. Lighting

### 1.1 Light position patterns (the four classic setups)

| Pattern | Horizontal angle from camera axis | Vertical position | Signature | Effect |
|---|---|---|---|---|
| **Loop** | 30–45° (some sources: 25–50°) | Slightly above the subject's eye level | Small comma-shaped nose-shadow "loop" on the cheek, not touching the cheek shadow | Balanced, flattering, the default for corporate/headshot work |
| **Rembrandt** | ~45°, pushed further around than loop | Raised above eye level (enough that the nose shadow drops far) | Nose shadow and cheek shadow *merge*, leaving an isolated triangle of light on the far cheek/under the eye | More dramatic/moody; strong jaw and cheekbone modeling |
| **Short lighting** | Light illuminates the side of the face turned **away** from camera | — | Shadow falls on the near side of the face | Slims and sculpts the face — the standard choice for a leaner, more masculine, more dramatic read |
| **Broad lighting** | Light illuminates the side of the face turned **toward** camera | — | Shadow falls on the far side, mostly hidden | Widens/flattens the face, fills more texture — softer, more "commercial," reads less masculine |

Sources: [Rembrandt Lighting in Portrait Photography – Skylum](https://skylum.com/blog/rembrandt-lighting-in-photography), [What Is Rembrandt Lighting – ProEDU](https://proedu.com/blogs/news/what-is-rembrandt-lighting-free-photography-tutorial), [Rembrandt lighting setup – The Lens Lounge](https://thelenslounge.com/rembrandt-lighting-setup/), [5 Common Key Light Patterns – SLR Lounge](https://www.slrlounge.com/common-key-light-patterns/), [Rembrandt Lighting – PetaPixel](https://petapixel.com/rembrandt-lighting/).

**Avoid for a masculine read:** butterfly/paramount lighting (light high and centered on the
camera axis, ~45–60° above eye line, producing a symmetrical shadow directly under the nose)
and clamshell lighting (key above + reflector/fill directly below the face). Both are the
industry-standard *beauty/glamour* setups precisely because they erase jaw and cheekbone
shadow — the opposite of what reads as masculine. **[Craft]** — [Learn Proper Lighting for Men vs. Women – Fstoppers/Phoblographer](https://www.thephoblographer.com/2017/09/18/lighting-men-vs-women-portraits/), [Dramatic lighting for male portraits – Profoto](https://www.profoto.com/int/en/still-photography/tips-tricks/dramatic-lighting-for-male-portrait-photography).

### 1.2 Hard light vs. soft light

- **Hard light** (small/direct/undiffused source — direct sun, bare flash, small window) casts
  crisp, defined shadows and exaggerates every contour: jawline, cheekbones, skin texture,
  stubble. This is the texture that reads as masculine and rugged.
- **Soft light** (large/diffused source — softbox, overcast sky, sheer-curtained window) wraps
  around the face, compresses shadow edges, and smooths skin texture. Flattering but can read
  as flat/soft if used alone.
- Practical middle ground for "attractive but masculine": a **moderately soft key light held
  at a hard-light angle** (i.e., don't fully wrap the light around the face) — soft enough not
  to look harsh/unflattering, but still angled steeply enough to leave real jaw/cheekbone
  shadow rather than flooding it out.

**[Craft]** — [Introduction to Portrait Lighting – Cambridge in Colour](https://www.cambridgeincolour.com/tutorials/portrait-lighting.htm), [Portrait Lighting Basics – GVM](https://shop.gvmled.com/blogs/blog-posts/portrait-lighting-basics-flattering-light-for-every-face).

### 1.3 Lighting ratio (contrast between lit and shadow side)

The key\:fill ratio controls how deep the shadow side of the face goes:
- **~2:1** (one stop difference) — soft, low-contrast, "commercial/beauty" look. Shadows are
  barely visible.
- **~4:1 or greater** (two-plus stops difference) — dramatic, higher-contrast, defined shadow
  edge. This is the ratio associated with masculine/character portraiture and low-key
  lighting.

For a masculine-but-attractive target, bias toward **4:1** rather than 2:1 — enough shadow to
carve the face, not so much that detail is lost. **[Craft]** — [Lighting Ratio in Photography – GVM](https://gvmled.com/photography-lighting-ratio-guide/), [Profoto: Dramatic lighting for male portraits](https://www.profoto.com/int/en/still-photography/tips-tricks/dramatic-lighting-for-male-portrait-photography).

### 1.4 Color temperature

| Range | Character | Use |
|---|---|---|
| **2700–3500 K** | Warm, orange/amber, "golden hour"/tungsten | Flattering to skin tone, cozy, intimate — most portrait photographers bias a few hundred K warmer than "accurate" specifically because warm light flatters skin |
| **5000–5500 K** | Neutral daylight | The commonly cited "ideal neutral" portrait range |
| **5500–5800 K+** | Slightly cool | Clean, crisp, "editorial" look |
| **>6500 K / uncorrected fluorescent** | Cool, blue/green cast | Reads as clinical/unflattering — avoid |

**[Craft]** — [Color Temperature in Photography – PhotoWorkout](https://www.photoworkout.com/color-temperature-in-photography/), [Best color temperature for portraits – The Lens Lounge](https://thelenslounge.com/best-color-temperature-for-portrait-photography/), [The Art of Color Temperature in Portrait Photography](https://www.numberanalytics.com/blog/color-temperature-portrait-photography-techniques). Warm light's comfort/relaxation association also has experimental backing (NCBI-indexed research on 2700–3000 K perceived comfort, as summarized in the PhotoWorkout piece above).

### 1.5 Catchlights

A catchlight is the point reflection of the light source in the eye. Position the key light
**in front of and slightly above** the subject so the reflection lands between the **10 and 2
o'clock positions** of the eye (clock face centered on the pupil). Without a catchlight, eyes
read as dull/dead; with one, they read as alive and engaged — photographers treat this as
essentially mandatory (cited as relevant in ~90% of portrait setups). **[Craft]** — [Catchlights: How to Make the Eyes Sparkle – iPhotography](https://www.iphotography.com/blog/catchlights/), [How to create catchlights – The Lens Lounge](https://thelenslounge.com/catchlights-in-photography/).

### Translating §1 into prompt language

"Soft directional key light from camera-left at roughly a 45-degree angle, positioned above
eye level, warm golden-hour color temperature, visible catchlight in both eyes, moderate
shadow on the opposite side of the face for dimension" is a legitimate, specific scene
direction — no face description required.

---

## 2. Camera angle and height

### 2.1 The baseline convention: low angle reads as powerful, high angle reads as weak

Cinematography's long-standing convention: a **camera positioned below the subject's eye
line, tilted up** ("low-angle shot") makes the subject read as larger, more dominant, more
powerful. A camera **above the eye line, tilted down** ("high-angle shot") makes the subject
read as smaller, weaker, more vulnerable. This is treated as settled craft knowledge — see
the general framing in [Low-angle shot – Wikipedia](https://en.wikipedia.org/wiki/Low-angle_shot)
and practitioner summaries at [The Psychology of Camera Angles – PhotoWorkout](https://www.photoworkout.com/camera-angles/)
and [Camera Angles That Make Characters Appear Powerful – LensViewing](https://lensviewing.com/which-camera-angle-makes-the-character-appear-powerful-and-dominant/).
(One frequently repeated statistic — "low angle increases perceived importance by up to
30%, per a USC study" — could not be traced back to an identifiable primary study in this
pass; treat it as unverified folk-repetition, not as data.)

### 2.2 The real-world complication

A 2023 peer-reviewed study on videoconferencing found the relationship is not simple:
when both parties' cameras were on, the person shot from a **low** angle was rated **less**
powerful than when shot from a high angle — the opposite of the film-theory prediction —
while camera angle had no effect when only one party's camera was active. The authors
conclude other factors (mutual gaze, context, individual differences) interact with angle.
**[Research]** — [The impact of camera usage and angle on perceptions of power during videoconferencing, *Computers in Human Behavior Reports*, 10 (2023)](https://www.sciencedirect.com/science/article/pii/S2451958823000180).
Practical takeaway: the low-angle-equals-power effect is real but not unconditional — it
interacts with context, so treat "shoot from slightly below eye level" as a moderate lever,
not a guaranteed one.

### 2.3 Head pitch (chin up/down) and dominance — a genuinely contested research area

This is distinct from *camera* height (§2.1–2.2, where the subject's head stays level and the
camera moves) — this is about tilting the subject's **head/chin** up or down. The literature
does not agree on direction, and a prompt-writer should know that rather than get a
false-confidence rule:

- **Mignault & Chaudhuri (2003)**, *Journal of Nonverbal Behavior*, 27(2), 111–132 — using 3D
  face models pitched up or down, dominance ratings rose with **upward** pitch and fell
  (read as submissive) with **downward** pitch. They frame this as an evolutionary
  head-raise/head-lower dominance-submission signal shared with other social species.
  [DOI: 10.1023/A:1023914509763](https://link.springer.com/article/10.1023/A:1023914509763)
- **Witkower & Tracy (2019)**, *Psychological Science*, 30(6), 893–906 — found the **opposite**
  direction for a neutral face: downward head tilt increased perceived dominance. Their
  mechanism is a visual illusion, not a real expression change — tilting the head down makes
  neutral eyebrows *look* lowered and V-shaped (the anatomical geometry of the brow relative
  to the tilted face mimics an anger/aggression brow), and that illusory brow shape is what
  reads as dominant, not the tilt itself. [DOI: 10.1177/0956797619838762](https://doi.org/10.1177/0956797619838762)
- **Marshall, Bartolacci & Burke (2020)**, *Evolutionary Psychology*, 18(1) — tested continuous
  pitch from −15° to +15°: **upward** pitch produced a linear increase in both **masculinity**
  and **social dominance** ratings (and a matching decrease in femininity), while **downward**
  pitch produced higher **attractiveness** ratings, peaking at the most extreme downward angle
  tested (−15°), with the effect strongest on female faces.
  [DOI: 10.1177/1474704920910403](https://doi.org/10.1177/1474704920910403)

**The tension that matters for this project:** the one study that isolated attractiveness
specifically (Marshall et al.) found downward pitch is the more "attractive" direction but
the less masculine/dominant one — upward pitch is more masculine but was not the
attractiveness-maximizing direction. There is no single head-pitch angle in the literature
that simultaneously maximizes both. Practical resolution used below in §8: keep head pitch
close to neutral-to-very-slightly-up (masculine side of neutral, not a deep downward nod),
and get the "flattering" benefit from camera height and the Hurley jaw technique (§3.7)
instead of from a large downward head pitch — those operate on different mechanisms
(silhouette/shadow vs. the brow-angle illusion) and don't fight each other the way two
different head-pitch recommendations would.

### 2.4 Phone-specific lens distortion (directly relevant to a phone-camera candid style)

A phone's main/selfie camera is a wide-angle lens (typically ~24–28mm full-frame equivalent).
At close distance this measurably distorts facial proportions — not folklore, a measured
optical effect:

> A selfie taken at ~12 inches from the face makes the nasal base appear **~30% wider** and
> the nasal tip **~7% wider** than the same face photographed from 5 feet (standard portrait
> distance).

**[Research]** — Ward, B., Ward, M., Fried, O., & Paskhover, B. (2018). "Nasal Distortion in
Short-Distance Photographs: The Selfie Effect." *JAMA Facial Plastic Surgery*, 20(4), 333–335.
[DOI: 10.1001/jamafacial.2018.0009](https://pubmed.ncbi.nlm.nih.gov/29494735/) — also covered
in [Rutgers University's research summary](https://www.rutgers.edu/news/selfies-drive-self-image-and-may-lead-many-seek-plastic-surgery).

Practical rule for a "phone-camera" prompt: specify **more camera-to-subject distance plus
a longer/zoomed framing** rather than a close wide shot — i.e., direct it like a
35mm-135mm-equivalent portrait lens result (see §7.4), not a 12-inch arm's-length selfie,
even when the brief calls for a "candid phone photo" look.

### 2.5 Practical synthesis for camera geometry

- Camera height: **at or slightly below the subject's eye line**, not above it (avoids the
  high-angle "diminishing" read, gets a mild version of the low-angle "power" read without
  going so low that a wide phone lens starts distorting the jaw/nostrils).
- Head pitch: **neutral to very slightly up** — do not direct a deep chin-down nod.
- Combine with the Hurley forward-jaw micro-adjustment (§3.7) for jaw definition instead of
  a downward head pitch.

---

## 3. Posture and body language

### 3.1 Shoulder angle: the "universally flattering angle"

Rotate the torso/shoulders **30–45° off the camera's axis** rather than squaring both
shoulders straight at the lens. Photography practitioners call this the "universally
flattering angle": it's slimming, reads as more dynamic/candid, and is less confrontational
than a full frontal square-on stance. The diagonal shoulder line also does compositional work
— a diagonal is inherently more visually engaging than a horizontal line parallel to the
frame edge. **[Craft]** — [The Universally Flattering Angle](https://theartofbeingphotographed.com/posing-tips-the-universally-flattering-angle/), [Posing Tips for Portraits – Shoulders, Digital Photography School](https://digital-photography-school.com/posing-tips-for-portraits-shoulders/).

### 3.2 Weight distribution (contrapposto)

Shift weight onto one leg (classical *contrapposto*), letting the other knee soften — this
introduces a natural counter-twist between hips and shoulders instead of a stiff, symmetrical
stance.
- Weight on the **back** leg reads softer/more relaxed.
- Weight on the **front** leg reads more aggressive, dramatic, and powerful.
For a masculine-leaning result, front-leg weighting (or a neutral, evenly-balanced stance) is
the better default. **[Craft]** — [Full body portraits: posing, composition, angles – The Lens Lounge](https://thelenslounge.com/full-body-portraits/).

### 3.3 Postural expansiveness/openness — the strongest attraction evidence in this section

This is the best-evidenced single body-language finding for attraction specifically, because
it comes from **field experiments with real behavioral outcomes**, not just observer ratings
of photos:

> Across a **144-person speed-dating field study** and a **3,000-person online-dating field
> experiment**, postural expansiveness (occupying more physical space — open limbs, torso not
> collapsed inward) was the strongest behavioral predictor of romantic interest. Each
> one-unit increase in coded expansiveness nearly **doubled** the odds of getting a "yes."
> Causally manipulating a profile photo from a contracted to an expansive posture nearly
> doubled positive response rates.

**[Research]** — Vacharkulksemsuk, T., Reit, E., Khambatta, P., Eastwick, P. W., Finkel, E. J.,
& Carney, D. R. (2016). "Dominant, open nonverbal displays are attractive at
zero-acquaintance." *PNAS*, 113(15), 4009–4014. [DOI: 10.1073/pnas.1508932113](https://www.pnas.org/doi/10.1073/pnas.1508932113).

Practical direction: an **open** stance — shoulders not hunched, arms not fully crossed
in front of the torso, some visible space between arms and body (e.g., a hand in a pocket
with the elbow out, or one arm resting on a surface) — outperforms a closed/contracted
stance for attraction specifically, independent of the dominance angle covered next.

### 3.4 What to keep — and not keep — from "power posing"

Amy Cuddy's original claim (Carney, Cuddy & Yap, 2010, *Psychological Science*) was that
holding an expansive pose for two minutes changes the poser's own **testosterone/cortisol**
and felt power. That specific hormonal/behavioral claim **failed to replicate** in a
higher-powered study — [Ranehill et al. (2015)](https://scienceblog.com/g-body-language-that-makes-a-person-seem-powerful/),
with 200 participants, found no hormone or risk-taking effect — and Dana Carney (the
original paper's lead author) publicly stated in 2016 that she no longer believes the effect
is real. A 2018 p-curve re-analysis of 55 studies (Cuddy, Schultz, & Fosse) argued there is
still evidential value for posture affecting the *poser's own felt sense of power*, but that
is a different question from ours.

**Why this mostly doesn't matter for a still image:** everything in this project is about how
a **viewer perceives a photo**, not about the subject's internal hormone levels. The
observer-perception evidence — §3.3's field data, and the dominance-perception meta-analysis
below — is separate from the debunked hormonal claim and is not undermined by that
replication failure. Don't import "power posing is debunked" as a reason to discard open
posture; the debunked part is the hormones, not the perception.

### 3.5 Nonverbal dominance cues (meta-analytic)

**[Research]** — Hall, J. A., Coats, E. J., & LeBeau, L. S. (2005). "Nonverbal Behavior and the
Vertical Dimension of Social Relations: A Meta-Analysis." *Psychological Bulletin*, 131(6),
898–924. Upright posture, an upright/raised head, and wide/expansive gestures were the
nonverbal cues most consistently coded as dominant across the studies reviewed. Notably, the
meta-analysis also found that people's *beliefs* about which cues signal power are more
consistent and stronger than the actual behavioral differences measured in genuinely
high-power people — which, for a directed photo, is a feature: we only need the cue to be
legible to a viewer, not biologically authentic.

### 3.6 Hand placement

- **Hands in pockets, thumbs left outside the pocket opening** is the most commonly
  recommended default for a casual-but-composed male pose: it reads as relaxed and confident,
  keeps elbows slightly bent (avoiding a stiff straight-arm silhouette), and the visible thumb
  keeps the pose from reading as hidden/closed-off.
- Fully crossed arms read as authoritative but also closed-off — in tension with the
  openness finding in §3.3. If the goal is confident *and* approachable/attractive rather
  than purely authoritative, prefer the pockets-with-thumbs-out version over crossed arms.

**[Craft]** — [Hands in Pockets Body Language – The Power Moves](https://thepowermoves.com/hands-in-pockets/), [25 Best Male Poses – ExpertPhotography](https://expertphotography.com/photographers-guide-posing-men-portraits).

### 3.7 The jaw/chin "forward-and-down" technique (Peter Hurley method)

Headshot photographer Peter Hurley's widely taught fix for a defined jawline and no double
chin is **not** "stick your chin out." His own instruction: *"jam your forehead towards the
camera and allow the chin to follow, tightening the skin against your jawline"* — i.e.,
project the crown/forehead forward first, and let the chin trail rather than leading with an
upward jut. **[Craft, primary source]** — [Peter Hurley: It's All About The Jawline – Scott Kelby's Photoshop Insider](https://scottkelby.com/its-guest-blog-wednesday-featuring-peter-hurley/), also documented at [Rangefinder](https://rangefinderonline.com/news-features/tips-techniques/peter-hurley-squinched-our-staff-2/) and [Fstoppers](https://fstoppers.com/portraits/peter-hurleys-squinch-helps-make-better-headshots-8556).

**Why it works (mechanism):** the underside of the jaw is covered by loose skin and the thin
platysma sheet muscle running from the collarbone up to the jawline and lower face. When that
region is slack, it folds and reads as a "double chin" regardless of actual body fat. Pushing
the crown of the head forward (not up, not down — forward, toward the camera) stretches this
skin/muscle sheet taut against the underlying jaw bone before the chin is allowed to settle
back down, so the visible edge becomes the bone (mandible) rather than the loose tissue
drooping below it. This is a mechanical/anatomical result of tautening slack tissue over
bone, distinct from and compatible with whatever the camera height and head-pitch decisions
in §2 are doing — it's a small local adjustment, not a head-pitch change, so it doesn't
conflict with keeping head pitch near-neutral per §2.5.

---

## 4. Expression

### 4.1 The Duchenne smile: exact muscle mechanics

Every smile involves the **zygomaticus major** (pulls the lip corners up and out, toward the
ears). What makes a smile a "Duchenne smile" specifically is the **added** contraction of the
**orbicularis oculi, pars orbitalis** — the muscle ring around the eye — which raises the
cheeks, narrows the eye aperture, and produces the crow's-feet wrinkling at the outer eye
corner. A smile with mouth movement only, and no eye-muscle involvement, is the "non-Duchenne"
or social/polite smile.

**[Research]** — Ekman, P., Davidson, R. J., & Friesen, W. V. (1990). "The Duchenne Smile:
Emotional Expression and Brain Physiology II." *Journal of Personality and Social Psychology*,
58(2), 342–353. Recorded facial action, EEG, and self-reported emotion while subjects watched
pleasant vs. unpleasant films; the Duchenne configuration tracked with pleasant-film viewing,
positive self-report, and left-frontal EEG asymmetry (the brain's positive-affect signature),
while non-Duchenne smiling did not track any of those. [PDF via APA/PsycNet](https://psycnet.apa.org/fulltext/1990-14081-001.pdf?sr=1).

### 4.2 Why the Duchenne configuration reads as more attractive to a viewer

A meta-analysis of studies asking observers to rate Duchenne vs. non-Duchenne smiles found
Duchenne smiles and the people producing them are rated as **more authentic, genuine,
attractive, and trustworthy**. The gap was larger in video than in still photos, and larger
for naturally elicited smiles than posed ones — but the effect held for photos and posed
smiles too, just at reduced size.

**[Research]** — Gunnery, S. D., & Ruben, M. A. (2016). "Perceptions of Duchenne and
non-Duchenne smiles: A meta-analysis." *Cognition and Emotion*, 30(3), 501–515.
[DOI: 10.1080/02699931.2015.1018817](https://pubmed.ncbi.nlm.nih.gov/25787714/).

### 4.3 It does not have to be a genuinely felt emotion to read as genuine

Important for a directed/generated photo specifically: subsequent research established that
Duchenne smiles **can be deliberately produced** without felt positive emotion, and still
register to observers as more genuine/positive than a non-Duchenne smile — the folk belief
that "you can't fake the eyes" is not fully accurate. What matters for the image is that the
**orbicularis oculi engagement is visibly present** (cheek raise + narrowed eye + crow's-feet),
not that it was caused by real amusement. This directly supports directing the *muscle
configuration* ("cheeks raised, eyes softly crinkled/narrowed at the corners") rather than
something un-directable like "make him genuinely happy."

**[Research]** — this deliberate-production finding is discussed in the Gunnery & Ruben (2016)
meta-analysis above and in the broader literature on posed vs. spontaneous Duchenne
displays (e.g., Krumhuber & Manstead's work on feigned Duchenne smiles, §4.4).

### 4.4 Smile dynamics and intensity (for a still frame)

Dynamic research (video, not stills) found **slow, smooth onset** of a smile reads as more
genuine/positive than an abrupt one, and that perceived genuineness tracks the *duration* of
onset/apex/offset in a graded way rather than a single on/off cutoff.
**[Research]** — Krumhuber, E., & Kappas, A. (2005). "Moving smiles: The role of dynamic
components for the perception of the genuineness of smiles." *Journal of Nonverbal Behavior*.
Symmetry as a genuineness cue is **inconsistent** across studies — early work suggested
spontaneous smiles are more symmetrical, later work found no reliable difference — so it's
not a reliable lever to direct one way or the other.

Since a generated still can't have "onset speed," the actionable takeaway is about
**intensity**: direct a **moderate, settled smile** (cheeks raised, eyes engaged, mouth corners
lifted but not a maximal wide grin) rather than an extreme/frozen-looking full grin, since the
dynamic-genuineness research as a whole associates the *gradual, moderate* version of a smile
with authenticity, and an extreme apex frozen as a still more often reads as posed/artificial.

### 4.5 The "squinch" — lower-eyelid micro-tension

Peter Hurley's second widely taught technique, aimed specifically at the eyes rather than the
mouth. In his own words: *"raise [the lower eyelid] just enough to bring it slightly closer to
your pupil. The upper eyelid barely moves."* This narrows the palpebral fissure (the
eye-opening) **from the bottom**, not by squinting the whole eye. Hurley: *"A subtle squinch
reads as confidence. An aggressive squinch reads as a glare"* — and it should be paired with
an expression "between neutral and a small smile," not a full smile. **[Craft, primary
source]** — [Peter Hurley: Squinch – What It Means and How to Do It](https://peterhurley.com/blog/2013/who-knew-it-really-all-about-squinch), also [Fstoppers](https://fstoppers.com/portraits/peter-hurleys-squinch-helps-make-better-headshots-8556).

**Why it works (physiological grounding):** wide-open eyes with more visible sclera (white of
the eye) are part of the human fear/startle expression — and camera anxiety produces exactly
that involuntary wide-eyed look. Peer-reviewed work on the *function* of fear expressions
found that widened eyes are one part of a configuration (also including flared nostrils and
faster eye movements) that objectively **increases the visual field and sensory intake** —
i.e., wide eyes are literally the face's threat-scanning configuration, while the opposite,
narrowed-eye configuration (as in disgust) reduces sensory intake. **[Research]** — Susskind,
J. M., Lee, D. H., Cusi, A., Feiman, R., Grabski, W., & Anderson, A. K. (2008). "Expressing
fear enhances sensory acquisition." *Nature Neuroscience*, 11(7), 843–850.
[DOI: 10.1038/nn.2138](https://www.nature.com/articles/nn.2138). The squinch works because it
pulls the eye shape *away* from that fear/startle configuration toward a narrower, more
deliberate-looking aperture — reading as calm and focused rather than anxious.

### 4.6 Gaze direction: a real trade-off between trust and attractiveness

- **Direct gaze, front-facing head** produces the **highest trustworthiness** ratings, and
  this "direct gaze bias" holds up across different head orientations. This replicates a
  large older literature (Kleinke, 1986, *Psychological Bulletin*, review of gaze effects on
  person perception).
- **Averted gaze combined with a three-quarter (~45°) head turn** produces the **highest
  attractiveness** ratings when comparing otherwise-equal faces — higher than a straight-on
  pose with direct gaze.
- Head orientation alone did not move trustworthiness ratings much; gaze direction did the
  work for trust, while head angle did the work for attractiveness.

**[Research]** — Kaisler, R. E., & Leder, H. (2017). "Combined Effects of Gaze and Orientation
of Faces on Person Judgments in Social Situations." *Frontiers in Psychology*, 8:259.
[DOI: 10.3389/fpsyg.2017.00259](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.00259/full).

**Practical resolution (also used in §3.1 and §7.5):** these two variables are separable in a
real photo — turn the **body/shoulders** 30–45° off-axis (the flattering, more-attractive
geometry) while keeping the **eyes** directed into the lens (the trust-signaling gaze). This
is the same "shoulders angled, face/eyes to camera" setup photographers already teach for
composition reasons (§3.1), and it turns out to also be the empirically-supported way to get
both benefits at once rather than trading one off against the other.

---

## 5. Grooming-presentation — what's actually usable under an identity lock

This category needs an honest caveat before the findings: most classic "grooming attractiveness"
research (beard length, eyebrow shape, hairstyle) is about **the face and hair themselves** —
exactly the two things this generator locks from the reference photos and must not describe.
Listing that research as if it were usable prompt material would contradict the project's own
constraint. Below is what the research says, followed by what's actually legitimate to direct.

### 5.1 Facial hair and attractiveness (background — mostly NOT usable here)

- **Dixson, B. J., & Brooks, R. C. (2013).** "The role of facial hair in women's perceptions of
  men's attractiveness, health, masculinity and parenting abilities." *Evolution and Human
  Behavior*, 34(4), 236–241. Heavy stubble rated most attractive overall; full beards, light
  stubble, and clean-shaven were rated similarly lower. Perceived masculinity rose
  monotonically with more facial hair, but attractiveness did not — it peaked at heavy
  stubble specifically. Facial hair's attractiveness boost was larger for long-term
  relationship judgments than short-term.
- **Dixson, B. J., et al. (2016).** "The masculinity paradox: facial masculinity and
  beardedness interact to determine women's ratings of men's facial attractiveness." *Journal
  of Evolutionary Biology*, 29(11), 2311–2320. Using computer-morphed faces (8,520 raters):
  making a clean-shaven face more OR less masculine than its natural bone structure both
  *reduced* attractiveness — extremes in either direction were penalized. Adding stubble/beard
  **dampened that penalty**, i.e., facial hair made both more-masculine-than-natural and
  less-masculine-than-natural bone structures read closer to their unmanipulated baseline.
  [DOI: 10.1111/jeb.12958](https://onlinelibrary.wiley.com/doi/10.1111/jeb.12958).

**Why this is mostly off-limits here:** facial hair sits on the jaw/lower face — the same
region the identity lock protects. Directing a different beard/stubble length than what's in
the reference photos would be describing/altering the locked face, which this project's
constraint (and `prompts/identity_lock.txt`) rules out.

**The one legitimate use:** if the reference photos already show a given facial-hair length,
it is fair game to direct its *grooming state* the same way you'd direct a real person to
"clean up" before a shoot — e.g., "neatly trimmed" or "well-groomed" as a maintenance
descriptor of the existing growth, not a request for a different style or length. That is
consistent with how a photographer briefs a real subject who already has that facial hair.

### 5.2 Skin finish: matte vs. shiny (this one is genuinely a lighting/state lever)

Oily skin under hard studio-type light produces visible hotspots, typically on the forehead,
nose, and T-zone. This is standard enough that on-set grooming for men is normally limited to
shine control (blotting, translucent powder) rather than actual makeup. **[Craft]** —
[Camera Ready Grooming Tips for Men](https://camerareadycosmetics.com/blogs/news/top-camera-ready-grooming-tips-for-men), [Oily Skin: How to Appear Shine-Free in Photographs – Garnier](https://www.garnierusa.com/tips-how-tos/oily-skin-how-to-appear-shine-free-in-photographs).

This is directly usable: specifying **"matte skin finish, minimal shine"** or conversely
**"a slight natural sheen"** describes how light interacts with real skin, not a change to
facial structure or texture identity, and is the kind of instruction a director gives a
subject/makeup artist on set. Keep it as a finish/lighting instruction rather than a
retouching instruction (the project's stated policy is "natural skin texture," not airbrushed
skin — see `prompts/studio_test.txt`).

### 5.3 Hair "state" vs. hairstyle (borderline — use narrowly)

Grooming research and practice separate the **cut** (locked here) from its **worn state** —
e.g., a photographer will ask a subject with a fixed haircut to have it "just washed and
combed" vs. "windswept" for different shoots without changing the cut itself. Directing hair
*state* ("neatly combed," "windswept," "damp") for a scene without specifying a different
length, part, or style is closer to directing a real subject's grooming for the shoot than to
altering their identity — but it is inherently closer to the locked attribute than skin finish
is, so use it sparingly and only as a state/weather-consistent descriptor (e.g., "windswept"
for an outdoor/motorcycle scene), not as a styling change.

---

## 6. Clothing fit

### 6.1 Shoulder seam placement — the fit point that matters most

The single most important fit checkpoint on a jacket: the **shoulder seam should end exactly
where the natural shoulder bone ends and the arm begins** — not sitting on top of the deltoid,
not drooping past it onto the upper arm. This is also the one measurement a tailor generally
**cannot fix after the fact**, unlike sleeve length or waist suppression, which is why it's
treated as the top fit priority. **[Craft]** — [Where Should Shoulder Seam Fall? – Tapered Menswear](https://taperedmenswear.com/blogs/tapered-blog/where-should-shoulder-seam-fall), [How a Suit Should Fit – Westwood Hart](https://westwoodhart.com/blogs/westwood-hart/how-suit-should-fit-shoulder-sleeve-trouser-fitting-rules).

### 6.2 Sleeve length

- **Dress shirt cuff:** should end exactly at the wrist bone (the break where hand meets
  wrist).
- **Jacket sleeve over a dress shirt:** should be shorter than the shirt sleeve by design,
  leaving **about 1/4 to 1/2 inch of shirt cuff visible** past the jacket sleeve.

**[Craft]** — [How Jacket Sleeve Length Should Fit – Proper Cloth](https://propercloth.com/reference/how-jacket-sleeve-length-should-fit/), [MasterClass: Measuring Sleeve Length](https://www.masterclass.com/articles/how-to-properly-measure-sleeve-length).

### 6.3 Collar fit — the two-finger rule

Buttoned at the neck, a properly fitted dress-shirt collar allows **two fingers** to slide
between collar and neck comfortably. Fewer than two fingers of room = too tight (visible neck
bulge, strained look); three or more = too loose (collar loses structure and collapses rather
than framing the neck). **[Craft]** — [How Dress Shirts Should Fit – Black Lapel](https://blacklapel.com/blogs/the-compass/how-dress-shirts-should-fit-the-complete-guide), [How a Dress Shirt Collar Should Fit – Hugh & Crye](https://www.hughandcrye.com/pages/how-a-dress-shirt-collar-should-fit).

### 6.4 The V-taper silhouette

A structured/padded shoulder line on a jacket or coat, combined with waist suppression
(tailoring that follows the torso in rather than hanging straight), creates the visual
impression of broader shoulders and a narrower waist regardless of the wearer's actual build.
Structure at the top, room (not tightness) at the waist is the standard formula. **[Craft]** —
[How to Build the Illusion of Broad Shoulders](https://blog.lafitness.com/2020/01/08/how-to-build-the-illusion-of-broad-shoulders/), general menswear silhouette guides on the V-taper.

### 6.5 Color/contrast matched to the (fixed) complexion

Menswear stylist Alan Flusser's widely-taught principle: clothing worn close to the face
should **echo the contrast level already present** between the wearer's skin and hair, not
fight it. A high-contrast face (e.g., dark hair against fair skin) is flattered by
high-contrast combinations near the face (e.g., a crisp white or very light shirt against a
dark jacket); a low-contrast face (skin and hair tones close together) is overpowered by
strong contrast and reads better in more tonally blended combinations. **[Craft]** —
principle attributed to Alan Flusser's *Dressing the Man*, as explained in [Understanding Contrast For Men – Bespoke Unit](https://bespokeunit.com/color/contrast/) and [Understanding Contrast Shirt Color Selection](https://atailoredsuit.com/understanding-contrast-shirt-color-selection.html).

This is a genuinely useful lever *specifically because* the face/complexion is fixed here:
since the reference photos already establish the subject's skin-hair contrast level, the
prompt can reason from that fixed contrast to a matching garment-color contrast without ever
describing the face itself.

---

## 7. Composition and framing

### 7.1 Rule of thirds and eye-line placement

Place the subject's **eye line on or near the upper horizontal third-line** of the frame
(dividing the frame into thirds top-to-bottom). This is the single most consistently taught
portrait composition rule, and it's where most portrait photographers default. **[Craft]** —
[Rule of Thirds in Photography – Digital Photography School](https://digital-photography-school.com/rule-of-thirds/), [Rule of Thirds in Portrait Photography – Bidun Art](https://bidunart.com/rule-of-thirds-in-portrait-photography/).

### 7.2 Headroom

The space between the top of the head and the top of the frame should scale with how tight
the shot is — a tighter crop (closer to the face) needs proportionally less headroom, a wider
shot needs more; too much headroom makes the subject look like they're "sinking," too little
feels cramped. **[Craft]** — [Headroom (photographic framing) – Wikipedia](https://en.wikipedia.org/wiki/Headroom_(photographic_framing)).

### 7.3 Lead room / nose room

Leave **more open space on the side of the frame the subject is facing or looking toward**
than on the side behind their head. This applies directly to the three-quarter-angle pose
recommended in §3.1/§4.6 — if the shoulders/head are turned toward camera-left, the
composition should leave more room on the left than the right, or the shot reads as cramped
and unbalanced. **[Craft]** — [Lead room – Wikipedia](https://en.wikipedia.org/wiki/Lead_room), [What is the Lead Room Principle – ExpertPhotography](https://expertphotography.com/lead-room-principle-photography).

### 7.4 Focal length / camera distance (and why it matters even on a phone)

- **85mm–135mm full-frame-equivalent** is the classic "flattering" portrait range: enough
  telephoto compression to keep facial proportions natural (correct nose-to-ear size ratio)
  without flattening the face into a 2D-looking slab, which starts happening at the longer end
  of that range.
- This requires standing farther back, which is precisely the variable the JAMA selfie-distortion
  study (§2.4) identifies as the actual cause of unflattering wide-lens close-ups — it's
  distance, not "the lens" per se, though phone main/selfie lenses are wide specifically to
  fit a room-scale frame at arm's length, which forces the unflattering close distance.
- **Phone-specific instruction:** favor a **2x–3x zoom framing** (equivalent to stepping back
  and using a longer lens) over a wide-angle close-up, and use "portrait mode" background blur
  to mimic the shallow depth of field a longer lens naturally produces.

**[Craft/Research]** — [85mm Portrait Photography – DIYPhotography](https://www.diyphotography.net/85mm-portrait-lens-guide/), [85mm vs 135mm – Fstoppers](https://fstoppers.com/gear/85mm-versus-135mm-lens-comparison-portraiture-635716); distance effect confirmed by Ward, Ward, Fried & Paskhover (2018), cited fully in §2.4.

### 7.5 Decoupling body angle from gaze direction

As established in §4.6, three-quarter body/head angle maximizes attractiveness ratings while
direct gaze maximizes trust ratings, and these are independently directable — angle the body
and shoulders 30–45° off-axis (§3.1) while keeping the eyes on the lens. Compositionally, this
also naturally creates the lead-room situation in §7.3 (the "far" side of the turned body
becomes the side needing extra room) and the diagonal shoulder line that draws the eye (§3.1).
All three rules reinforce the same physical setup rather than being independent instructions
to reconcile.

---

## 8. Key tensions worth restating

These are the places where "just do the flattering thing" and "just do the masculine/dominant
thing" pull in different directions, gathered in one place since the whole point of this
project is attractive **and** masculine simultaneously:

1. **Head pitch** (§2.3): downward pitch tested as more attractive but less
   masculine/dominant; upward pitch tested as more masculine/dominant. Resolution used
   throughout this document: keep head pitch neutral-to-slightly-up, and get jaw definition
   from the Hurley forward-jaw technique (§3.7, a silhouette effect) rather than from a
   downward pitch (a perception-of-dominance effect) — they're different mechanisms, so using
   one doesn't require giving up the other.
2. **Gaze vs. head/body angle** (§4.6): direct gaze wins trust, three-quarter angle wins
   attractiveness. Resolution: decouple them — angled shoulders/body, eyes still on the lens.
3. **Lighting flatness**: very soft, flat, low-ratio "beauty" lighting (butterfly/clamshell,
   ~2:1 ratio) is objectively more universally flattering/skin-smoothing but reads as
   feminine/commercial; masculine portraiture research and convention favors keeping real
   shadow (short lighting, 4:1+ ratio, harder light quality) even though it's less
   uniformly "flattering" in the beauty-lighting sense (§1.1–1.3).
4. **Camera angle**: low angle reads as powerful per classic film theory, but the one
   controlled peer-reviewed test of this in a realistic setting (videoconferencing) found the
   effect can reverse depending on context (§2.2) — treat "shoot from slightly below eye
   level" as a moderate, not absolute, lever.

---

## 9. Quick-reference cheat sheet

| Lever | Concrete setting | One-line why |
|---|---|---|
| Key light angle | 30–45° horizontal off camera axis, slightly above eye level (loop light) | Sculpts cheekbone/jaw without full Rembrandt drama |
| Light quality | Medium-soft source, hard-light angle | Keeps texture/shadow without harshness |
| Lighting ratio | ~4:1 key:fill | Masculine contrast vs. flat 2:1 beauty lighting |
| Color temperature | 3200–4500 K (warm-neutral) | Flatters skin without going orange or clinical-cool |
| Catchlight | Light source in front/above, reflection at 10–2 o'clock in eye | Eyes read alive, not dead |
| Camera height | At or slightly below eye level | Mild power read; avoids high-angle "diminished" look and phone-lens jaw distortion if too low |
| Head pitch | Neutral to very slightly up | Avoids submissive/feminine read of downward pitch (§2.3) |
| Jaw definition | Crown/forehead projects toward camera, chin follows (not juts up) | Tautens submental skin over jaw bone — Hurley technique |
| Shoulders | 30–45° off camera axis | "Universally flattering angle"; diagonal line reads dynamic |
| Weight | Front leg or neutral, not back-leg-soft | Reads more powerful than a soft back-leg contrapposto |
| Stance/arms | Open — not fully crossed; hand in pocket, thumb out | Openness correlates with attraction in field data (§3.3) |
| Gaze | Direct into lens | Maximizes trust rating |
| Body/head angle | Three-quarter (paired with direct gaze above) | Maximizes attractiveness rating |
| Smile | Moderate zygomaticus lift + visible cheek-raise/eye-crinkle | Duchenne marker reads genuine even if directed, not felt |
| Eyes | Slight lower-lid lift ("squinch"), upper lid relaxed | Moves away from wide-eyed fear/startle configuration |
| Skin finish | "Matte, minimal shine" or "slight natural sheen" as directed | Legitimate lighting/grooming state, not a retouch |
| Shoulder seam | Ends exactly at the shoulder bone | Single most important, least fixable fit point |
| Sleeve | Shirt cuff at wrist bone; ¼–½ inch of cuff shows past jacket sleeve | Standard menswear proportion rule |
| Collar | Two fingers of space, buttoned | Structured without choking |
| Jacket silhouette | Structured shoulder + suppressed waist | V-taper illusion regardless of build |
| Garment contrast | Match contrast level to the fixed skin/hair contrast | Echoes, doesn't fight, the locked complexion |
| Eye-line | Upper third of frame | Standard rule-of-thirds portrait placement |
| Lead room | More space on the side the subject faces/looks toward | Prevents a cramped read on an angled pose |
| Lens/distance | 85–135mm equivalent, or phone 2–3x zoom, not wide-angle close-up | Avoids nose/jaw distortion (measured +30% nasal width at selfie distance) |

---

## 10. Full source list

**Peer-reviewed / academic:**
- Ekman, P., Davidson, R. J., & Friesen, W. V. (1990). The Duchenne smile: Emotional expression and brain physiology II. *Journal of Personality and Social Psychology*, 58(2), 342–353.
- Gunnery, S. D., & Ruben, M. A. (2016). Perceptions of Duchenne and non-Duchenne smiles: A meta-analysis. *Cognition and Emotion*, 30(3), 501–515. https://doi.org/10.1080/02699931.2015.1018817
- Krumhuber, E., & Kappas, A. (2005). Moving smiles: The role of dynamic components for the perception of the genuineness of smiles. *Journal of Nonverbal Behavior*.
- Susskind, J. M., Lee, D. H., Cusi, A., Feiman, R., Grabski, W., & Anderson, A. K. (2008). Expressing fear enhances sensory acquisition. *Nature Neuroscience*, 11(7), 843–850. https://doi.org/10.1038/nn.2138
- Dixson, B. J., & Brooks, R. C. (2013). The role of facial hair in women's perceptions of men's attractiveness, health, masculinity and parenting abilities. *Evolution and Human Behavior*, 34(4), 236–241.
- Dixson, B. J., et al. (2016). The masculinity paradox: facial masculinity and beardedness interact to determine women's ratings of men's facial attractiveness. *Journal of Evolutionary Biology*, 29(11), 2311–2320. https://doi.org/10.1111/jeb.12958
- Ward, B., Ward, M., Fried, O., & Paskhover, B. (2018). Nasal distortion in short-distance photographs: The selfie effect. *JAMA Facial Plastic Surgery*, 20(4), 333–335. https://doi.org/10.1001/jamafacial.2018.0009
- Mignault, A., & Chaudhuri, A. (2003). The many faces of a neutral face: Head tilt and perception of dominance and emotion. *Journal of Nonverbal Behavior*, 27(2), 111–132.
- Witkower, Z., & Tracy, J. L. (2019). A facial-action imposter: How head tilt influences perceptions of dominance from a neutral face. *Psychological Science*, 30(6), 893–906. https://doi.org/10.1177/0956797619838762
- Marshall, P., Bartolacci, A., & Burke, D. (2020). Human face tilt is a dynamic social signal that affects perceptions of dimorphism, attractiveness, and dominance. *Evolutionary Psychology*, 18(1). https://doi.org/10.1177/1474704920910403
- Vacharkulksemsuk, T., Reit, E., Khambatta, P., Eastwick, P. W., Finkel, E. J., & Carney, D. R. (2016). Dominant, open nonverbal displays are attractive at zero-acquaintance. *PNAS*, 113(15), 4009–4014. https://doi.org/10.1073/pnas.1508932113
- Hall, J. A., Coats, E. J., & LeBeau, L. S. (2005). Nonverbal behavior and the vertical dimension of social relations: A meta-analysis. *Psychological Bulletin*, 131(6), 898–924.
- Kaisler, R. E., & Leder, H. (2017). Combined effects of gaze and orientation of faces on person judgments in social situations. *Frontiers in Psychology*, 8:259. https://doi.org/10.3389/fpsyg.2017.00259
- Camera angle/power in videoconferencing (2023). *Computers in Human Behavior Reports*, 10. https://www.sciencedirect.com/science/article/pii/S2451958823000180
- Carney, D. R., Cuddy, A. J. C., & Yap, A. J. (2010) original power-posing study, and Ranehill, E., et al. (2015) failed replication — both discussed in §3.4.

**Professional photography/styling practitioner references:**
- Peter Hurley (headshot photographer) — squinch and jaw-forward technique, https://peterhurley.com
- Skylum, ProEDU, The Lens Lounge, SLR Lounge, PetaPixel, Fstoppers, ExpertPhotography, Cambridge in Colour, Digital Photography School, PhotoWorkout — portrait lighting/posing/composition craft references (linked inline above)
- Proper Cloth, Black Lapel, Hugh & Crye, Tapered Menswear, Westwood Hart, Bespoke Unit — menswear fit/tailoring references (linked inline above); the contrast-matching principle (§6.5) is attributed to Alan Flusser's *Dressing the Man*.

---

## Note on what's deliberately excluded

Nothing above describes or implies changing eye shape/color, nose shape, jaw bone structure,
face shape, or hairstyle/hair color — all of that is the generator's identity lock and stays
untouched. Every lever here is something external to the fixed identity: light, camera
geometry, clothing, posture, and directable-but-temporary facial *state* (expression, gaze,
skin finish) rather than facial *structure*.

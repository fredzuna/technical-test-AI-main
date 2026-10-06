# Technical Decisions

## 1. Rejected approaches and why

### Embedding-only ranking

Embedding ranking was evaluated separately from the structured ranking.

* Top-1 accuracy: **45.92%**
* Top-3 accuracy: **62.23%**

This was slightly worse than structured ranking:

* Top-1: **47.64%**
* Top-3: **62.66%**

Embedding similarity is useful for semantic matching, but it can confuse very similar vehicle versions. It was therefore not used as the only ranking signal.

### Aggressive auto-accept

Lower confidence thresholds caused large negative scores because incorrect auto-accept predictions have a **-3 penalty**.

For example:

* Threshold 0.60: **-162.35**
* Threshold 0.65: **-33.75**
* Threshold 0.70: **+28.90**

The system therefore avoids aggressively accepting predictions when confidence is not sufficiently high.

### Very high confidence threshold

Higher thresholds reduce incorrect auto-accepts, but they also send too many predictions to review.

For example:

* 0.80: score **26.50**, 59 auto-accept / 174 review
* 0.90: score **26.05**, 22 auto-accept / 211 review
* 0.95: score **27.45**, 10 auto-accept / 223 review

The small score improvement at very high thresholds does not justify making almost every prediction a manual review.

---

## 2. Auto-accept threshold

The selected threshold is **0.70**.

At this threshold:

* Score: **28.90**
* Auto-accept: **103 / 233**
* Review: **130 / 233**

It produced the best score among the tested thresholds.

The threshold is intentionally conservative because the cost of an incorrect auto-accept is much higher than the cost of sending a prediction to review.

This threshold should be recalibrated if more labeled production data becomes available.

---

## 3. Handling ambiguous input

Some queries contain very little identifying information, for example:

* `PLATAFORMA`
* `TOLVA`
* `REMOLQUES`
* `CAMIONETA`

These descriptions may identify a general vehicle type but not a unique catalog version.

The system therefore uses a confidence-based decision:

* Strong candidate + sufficient confidence → `auto_accept`
* Weak or ambiguous candidate → `review`

The system should not pretend that a generic description uniquely identifies a vehicle when the catalog contains multiple possible matches.

For ambiguous queries, the preferred future behavior is to use available structured information such as year, vehicle type, segment, manufacturer, and submodel before selecting a specific version.

---

## 4. What I would do with two more weeks

The current evaluation shows two equally important error sources:

* **61 failures** where the correct candidate was not retrieved.
* **61 failures** where the correct candidate was retrieved but ranked incorrectly.

I would prioritize the work in this order:

### 1. Improve retrieval

Increase Recall@20 from the current **73.82%**.

I would add stronger normalization and matching for:

* vehicle model numbers
* manufacturer and submodel
* trim names
* engine size
* transmission
* body type
* axle count
* capacity and other numeric specifications

I would also add explicit handling for generic descriptions and use structured filters before semantic ranking where possible.

### 2. Improve vehicle identity extraction

Extract important identity fields separately instead of treating the entire description as one text string.

For example:

`BMW X4 XDRIVE30IA BASE L4 2.0T`

could produce:

* Manufacturer: BMW
* Model: X4
* Variant: XDRIVE30IA
* Trim: BASE
* Engine: 2.0T

These fields can then receive different ranking weights.

### 3. Improve confidence calibration

The current confidence score is heuristic. With more labeled data, I would calibrate it against actual correctness and measure:

* precision of `auto_accept`
* recall of correct Top-3 results
* score by confidence bucket

This would make the review decision more reliable.

### 4. Add regression tests

Every important failure discovered during evaluation should become a regression test so that improvements to retrieval or ranking do not break previously solved vehicle types.

---

## 5. Four hours with a domain expert

I would spend the four hours with a domain expert understanding how the catalog is actually maintained and how ambiguous descriptions are interpreted.

I would specifically ask for:

### Catalog identity rules

Which fields uniquely identify a catalog version?

For example, whether the combination of:

`manufacturer + submodel + year + trim + vehicle type`

is sufficient, or whether other fields are required.

### Synonyms and abbreviations

Identify common domain abbreviations and equivalent terms.

Examples include:

* `F-600` / `F 600` / `F600`
* `CHASIS CABINA` / `CHASIS-CABINA`
* `AUT` / `AUTOMATICA`
* `4X2` / `4 X 2`

### Generic vehicle descriptions

Understand how descriptions such as `PLATAFORMA`, `TOLVA`, and `REMOLQUES` are normally resolved by human experts.

This is important because these were a significant source of retrieval failures.

### Version selection rules

When multiple catalog versions match the same model, ask which attributes should take priority.

For example:

* model year
* engine
* trim
* transmission
* body configuration
* capacity
* axle count

These rules would directly improve the ranking model.

### Business risk

Finally, I would ask what types of incorrect matches are most costly. This would help determine whether the system should favor `review` more often for certain vehicle categories or ambiguous queries.

---

## 6. Overall decision

The final approach uses a **hybrid retrieval and ranking pipeline**:

```text
Query
  ↓
Normalize / extract vehicle identity
  ↓
Structured candidate retrieval
  ↓
Structured + embedding ranking
  ↓
Confidence calculation
  ↓
0.70 threshold
  ↓
Auto-accept / Review
```

The hybrid ranker was selected because it achieved the best measured ranking performance:

* **Top-1: 54.08%**
* **Top-3: 65.67%**

The system is intentionally designed to send uncertain matches to review rather than forcing an incorrect automatic decision.

# Evaluation

## 1. Results on labeled set

Evaluation was performed on the 233 labeled queries in `data/queries_labeled.csv`.

### Retrieval

The retrieval stage returned the correct catalog code in the top 20 candidates for:

* **172 / 233 queries**
* **Recall@20: 73.82%**
* Correct candidate missing from top 20: **61 queries**

This means retrieval is still a significant source of errors. When the correct catalog version is not retrieved, the ranking stage cannot recover it.

### Ranking

| Method             |      Top-1 |      Top-3 |
| ------------------ | ---------: | ---------: |
| Structured ranking |     47.64% |     62.66% |
| Embedding ranking  |     45.92% |     62.23% |
| Hybrid ranking     | **54.08%** | **65.67%** |

The hybrid approach performed best. Compared with structured ranking, it improved:

* Top-1 accuracy by **6.44 percentage points**
* Top-3 accuracy by **3.01 percentage points**

Embedding-only ranking performed slightly worse than the structured approach, so embeddings were kept as an additional signal rather than used as the primary ranking method.

### Error breakdown

There were **122 total failures**.

* **61 failures:** correct candidate was not in the top 20 → retrieval failure.
* **61 failures:** correct candidate was retrieved but was not ranked first → ranking failure.

This shows that both retrieval and ranking need improvement, with retrieval being especially important because ranking cannot fix a missing candidate.

### Decision threshold

The decision threshold was evaluated using the scoring rules from the challenge.

| Threshold |     Score | Auto-accept |  Review |
| --------: | --------: | ----------: | ------: |
|      0.60 |   -162.35 |         222 |      11 |
|      0.65 |    -33.75 |         166 |      67 |
|  **0.70** | **28.90** |     **103** | **130** |
|      0.75 |     28.10 |          79 |     154 |
|      0.80 |     26.50 |          59 |     174 |
|      0.85 |     14.95 |          36 |     197 |
|      0.90 |     26.05 |          22 |     211 |
|      0.95 |     27.45 |          10 |     223 |

The best evaluated threshold was **0.70**, producing a score of **28.90** on the labeled set.

The system therefore uses **0.70** as the current auto-accept threshold. Predictions below this threshold are sent to review.

---

## 2. Experiment ledger

| Experiment                                        | Result                         | Decision                    |
| ------------------------------------------------- | ------------------------------ | --------------------------- |
| Structured retrieval using vehicle/catalog fields | Recall@20 = 73.82%             | Keep                        |
| Structured ranking                                | Top-1 = 47.64%, Top-3 = 62.66% | Keep as main ranking signal |
| Embedding-only ranking                            | Top-1 = 45.92%, Top-3 = 62.23% | Do not use alone            |
| Hybrid structured + embedding ranking             | Top-1 = 54.08%, Top-3 = 65.67% | Keep                        |
| Confidence threshold 0.50                         | Score = -195.00                | Reject                      |
| Confidence threshold 0.55                         | Score = -195.00                | Reject                      |
| Confidence threshold 0.60                         | Score = -162.35                | Reject                      |
| Confidence threshold 0.65                         | Score = -33.75                 | Reject                      |
| Confidence threshold 0.70                         | Score = 28.90                  | Keep                        |
| Confidence threshold 0.75                         | Score = 28.10                  | Reject in favor of 0.70     |
| Confidence threshold 0.80                         | Score = 26.50                  | Reject                      |
| Confidence threshold 0.85                         | Score = 14.95                  | Reject                      |
| Confidence threshold 0.90                         | Score = 26.05                  | Reject                      |
| Confidence threshold 0.95                         | Score = 27.45                  | Reject in favor of 0.70     |

The main conclusion from the experiments is that combining structured vehicle information with semantic similarity performs better than either signal alone. The threshold experiment also shows that being too aggressive with auto-accept creates a large penalty from incorrect predictions.

---

## 3. Ten specific failures

The following failures were selected to represent different failure modes observed on the labeled set.

### q0001

* **Query:** `CAVALIER LS A 1.5 4P STD`, 2018
* **Correct:** `R000BS`
* **Returned:** `P00071`
* **Correct rank:** 14
* **Failure type:** Ranking
* **Cause:** The correct candidate was retrieved, but another catalog version received a higher score.
* **Remediation:** Give stronger weight to exact model/submodel identity and improve handling of trim/version names such as `LS`.

### q0008

* **Query:** `HINO 816 LONG SERIE 300`, 2019
* **Correct:** `I000AJ`
* **Returned:** `W0008K`
* **Correct rank:** 4
* **Failure type:** Ranking
* **Cause:** The correct HINO candidate was retrieved but model identity was not strong enough to place it first.
* **Remediation:** Improve manufacturer/model identity extraction and give stronger weight to exact model numbers such as `816`.

### q0011

* **Query:** `NISSAN NP300 CHASIS CABINA DH PAQ SEG AC STD`, 2019
* **Correct:** `H000BN`
* **Returned:** `P000AN`
* **Correct rank:** 2
* **Failure type:** Ranking
* **Cause:** Two very similar NP300 versions received almost identical scores.
* **Remediation:** Improve submodel and trim-level matching, especially for package/configuration terms.

### q0014

* **Query:** `PLATAFORMA 2 EJES`, 2006
* **Correct:** `Z0000M`
* **Returned:** `U0007I`
* **Failure type:** Retrieval
* **Cause:** The query contains very little identifying information. The description is generic and mainly identifies a vehicle category rather than a specific catalog version.
* **Remediation:** Use stronger type/segment/year filtering and handle generic trailer descriptions as ambiguous cases.

### q0018

* **Query:** `REMOLQUES`, 2025
* **Correct:** `Z0000M`
* **Returned:** `D0003O`
* **Failure type:** Retrieval
* **Cause:** The query is extremely short and does not provide enough information to uniquely identify a catalog version.
* **Remediation:** Detect low-information queries and favor broad retrieval plus review instead of forcing a specific version.

### q0024

* **Query:** `TANQUE A.INOX ANILLADO 2 EJES 31,000 LTS MEDIA. AUT.`, 2023
* **Correct:** `Q00046`
* **Returned:** `U0003Y`
* **Failure type:** Retrieval
* **Cause:** Important domain-specific attributes such as tank type, capacity, axle count, and configuration were not sufficient to retrieve the correct catalog version.
* **Remediation:** Add domain-specific normalization for trailer/body terminology and numeric specifications.

### q0032

* **Query:** `AUDI A3 40 TFSI S LINE L4 2.0 190 HP S TRONIC`, 2024
* **Correct:** `W000C8`
* **Returned:** `Z000C6`
* **Correct rank:** 6
* **Failure type:** Ranking
* **Cause:** Several Audi A3 versions have very similar descriptions. The ranking does not distinguish all trim and engine attributes strongly enough.
* **Remediation:** Extract structured attributes such as model, trim, engine size, horsepower, and transmission separately.

### q0039

* **Query:** `BMW X4 XDRIVE30IA BASE 5P L4 2.0T BA ABS AA. AUT.`, 2023
* **Correct:** `K0001S`
* **Returned:** `H0007C`
* **Correct rank:** 3
* **Failure type:** Ranking
* **Cause:** Similar BMW X4 catalog versions are difficult to separate using general text similarity.
* **Remediation:** Improve exact matching for model variant and configuration terms such as `XDRIVE30IA` and `BASE`.

### q0054

* **Query:** `PLATAFORMA`, 2008
* **Correct:** `Z0000M`
* **Returned:** `L0001A`
* **Failure type:** Retrieval
* **Cause:** The description is too generic to identify a unique catalog version.
* **Remediation:** Treat generic descriptions as low-confidence queries and rely more heavily on vehicle type, segment, and year constraints.

### q0075

* **Query:** `RENEGADE LATITUDE L4 IMP AUT 4 ABS CA SE PIEL SM SQ CB`, 2021
* **Correct:** `L000BQ`
* **Returned:** `N0006G`
* **Failure type:** Retrieval
* **Cause:** The expected catalog candidate was not retrieved despite the query containing several useful configuration attributes.
* **Remediation:** Improve token normalization and retrieval weighting for trim, engine, transmission, and equipment terms.

### Summary of failures

The failures show two main classes of problems:

1. **Generic or incomplete descriptions**
   Examples include `PLATAFORMA`, `TOLVA`, and `REMOLQUES`. These queries often do not contain enough information to uniquely identify a catalog version.

2. **Very similar catalog versions**
   Queries such as Audi A3, BMW X4, Nissan NP300, and HINO 816 can retrieve the correct candidate but still rank a similar version above it.

The first problem should primarily be addressed in retrieval and ambiguity detection. The second should be addressed with better vehicle identity extraction, structured attribute matching, and improved ranking.

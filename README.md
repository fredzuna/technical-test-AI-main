# Work sample: matching broker vehicle descriptions to a catalog

Five hours, one sitting. Everything you need is in this directory.

## The situation

An insurance broker sends us a fleet spreadsheet. One row, one vehicle,
described in whatever shorthand the person at the keyboard uses:

    MERCEDEZ BENZ CHASIS CABINA LK-1417/34     1993
    GMOTORS YUKON DENALI 6VEL AUT              2009
    CAJA CERRADA RM 2 EJES 40' BAJA            2015
    CITYSTAR CF 600 RB CUMMINS 200 HP 9 TON    2007

To quote the policy we need the insurer's catalog code for each vehicle. Get it
right and the quote is correct. Get it wrong and we have quoted the wrong
vehicle, which surfaces later, in front of the client.

Today a human underwriter does this by hand, thousands of rows at a time. Your
job is to build the system that does it, and - just as important - to tell us
honestly how good that system is.

## Your task

For each query in `data/queries_blind.csv`, produce:

- `top1_code` - your single best catalog code
- `top3_codes` - your ranked top 3, pipe-separated, best first, `top1_code` included
- `confidence` - a number in `[0, 1]`
- `decision` - either `auto_accept` (we send it straight through) or `review`
  (we put it in front of a human)

Only codes from `data/versions.csv` are valid answers.

## How you are scored

**Not on accuracy.** On the business utility of your output:

| Outcome | Utility |
|---|---|
| `auto_accept`, `top1_code` correct | **+1.00** |
| `auto_accept`, `top1_code` wrong | **-3.00** |
| `review`, correct code among `top3_codes` | **+0.15** |
| `review`, correct code not among `top3_codes` | **-0.05** |

Reported as the mean per row. A wrong auto-accept costs three times what a
correct one earns, because it flows into a quote. Sending a row to a human is
cheap but not free.

`score.py` is the exact script we will run on your submission. Use it on the
labeled set as often as you like. It also prints what your own candidate lists
would have scored under two trivial policies, so you can see whether your
decision logic is adding anything.

This metric has structure. It is worth twenty minutes of thought before you
write a threshold.

## The data

The catalog arrives the way the insurer maintains it: normalized across files,
with a separate year table. Joining it up is your problem, and the choices you
make there matter more than they look.

**`data/versions.csv`** - 13,298 rows covering 13,140 distinct codes. The leaf
level. **Only a `code` from this file is a valid answer.**

| Column | Meaning |
|---|---|
| `code` | This version's identifier, and a valid answer |
| `submodel_key`, `manufacturer_key` | The `code` of this row's submodel and manufacturer |
| `descveh` | Version description |
| `tipveh` | Vehicle type, in the insurer's taxonomy |
| `cvesegm` | Commercial segment |

**`data/submodels.csv`** - 1,338 rows. Model line. Join `versions.submodel_key`
to `submodels.code`. Carries `submarca`.

**`data/manufacturers.csv`** - 123 rows. Join `versions.manufacturer_key` to
`manufacturers.code`. Carries `marca`.

**`data/version_years.csv`** - 85,617 rows of `(code, modelo)`. Which model years
each code is offered in.

**`data/queries_labeled.csv`** - 233 rows with `expected_code`. Yours to train,
tune and evaluate on.

**`data/queries_blind.csv`** - 155 rows without labels. This is what you submit
predictions for.

Both query files carry the broker's own fields: `description`, `year`, `marca`,
`submarca`, `tipveh`, and a coarse `segment` we derived from the text. They are
as we received them, including the gaps.

Three things you should know rather than discover the hard way:

- The labels were produced by domain experts working at speed. They are the best
  ground truth we have. They are not guaranteed perfect.
- The blind set is weighted towards the harder commercial segments, so its mix of
  vehicle types is not identical to the labeled set's.
- These are the insurer's own files, not something we cleaned up for you. They
  have the warts you would expect. We have not listed them; finding the ones that
  affect your results is part of the work.

## What to send back

1. **`predictions.csv`** - the blind set, in the schema above. Validate it with
   `python submission_check.py --predictions predictions.csv --queries data/queries_blind.csv`.

2. **`EVAL.md`** - three sections, all of them required:
   - Your results on the labeled set, with **retrieval recall reported separately
     from ranking accuracy**. We want to know how often the right answer was
     never in your candidate list at all, as distinct from how often it was there
     and you ranked something else above it.
   - An **experiment ledger**: one line per thing you tried. What you changed, what
     the number did, whether you kept it. Including the ones that failed.
   - **Ten specific failures from the labeled set, cited by `query_id`.** For each:
     what the right answer was, what you returned, why you think that happened,
     and what you did or would do about it. This is the section we read first.

3. **`DECISIONS.md`** - two pages maximum:
   - What you tried and rejected, and why.
   - How you chose your auto-accept threshold.
   - What your system does when the input genuinely does not determine one answer.
   - What you would do with two more weeks.
   - You have four hours of a domain expert's time. What do you ask them for, and
     why that rather than more engineering?

4. **Your code**, with `make predict` reproducing `predictions.csv` from a clean
   checkout. We will run it.

Please commit as you go rather than squashing at the end, and keep the `.git`
directory in what you send us. We are interested in the order you did things in,
not in policing you.

## Constraints

- **Five hours.** One sitting, hard stop. Send us what you have at five hours.
- **`make predict` must run on our machine**, with only `OPENAI_API_KEY` set and
  `make setup` performed. If it does not run, we cannot score you.
- **Budget: under $2 of LLM spend and under 10 minutes wall-clock** for the
  155-row blind run. We verify this when we re-run it. Design for it.
- **Use AI assistants.** We do, all day. We are evaluating your judgment, not
  your typing. The written deliverables are where that judgment shows.

## Getting started

`make setup` installs the dependencies. `make baseline` runs the naive solution
in `solution/baseline.py` over the labeled set and scores it, so you have a floor
on the scoreboard from minute one. It is deliberately poor. You are expected to
replace it; keep the input/output contract.

`embed_helper.py` gives you cached batch embeddings if you want them. Nothing
depends on it, and a strong submission does not have to use an LLM at all.

## Read this before you start

**The task is larger than five hours.** That is deliberate and it is not a trick.
You will have to decide what not to do, and those choices are a graded part of
the exercise. A focused, well-measured, honestly-described partial system beats
an ambitious one you cannot account for.

We weight the submission roughly like this:

| | |
|---|---|
| `EVAL.md` - the harness, the decomposition, the ten failures | 35% |
| `DECISIONS.md` - judgment and calibration reasoning | 30% |
| Utility score on the blind set | 20% |
| Code quality and reproducibility | 15% |

Two things will end the review regardless of everything else: `make predict` not
running, and a blind-set utility that fails to beat the shipped baseline.

We would rather see a system you can explain than a number you cannot.

## Practicalities

- **Return within one week** of receiving this kit. The five hours are one
  sitting, but you choose which day - tell us when you plan to start.
- **How:** zip the whole directory, including your `.git` folder, and reply to
  the email that sent you this kit with the archive attached.
- **Confidential.** The catalog in this kit is real industry data shared with you
  for this exercise only. Please do not redistribute it, publish it, or keep it
  after we have finished the process. The identifiers have been re-encoded, so
  nothing here maps back to a named insurer's systems.

Questions about the brief are welcome and do not count against you. Ask before
you burn an hour on an ambiguity.

Good luck.

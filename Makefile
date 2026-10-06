# Contract between your solution and our grading harness.
#
# `make predict` is the only target we are guaranteed to run. It must read
# data/queries_blind.csv and write predictions.csv, end to end, with no manual
# steps in between. We run it from a clean clone of what you send us, with only
# OPENAI_API_KEY set and the documented setup performed.
#
# Budget, enforced on our re-run: under $2 of LLM spend and under 10 minutes.

PYTHON ?= python3
BLIND  := data/queries_blind.csv
DEV    := data/queries_labeled.csv

.PHONY: setup predict score check baseline clean

setup:
	$(PYTHON) -m pip install -r requirements.txt

## Produce predictions.csv for the blind set. Point this at your own entry point.
predict:
	$(PYTHON) solution/baseline.py --queries $(BLIND) --versions data/versions.csv --out predictions.csv

## Score yourself on the labeled dev set. Generate dev_predictions.csv first.
score:
	$(PYTHON) score.py --predictions dev_predictions.csv --labels $(DEV)

## Validate the format of your final submission.
check:
	$(PYTHON) submission_check.py --predictions predictions.csv --queries $(BLIND)

## Run the supplied baseline over dev, so you have a floor to beat on day one.
baseline:
	$(PYTHON) solution/baseline.py --queries $(DEV) --versions data/versions.csv --out dev_predictions.csv
	$(PYTHON) score.py --predictions dev_predictions.csv --labels $(DEV)

clean:
	rm -f predictions.csv dev_predictions.csv

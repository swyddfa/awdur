# Global flags to pass to hatch, e.g. -v, --no-color etc.
PY ?= 3.14
HATCH = hatch
HATCH_ARGS =

.PHONY: clean-env
clean-env:
	for venv in $$($(HATCH) env show -i --json | jq -r 'keys | join(" ")') ; do $(HATCH) env remove "$${venv}" ; done

.PHONY: dist
dist:
	$(HATCH) $(HATCH_ARGS) build

.PHONY: test
test:
	$(HATCH) $(HATCH_ARGS) test -py=$(PY)

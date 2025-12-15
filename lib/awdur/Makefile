# Global flags to pass to hatch, e.g. -v, --no-color etc.
HATCH = hatch
HATCH_ARGS =

.PHONY: clean-env
clean-env:
	for venv in $$($(HATCH) env show -i --json | jq -r 'keys | join(" ")') ; do $(HATCH) env remove "$${venv}" ; done

.PHONY: dist
dist:
	$(HATCH) $(HATCH_ARGS) build

.PHONY: test
test: ARGS ?= -i py=$(shell $(PY) -c 'import sys;v=sys.version_info;print(f"{v.major}.{v.minor}")')
test: $(PY)
	$(HATCH) $(HATCH_ARGS) test $(ARGS)

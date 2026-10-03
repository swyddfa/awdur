ARCH ?= $(shell arch)
BIN ?= $(HOME)/.local/bin

ifeq ($(strip $(ARCH)),)
$(error Unable to determine platform architecture)
endif

UV_VERSION := 0.12.10

UV ?= $(shell command -v uv)
UVX ?= $(shell command -v uvx)

ifeq ($(strip $(UV)),)

UV := $(BIN)/uv
UVX := $(BIN)/uvx

$(UV):
	curl -L --output /tmp/uv.tar.gz https://github.com/astral-sh/uv/releases/download/$(UV_VERSION)/uv-$(ARCH)-unknown-linux-gnu.tar.gz
	tar -xf /tmp/uv.tar.gz -C /tmp
	rm /tmp/uv.tar.gz

	test -d $(BIN) || mkdir -p $(BIN)

	mv /tmp/uv-$(ARCH)-unknown-linux-gnu/uv $@
	mv /tmp/uv-$(ARCH)-unknown-linux-gnu/uvx $(UVX)

	$@ --version
	$(UVX) --version

endif

# Our default Python version
PY_VERSION := 3.14

# Hatch is not only used for building packages, but bootstrapping any missing
# interpreters
HATCH ?= $(shell command -v hatch)

ifeq ($(strip $(HATCH)),)

HATCH := $(BIN)/hatch

$(HATCH): | $(UV)
	$(UV) tool install hatch
	$@ --version

endif

PY_TOOLS := $(HATCH)

# Set a default `python` command if there is not one already
PY ?= $(shell command -v python)

ifeq ($(strip $(PY)),)
PY := $(BIN)/python

$(PY): | $(UV)
	$(UV) python install $(PY_VERSION)
	ln -s $$($(UV) python find $(PY_VERSION)) $@
	$@ --version
endif

# One command to bootstrap all tools and check their versions
.PHONY: tools
tools: $(UV) $(PY) $(PY_TOOLS)
	for prog in $^ ; do echo -n "$${prog}\t" ; PATH=$(BIN) $${prog} --version; done

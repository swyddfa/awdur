# Minimal makefile for Sphinx documentation
#

BUILDDIR ?= _build

.PHONY: clean
clean:
	[ -d $(BUILDDIR) ] && rm -r $(BUILDDIR)

.PHONY: dirhtml
dirhtml:
	uv run --no-project \
               --python 3.14 \
               --with sphinx \
               --with furo \
               --with-editable ../lib/awdur \
               sphinx-build -M dirhtml . $(BUILDDIR)

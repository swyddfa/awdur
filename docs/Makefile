PY ?= 3.14
BUILDDIR ?= _build

.PHONY: clean
clean:
	[ -d $(BUILDDIR) ] && rm -r $(BUILDDIR)

.PHONY: dirhtml
dirhtml: requirements.txt
	uv run --no-project \
               --python $(PY) \
               --with-requirements requirements.txt \
               --with-editable ../lib/awdur \
               sphinx-build -M dirhtml . $(BUILDDIR)

%.txt: %.in
	uv pip compile --generate-hashes --upgrade --python-version $(PY) --output-file $@ $<

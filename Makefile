PYTHON ?= python3
GENERATED := chndomains.rsc

all: generate

.PHONY: generate
generate:
	$(PYTHON) generate.py

.PHONY: check
check:
	$(PYTHON) -m py_compile generate.py
	$(PYTHON) generate.py
	tmp=$$(mktemp); \
	trap 'rm -f "$$tmp"' EXIT; \
	cp $(GENERATED) "$$tmp"; \
	$(PYTHON) generate.py; \
	cmp "$$tmp" $(GENERATED)

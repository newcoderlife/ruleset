PYTHON ?= python3
GENERATED := chndomains.rsc
CHECKSUM := chndomains.sha256

all: generate

.PHONY: generate
generate:
	$(PYTHON) generate.py --output $(GENERATED)

.PHONY: checksum
checksum: generate
	shasum -a 256 $(GENERATED) > $(CHECKSUM)

.PHONY: lint
lint:
	$(PYTHON) lint.py

.PHONY: check
check: lint
	$(PYTHON) -m py_compile generate.py lint.py
	tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT; \
	$(PYTHON) generate.py --output "$$tmp/first.rsc"; \
	$(PYTHON) generate.py --output "$$tmp/second.rsc"; \
	cmp "$$tmp/first.rsc" "$$tmp/second.rsc"

.PHONY: clean
clean:
	rm -f $(GENERATED) $(CHECKSUM)

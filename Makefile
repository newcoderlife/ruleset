all: generate

.PHONY: generate
generate:
	python3 generate.py

.PHONY: force-push
force-push:
	git add . && git commit --amend --no-edit && git push -f
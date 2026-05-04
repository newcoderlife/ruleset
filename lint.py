#!/usr/bin/env python3

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent
DOMAINS_DIR = ROOT / "domains"

OPTIONAL_FILES = {"local.cn", "local.noncn"}
ENTRY_FILES = ("cn", "noncn", "ruleset.cn", "ruleset.noncn")

LABEL_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


errors = []
parsed_files = {}


def display_path(path):
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def location(path, line_number):
    return f"{display_path(path)}:{line_number}"


def add_error(message):
    errors.append(message)


def is_optional(path):
    return path.name in OPTIONAL_FILES


def is_inside_repo(path):
    return path == ROOT or ROOT in path.parents


def parent_domains(domain):
    labels = domain.rstrip(".").split(".")
    return [".".join(labels[index:]) + "." for index in range(1, len(labels))]


def domain_entries(items):
    return [item for item in items if item[0] == "domain"]


def validate_domain(domain, path, line_number):
    if domain != domain.lower():
        add_error(f"{location(path, line_number)}: domain must be lowercase: {domain}")

    if not domain.endswith("."):
        add_error(f"{location(path, line_number)}: domain must end with '.': {domain}")
        return

    bare_domain = domain.rstrip(".")
    labels = bare_domain.split(".")

    if bare_domain == "" or any(label == "" for label in labels):
        add_error(f"{location(path, line_number)}: invalid domain: {domain}")
        return

    for label in labels:
        if len(label) > 63:
            add_error(f"{location(path, line_number)}: domain label is too long: {label}")
        elif LABEL_PATTERN.fullmatch(label) is None:
            add_error(f"{location(path, line_number)}: invalid domain label: {label}")


def include_target(path, include_text, line_number):
    target_text = include_text.removeprefix("include:").strip()

    if target_text == "":
        add_error(f"{location(path, line_number)}: empty include")
        return None

    target_path = Path(target_text)
    if target_path.is_absolute():
        add_error(f"{location(path, line_number)}: include must be relative")
        return None

    target_path = (path.parent / target_path).resolve()
    if not is_inside_repo(target_path):
        add_error(f"{location(path, line_number)}: include escapes repository")
        return None

    if not target_path.exists():
        if not is_optional(target_path):
            add_error(
                f"{location(path, line_number)}: include target does not exist: {target_text}"
            )
            return None

    elif not target_path.is_file():
        add_error(f"{location(path, line_number)}: include target is not a file: {target_text}")
        return None

    return target_path


def parse_file(path):
    path = path.resolve()
    cached = parsed_files.get(path)
    if cached is not None:
        return cached

    if not path.exists():
        if not is_optional(path):
            add_error(f"{display_path(path)}: file does not exist")

        parsed_files[path] = []
        return []

    lines = path.read_text().splitlines()
    if lines and lines[-1].strip() == "":
        add_error(f"{location(path, len(lines))}: trailing blank line at end of file")

    items = []
    seen_domains = {}

    for line_number, raw_line in enumerate(lines, start=1):
        if raw_line != raw_line.rstrip():
            add_error(f"{location(path, line_number)}: trailing whitespace")

        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue

        if raw_line != raw_line.lstrip():
            add_error(f"{location(path, line_number)}: leading whitespace")

        if line.startswith("include:"):
            target_path = include_target(path, line, line_number)
            if target_path is not None:
                items.append(("include", target_path, path, line_number))

            continue

        validate_domain(line, path, line_number)

        first_seen = seen_domains.get(line)
        if first_seen is not None:
            first_path, first_line = first_seen
            add_error(
                f"{location(path, line_number)}: duplicate domain: {line} "
                f"(first seen at {location(first_path, first_line)})"
            )
        else:
            seen_domains[line] = (path, line_number)

        items.append(("domain", line, path, line_number))

    parsed_files[path] = items
    return items


def expand_file(path, stack=()):
    path = path.resolve()
    if path in stack:
        cycle = " -> ".join(display_path(item) for item in (*stack, path))
        add_error(f"{display_path(path)}: include cycle: {cycle}")
        return []

    expanded = []
    for kind, value, item_path, line_number in parse_file(path):
        if kind == "domain":
            expanded.append((kind, value, item_path, line_number))
        else:
            expanded.extend(expand_file(value, (*stack, path)))

    return expanded


def check_sorted(path, items):
    domains = domain_entries(items)
    current_order = [domain for _, domain, _, _ in domains]
    sorted_order = sorted(current_order)

    if current_order == sorted_order:
        return

    for item, expected_domain in zip(domains, sorted_order):
        _, current_domain, item_path, line_number = item
        if current_domain != expected_domain:
            add_error(
                f"{location(item_path, line_number)}: domains must be sorted: "
                f"expected {expected_domain}, found {current_domain}"
            )
            return

    add_error(f"{display_path(path)}: domains must be sorted")


def check_covered_domains(scope, items):
    first_entry = {}
    for _, domain, path, line_number in domain_entries(items):
        first_entry.setdefault(domain, (path, line_number))

    for _, domain, path, line_number in domain_entries(items):
        for parent in parent_domains(domain):
            parent_entry = first_entry.get(parent)
            if parent_entry is None:
                continue

            parent_path, parent_line = parent_entry
            add_error(
                f"{location(path, line_number)}: redundant domain in {scope}: "
                f"{domain} is covered by {parent} "
                f"at {location(parent_path, parent_line)}"
            )
            break


def check_expanded_duplicates(scope, items):
    first_entry = {}

    for _, domain, path, line_number in domain_entries(items):
        previous = first_entry.get(domain)
        if previous is None:
            first_entry[domain] = (path, line_number)
            continue

        previous_path, previous_line = previous
        add_error(
            f"{location(path, line_number)}: duplicate domain in {scope}: "
            f"{domain} (first seen at {location(previous_path, previous_line)})"
        )

    return first_entry


def all_linted_files():
    files = [ROOT / name for name in ENTRY_FILES]
    domain_files = []

    for path in sorted(DOMAINS_DIR.iterdir()):
        if path.is_file():
            files.append(path)
            domain_files.append(path.resolve())
        else:
            add_error(f"{display_path(path)}: expected a file")

    for name in OPTIONAL_FILES:
        path = ROOT / name
        if path.exists():
            files.append(path)

    return files, set(domain_files)


def lint():
    files, domain_files = all_linted_files()

    for path in files:
        items = parse_file(path)
        check_covered_domains(display_path(path), items)

        if path.resolve() in domain_files:
            check_sorted(path, items)

    cn_items = expand_file(ROOT / "cn")
    noncn_items = expand_file(ROOT / "noncn")

    check_covered_domains("cn ruleset", cn_items)
    cn_domains = check_expanded_duplicates("cn ruleset", cn_items)
    noncn_domains = check_expanded_duplicates("noncn ruleset", noncn_items)

    for domain in sorted(cn_domains.keys() & noncn_domains.keys()):
        cn_path, cn_line = cn_domains[domain]
        noncn_path, noncn_line = noncn_domains[domain]
        add_error(
            f"{domain}: assigned to both cn and noncn "
            f"({location(cn_path, cn_line)} and {location(noncn_path, noncn_line)})"
        )


def main():
    lint()

    if not errors:
        return 0

    for error in errors:
        print(error, file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

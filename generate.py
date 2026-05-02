#!/usr/bin/env python3

import argparse
from pathlib import Path
from typing import TypeVar


DEFAULT_NONCN_DNS = "1.1.1.1,8.8.8.8"
DEFAULT_CN_DNS = "223.5.5.5,114.114.114.114"
OPTIONAL_RULESETS = {"local.cn", "local.noncn"}
RULE_COMMENT = "ruleset"
T = TypeVar("T")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RouterOS DNS forwarder rules.")
    parser.add_argument("--noncn-ruleset", default="noncn", help="non-CN ruleset file")
    parser.add_argument("--cn-ruleset", default="cn", help="CN ruleset file")
    parser.add_argument("--output", default="chndomains.rsc", help="RouterOS script output")
    parser.add_argument(
        "--noncn-name",
        default="noncn",
        help="RouterOS forwarder name for non-CN domains",
    )
    parser.add_argument(
        "--cn-name",
        default="cn",
        help="RouterOS forwarder name for CN domains",
    )
    parser.add_argument(
        "--noncn-dns",
        default=DEFAULT_NONCN_DNS,
        help="DNS servers for non-CN domains",
    )
    parser.add_argument(
        "--cn-dns",
        default=DEFAULT_CN_DNS,
        help="DNS servers for CN domains",
    )
    return parser.parse_args()


def dedupe(items: list[T]) -> list[T]:
    return list(dict.fromkeys(items))


def domain_specificity(domain: str) -> int:
    return len(domain.rstrip(".").split("."))


def parent_domains(domain: str) -> list[str]:
    labels = domain.rstrip(".").split(".")
    return [".".join(labels[index:]) + "." for index in range(1, len(labels))]


def read_ruleset(file_path: str | Path) -> list[str]:
    path = Path(file_path)
    result = []

    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError:
        if path.name in OPTIONAL_RULESETS:
            return []
        raise

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue

        if line.startswith("include:"):
            include_target = line.removeprefix("include:").strip()
            if include_target == "":
                raise ValueError(f"{path}:{line_number}: empty include")

            include_path = path.parent / include_target
            result.extend(read_ruleset(include_path))
        else:
            if not line.endswith("."):
                raise ValueError(f"{path}:{line_number}: domain must end with '.'")

            result.append(line)

    return dedupe(result)


def prune_covered_domains(domains: list[str]) -> list[str]:
    domains = dedupe(domains)
    domain_set = set(domains)
    result = []

    for domain in domains:
        if any(parent in domain_set for parent in parent_domains(domain)):
            continue

        result.append(domain)

    return result


def sort_group_domains(domains: list[str]) -> list[str]:
    indexed_domains = list(enumerate(prune_covered_domains(domains)))
    indexed_domains.sort(key=lambda item: (domain_specificity(item[1]), item[0]))
    return [domain for _, domain in indexed_domains]


def build_static_entries(
    noncn: list[str],
    cn: list[str],
    noncn_name: str,
    cn_name: str,
) -> list[tuple[str, str]]:
    entries = [(domain, noncn_name) for domain in noncn]
    entries.extend((domain, cn_name) for domain in cn)

    forward_by_domain = {}
    for domain, forward_to in entries:
        existing = forward_by_domain.get(domain)
        if existing is not None and existing != forward_to:
            raise ValueError(f"{domain} is assigned to both {existing} and {forward_to}")

        forward_by_domain[domain] = forward_to

    result = [(domain, cn_name) for domain in sort_group_domains(cn)]
    result.extend((domain, noncn_name) for domain in sort_group_domains(noncn))
    return result


def write_routeros_rules(
    output: str | Path,
    noncn: list[str],
    cn: list[str],
    noncn_name: str,
    cn_name: str,
    noncn_dns: str,
    cn_dns: str,
) -> None:
    entries = build_static_entries(noncn, cn, noncn_name, cn_name)

    with Path(output).open("w") as f:
        f.write(f"/ip/dns/static remove [find where comment={RULE_COMMENT}]\n")
        f.write(f"/ip/dns/forwarders remove [find where comment={RULE_COMMENT}]\n")

        f.write(
            f"/ip/dns/forwarders add comment={RULE_COMMENT} dns-servers={noncn_dns} name={noncn_name}\n"
        )
        f.write(
            f"/ip/dns/forwarders add comment={RULE_COMMENT} dns-servers={cn_dns} name={cn_name}\n"
        )

        for domain, forward_to in entries:
            f.write(
                f"/ip/dns/static add comment={RULE_COMMENT} forward-to={forward_to} match-subdomain=yes name={domain} type=FWD\n"
            )

        f.write("/ip/dns/cache flush\n")


if __name__ == "__main__":
    args = parse_args()
    write_routeros_rules(
        output=args.output,
        noncn=read_ruleset(args.noncn_ruleset),
        cn=read_ruleset(args.cn_ruleset),
        noncn_name=args.noncn_name,
        cn_name=args.cn_name,
        noncn_dns=args.noncn_dns,
        cn_dns=args.cn_dns,
    )

#!/usr/bin/env python3

import argparse
from pathlib import Path


DEFAULT_NONCN_DNS = "1.1.1.1,8.8.8.8"
DEFAULT_CN_DNS = "223.5.5.5,114.114.114.114"
OPTIONAL_RULESETS = {"local.cn", "local.noncn"}
RULE_COMMENT = "ruleset"


def parse_args() -> argparse.Namespace:
    """Parse CLI options for ruleset inputs, output path, and DNS forwarders."""
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


def read_ruleset(file_path: str | Path, fallback_address_list: str) -> list[tuple[str, str]]:
    """Expand a ruleset file into domain and address-list pairs."""
    path = Path(file_path)
    address_list = path.name if path.parent.name == "domains" else fallback_address_list
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
            result.extend(read_ruleset(include_path, fallback_address_list))
        else:
            if not line.endswith("."):
                raise ValueError(f"{path}:{line_number}: domain must end with '.'")

            result.append((line, address_list))

    return list(dict.fromkeys(result))


def build_static_entries(
    noncn: list[tuple[str, str]],
    cn: list[tuple[str, str]],
    noncn_name: str,
    cn_name: str,
) -> list[tuple[str, str, str]]:
    """Build de-duplicated RouterOS static DNS entries from both rulesets."""
    entries = [(domain, noncn_name, address_list) for domain, address_list in noncn]
    entries.extend((domain, cn_name, address_list) for domain, address_list in cn)

    seen_domains = set()
    for domain, _, _ in entries:
        if domain in seen_domains:
            raise ValueError(f"{domain} is assigned more than once")

        seen_domains.add(domain)

    return sorted(entries, key=lambda entry: -len(entry[0].rstrip(".").split(".")))


def write_routeros_rules(
    output: str | Path,
    noncn: list[tuple[str, str]],
    cn: list[tuple[str, str]],
    noncn_name: str,
    cn_name: str,
    noncn_dns: str,
    cn_dns: str,
) -> None:
    """Write a complete RouterOS script for forwarders, static DNS rules, and cache flush."""
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

        for domain, forward_to, address_list in entries:
            f.write(
                f"/ip/dns/static add address-list={address_list} comment={RULE_COMMENT} "
                f"forward-to={forward_to} match-subdomain=yes name={domain} type=FWD\n"
            )

        f.write("/ip/dns/cache flush\n")


if __name__ == "__main__":
    args = parse_args()
    write_routeros_rules(
        output=args.output,
        noncn=read_ruleset(args.noncn_ruleset, args.noncn_name),
        cn=read_ruleset(args.cn_ruleset, args.cn_name),
        noncn_name=args.noncn_name,
        cn_name=args.cn_name,
        noncn_dns=args.noncn_dns,
        cn_dns=args.cn_dns,
    )

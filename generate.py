#!/usr/bin/env python3

import argparse
from pathlib import Path


DEFAULT_NONCN_DNS = "1.1.1.1,8.8.8.8"
DEFAULT_CN_DNS = "223.5.5.5,114.114.114.114"
OPTIONAL_RULESETS = {"local.cn", "local.noncn"}


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


def dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


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


def write_routeros_rules(
    output: str | Path,
    noncn: list[str],
    cn: list[str],
    noncn_name: str,
    cn_name: str,
    noncn_dns: str,
    cn_dns: str,
) -> None:
    with Path(output).open("w") as f:
        f.write("/ip/dns/forwarders remove [find where comment=automate]\n")
        f.write("/ip/dns/static remove [find where comment=automate]\n")

        f.write(
            f"/ip/dns/forwarders add comment=automate dns-servers={noncn_dns} name={noncn_name}\n"
        )
        f.write(
            f"/ip/dns/forwarders add comment=automate dns-servers={cn_dns} name={cn_name}\n"
        )

        for domain in noncn:
            f.write(
                f"/ip/dns/static add comment=automate forward-to={noncn_name} match-subdomain=yes name={domain} type=FWD\n"
            )
        for domain in cn:
            f.write(
                f"/ip/dns/static add comment=automate forward-to={cn_name} match-subdomain=yes name={domain} type=FWD\n"
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

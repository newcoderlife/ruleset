#!/usr/bin/env python3

import os


def contains(subdomain: str, ruleset: list) -> str:
    if ruleset is None:
        return ""

    result = ""
    for domain in ruleset:
        s = subdomain.split(".")[::-1]
        d = domain.split(".")[::-1]
        if len(d) > len(s):
            continue

        flag = True
        for i in range(len(d)):
            if d[i] != s[i]:
                flag = False
                break
        if flag and (result == "" or len(domain) < len(result)):
            result = domain
    return result


def read_ruleset(file_path: str) -> list:
    dirname = os.path.dirname(file_path)

    result = []
    try:
        with open(file_path, "r") as f:
            for line in f:
                if line.strip() == "" or line.startswith("#"):
                    continue

                if line.startswith("include:"):
                    result.extend(
                        read_ruleset(
                            os.path.join(dirname, line.removeprefix("include:").strip())
                        )
                    )
                else:
                    result.append(line.strip())
            print(f"read {file_path}")
    except FileNotFoundError:
        print(f"{file_path} not found")
    except Exception as e:
        print(f"read {file_path} except {e}")

    return list(set(result))


if __name__ == "__main__":
    noncn = read_ruleset("ruleset.noncn")
    cn = read_ruleset("cn")

    with open("chndomains.rsc", "w") as f:
        f.write("/ip/dns/forwarders remove [find where comment=automate]\n")
        f.write("/ip/dns/static remove [find where comment=automate]\n")

        f.write(
            "/ip/dns/forwarders add comment=automate dns-servers=1.1.1.1,8.8.8.8 name=noncn\n"
        )
        f.write(
            "/ip/dns/forwarders add comment=automate dns-servers=223.5.5.5,114.114.114.114 name=cn\n"
        )

        for domain in noncn:
            f.write(
                f"/ip/dns/static add comment=automate forward-to=noncn match-subdomain=yes name={domain} type=FWD\n"
            )
        for domain in cn:
            f.write(
                f"/ip/dns/static add comment=automate forward-to=cn match-subdomain=yes name={domain} type=FWD\n"
            )

        f.write("/ip/dns/cache flush\n")

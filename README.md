# Ruleset

RouterOS DNS forwarder rules for CN and non-CN domains.

`generate.py` reads the ruleset files and writes `chndomains.rsc`, a RouterOS script
that creates DNS forwarders and static FWD entries.

## Usage

Generate the RouterOS script:

```sh
make generate
```

Import `chndomains.rsc` on RouterOS after reviewing the DNS upstreams in the
generated file.

Default upstreams:

- `noncn`: `1.1.1.1,8.8.8.8`
- `cn`: `223.5.5.5,114.114.114.114`

Override them when generating:

```sh
python3 generate.py --noncn-dns 1.1.1.1,8.8.8.8 --cn-dns 223.5.5.5,114.114.114.114
```

## Rules

- `ruleset.noncn` and `ruleset.cn` define shared domain groups.
- `noncn` and `cn` are the top-level inputs used by the generator.
- `local.noncn` and `local.cn` are optional local overrides and are ignored by git.
- Domain entries should use the trailing-dot form, for example `twitter.com.`.

Run this before committing generated output:

```sh
make check
```

All contributions are welcome.

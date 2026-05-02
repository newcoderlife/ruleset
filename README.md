# Ruleset

RouterOS DNS forwarder rules for routing CN and non-CN domains to different DNS
upstreams.

## Generate

```sh
make generate
make check
```

The generated RouterOS script is `chndomains.rsc`.

Default upstreams:

- `cn`: `223.5.5.5,114.114.114.114`
- `noncn`: `1.1.1.1,8.8.8.8`

Override upstreams:

```sh
python3 generate.py --cn-dns 223.5.5.5,114.114.114.114 --noncn-dns 1.1.1.1,8.8.8.8
```

## RouterOS

Create the update script:

```routeros
/system script add name=ruleset-update source={
    /tool fetch url="https://raw.githubusercontent.com/newcoderlife/ruleset/master/chndomains.rsc" dst-path=chndomains.rsc mode=https
    /import file-name=chndomains.rsc
}
```

Run once:

```routeros
/system script run ruleset-update
```

Update daily at 04:00:

```routeros
/system scheduler add name=ruleset-update interval=1d start-time=04:00:00 on-event=ruleset-update
```

Run once after startup:

```routeros
/system scheduler add name=ruleset-update-startup interval=0s start-time=startup on-event=ruleset-update
```

## Rules

- `cn` and `noncn` are the generator inputs.
- `ruleset.cn` and `ruleset.noncn` contain shared includes.
- `local.cn` and `local.noncn` are optional local-only overrides.
- Domain entries use trailing dots, for example `twitter.com.`.

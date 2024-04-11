# Ruleset

Ruleset use with pforward log to generate non-CN domain rulset for CoreDNS.

About [PForward](https://github.com/newcoderlife/pforward).

## Usage

Install with PForward automatically.

```
cd /etc/coredns/rules/
./run.sh /var/log/coredns.log
```

Add `--refresh` to run `service coredns restart`.

Add `--update` to download latest ruleset and database.

Add `--upload` to upload local ruleset to author.

All contributions are welcome.

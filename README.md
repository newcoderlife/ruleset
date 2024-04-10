# Ruleset

Ruleset use with pforward log to generate non-CN domain rulset for pforward.

About [pforward](https://github.com/newcoderlife/pforward).

## Usage

Install with PForward automatically.

```
cd /etc/coredns/rules/
./run.sh /var/log/coredns.log
```

Add `--refresh` to run `service coredns restart`.

Add `--update` to download latest ruleset.

Add `--upload` to upload local ruleset to author.

All contributions are welcome.

# setup-uv

Covers the `setup-uv` input of `run-scrut-tests.yml`, which installs uv and
adds it to `PATH` before `scrut-setup-cmd` runs. GitHub runners do not ship uv,
so these tests fail unless the workflow installed it.

`HELLO_BIN` comes from the caller's `scrut-env`.

## uv is on PATH

```scrut
$ uv --version
uv * (glob)
```

## A PEP 723 script runs from its shebang

```scrut
$ "${HELLO_BIN}"
hello from a PEP 723 script
```

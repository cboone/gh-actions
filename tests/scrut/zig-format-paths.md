# Zig formatting paths

The fixture reads the default paths, environment binding, and formatting step
from `run-zig-ci.yml`. Each scenario runs that step under `/bin/bash` against
an isolated temporary project. `NODE_BIN` and `ZIG_FORMAT_FIXTURE` are absolute
paths supplied by the caller.

## Formatted default layout

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" formatted-default
formatted-default: passed
```

## Default paths exclude other directories

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" default-excludes-tools
default-excludes-tools: passed
```

## Formatted custom directory

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" formatted-custom
formatted-custom: passed
```

## Custom layout without a manifest

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" without-manifest
without-manifest: passed
```

## Unformatted custom directory

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" unformatted-custom
unformatted-custom: passed
```

## Unformatted manifest

The fixture also verifies that the previous command passes on this layout,
so this case specifically detects the manifest coverage gap.

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" unformatted-manifest
unformatted-manifest: passed
```

## Missing default manifest

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" missing-manifest
missing-manifest: passed
```

## Empty path list

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" empty
empty: passed
```

## Whitespace-only path list

```scrut
$ "${NODE_BIN}" "${ZIG_FORMAT_FIXTURE}" whitespace
whitespace: passed
```

# npm publish behavior

The fixture reads the production steps and their input defaults from
`publish-to-npm.yml`, `publish-to-npm-with-oidc.yml` and `deploy-to-pages.yml`,
then runs each step under `/bin/bash` with stub executables that report a
version or record the argument vector they receive. `NODE_BIN` and
`NPM_PUBLISH_FIXTURE` are absolute paths supplied by the caller.

## Trusted publishing refuses a registry that does not support it

```scrut
$ "${NODE_BIN}" "${NPM_PUBLISH_FIXTURE}" registry
registry: passed
```

## The npm and Node minimums are enforced before publishing

```scrut
$ "${NODE_BIN}" "${NPM_PUBLISH_FIXTURE}" versions
versions: passed
```

## The lockfile probe reports the lockfile it found

```scrut
$ "${NODE_BIN}" "${NPM_PUBLISH_FIXTURE}" detect
detect: passed
```

## Installs use the lockfile, skip lifecycle scripts, and refuse to guess

```scrut
$ "${NODE_BIN}" "${NPM_PUBLISH_FIXTURE}" install
install: passed
```

## The copied install and probe steps have not drifted apart

```scrut
$ "${NODE_BIN}" "${NPM_PUBLISH_FIXTURE}" parity
parity: passed
```

## Each publish workflow declares only its own mode's permissions

```scrut
$ "${NODE_BIN}" "${NPM_PUBLISH_FIXTURE}" shape
shape: passed
```

# Workflow argument binding

The fixture reads the production steps, their `env:` bindings and their input
defaults from the reusable workflows, then runs each step under `/bin/bash` with
stub executables that record the argument vector they receive. `NODE_BIN` and
`ARG_BINDING_FIXTURE` are absolute paths supplied by the caller.

## No workflow interpolates an ordinary input into a run block

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" policy
policy: passed
```

## Migrated steps declare their environment bindings

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" bindings
bindings: passed
```

## Every argument split rejects embedded newlines and expands quoted

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" guards
guards: passed
```

## The set of guarded split sites is the documented one

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" coverage
coverage: passed
```

## Shipped defaults produce the expected argument vector

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" defaults
defaults: passed
```

## A path containing spaces stays one argument

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" spaces
spaces: passed
```

## Argument boundaries survive runs of whitespace

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" boundaries
boundaries: passed
```

## Shell metacharacters are data, not syntax

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" metacharacters
metacharacters: passed
```

## Command substitutions and variables are not expanded

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" substitution
substitution: passed
```

## Globs are passed through unexpanded

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" glob
glob: passed
```

## An empty value contributes no argument

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" empty
empty: passed
```

## A multi-line value is rejected

```scrut
$ "${NODE_BIN}" "${ARG_BINDING_FIXTURE}" multiline
multiline: passed
```

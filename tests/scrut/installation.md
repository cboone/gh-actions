# Scrut installation

`SCRUT_BIN` identifies the installed executable. These assertions exercise
the installed tool, its version and its executable architecture.

## Pinned version

```scrut
$ "${SCRUT_BIN}" --version
scrut 0.4.3
```

## Executable matches the runner

```scrut
$ description="$(file -b "$(command -v "${SCRUT_BIN}")")" && case "$(uname -s)-$(uname -m)-${description}" in Linux-x86_64-*ELF*x86-64*|Linux-aarch64-*ELF*ARM*aarch64*|Linux-arm64-*ELF*ARM*aarch64*|Darwin-arm64-*Mach-O*arm64*|Darwin-x86_64-*Mach-O*x86_64*) printf 'Scrut matches runner architecture\n' ;; *) printf 'Unexpected executable: %s\n' "${description}"; exit 1 ;; esac
Scrut matches runner architecture
```

## Snapshot execution

```scrut
$ printf 'snapshot execution works\n'
snapshot execution works
```

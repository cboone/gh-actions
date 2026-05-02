# release-zig-binaries

Build a Zig binary for multiple targets and create a GitHub Release with
packaged artifacts and SHA-256 checksums. Leverages Zig's native
cross-compilation from a single runner (no matrix, no macOS runners).

`zig-version` and `zig-version-file` follow the same precedence rules as in
`run-zig-ci.yml`: `zig-version` wins if both are set, and if neither is set
`mlugg/setup-zig` falls back to its own auto-detection.

**Permissions:** `contents: write`

## Inputs

| Name               | Type   | Default         | Description                                       |
| ------------------ | ------ | --------------- | ------------------------------------------------- |
| `zig-version`      | string | `""`            | Zig version to install (e.g., `"0.15.2"`)         |
| `zig-version-file` | string | `""`            | Path to a `.zon` file with `.minimum_zig_version` |
| `binary-name`      | string |                 | Name of the binary (required)                     |
| `targets`          | string | (see below)     | Space-separated Zig target triples                |
| `optimize`         | string | `ReleaseSafe`   | Zig optimization level                            |
| `runs-on`          | string | `ubuntu-latest` | Runner label (Windows not supported)              |
| `timeout-minutes`  | number | `30`            | Job timeout in minutes                            |

Default `targets`:

```text
x86_64-linux-gnu aarch64-linux-gnu x86_64-macos aarch64-macos x86_64-windows-gnu
```

## Usage

```yaml
jobs:
  release:
    uses: cboone/gh-actions/.github/workflows/release-zig-binaries.yml@v3.0.0
    with:
      zig-version-file: build.zig.zon
      binary-name: "my-tool"
```

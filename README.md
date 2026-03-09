# Gh Actions

A collection of reusable GitHub Actions for CI/CD workflows.

## Prerequisites

- [Node.js](https://nodejs.org/) >= 20.18
- [uv](https://docs.astral.sh/uv/) (for yamllint)
- curl (for downloading actionlint)

## Setup

Install Node.js dev dependencies (prettier, markdownlint-cli2, cspell):

```bash
npm install
```

Install binary tools (actionlint):

```bash
make setup
```

## Usage

| Target              | Description                     |
| ------------------- | ------------------------------- |
| `make setup`        | Install local tool dependencies |
| `make lint`         | Lint GitHub Actions workflows   |
| `make lint-yaml`    | Lint YAML files                 |
| `make lint-md`      | Lint Markdown files             |
| `make format`       | Format with Prettier            |
| `make format-check` | Check formatting with Prettier  |
| `make spell`        | Check spelling                  |
| `make help`         | Show available targets          |

All targets auto-install their tools on first run. Node.js tools use `npx`,
yamllint uses `uv tool run`, and actionlint downloads a pinned binary to
`.local/bin/`.

## License

[MIT License](./LICENSE). TL;DR: Do whatever you want with this software, just keep the copyright notice included. The authors aren't liable if something goes wrong.

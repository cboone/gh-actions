# Documentation instructions

[development.md](development.md) owns the detailed trust model and contributor procedures. Keep it living and update it in place.

- Action references live beside `../actions/<name>/action.yml`; workflow references live in `workflows/<name>.md`. Follow the [component template](development.md#per-component-doc-template) and omit sections that do not apply.
- Root README keeps orientation, platform/version policy and flat component tables. Do not move full component reference tables there or add obsolete per-component anchor stubs.
- Follow the current documented release-tag convention for illustrative Usage examples; executable workflows and actions keep full SHA pins.
- Put breaking-change migration guides in `migrations/vN.md` and link them from the README Migration section.
- Root and scoped agent instructions contain operating rules and navigation. Keep each complete instruction chain within 32 KiB and every `CLAUDE.md` paired with its sibling `AGENTS.md`.

# Astrea Agent Rules

Project name: Astrea

Main docs directory: `docs/`

Blueprint: `PROJECT_BLUEPRINT.md`

Project memory:
`.business/`, `.idea/`, `.architecture/`, `.architect/`, `.plans/`, `.retrospectives/`, `.security/`

## Source-of-Truth Priority

1. Current user/GPT Architect instruction.
2. `PROJECT_BLUEPRINT.md`.
3. `AGENTS.md`.
4. Relevant architecture/business/plan/security docs.
5. Existing implementation.

## Rules

- `_ref/` is read-only local reference material.
- Never commit anything from `_ref/`.
- Never modify files in `_ref/`.
- Do not scan `_ref/` unless the GPT Architect explicitly requests a specific asset.
- Do not invent new branding independently.
- Do not expose candidate photos or private application data publicly.
- Do not put secrets into Git, docs, prompts or logs.
- Production data access is read-only unless explicitly approved.
- Destructive operations require explicit approval.
- Complex or multi-file implementation tasks follow Plan -> approval -> Build.
- Do not deploy without explicit approval.

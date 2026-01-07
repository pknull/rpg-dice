# Project Context

This project uses the **Asha** framework for session coordination and memory persistence.

## Quick Reference

**Framework:** Asha plugin provides CORE.md and operational protocols via SessionStart hook.

**Memory Bank:** Project context stored in `Memory/*.md` files.

## Commands

| Command | Purpose |
|---------|---------|
| `/asha:save` | Save session context to Memory Bank, archive session, refresh index, commit |
| `/asha:index` | Index files for semantic search (use `--full` for complete reindex, `--check` for dependency verification) |

## Session Workflow

1. **Start:** Read `Memory/activeContext.md` for context
2. **Work:** Operations logged automatically via hooks
3. **End:** Run `/asha:save` to synthesize and persist learnings

## Code Style

- Follow existing patterns in the codebase
- Use authority markers when uncertain: `[Inference]`, `[Speculation]`, `[Unverified]`
- Reference code locations as `file_path:line_number`


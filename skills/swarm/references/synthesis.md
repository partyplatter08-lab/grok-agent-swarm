# Synthesis guide

How the orchestrator merges worker outputs into one trustworthy deliverable.

## Why this matters

Swarms fail at the merge step more often than the fan-out step. Parallel workers happily produce confident, mutually incompatible claims. Your job is to **reconcile**, not to average or paste.

## Procedure

1. **Ingest** every unit's required return block (`Status`, `Summary`, `Evidence`, `Artifacts`, `Open questions`, `Handoff`).
2. **Index evidence** by claim. Prefer claims with paths/URLs/quotes.
3. **Dedupe** near-identical findings across units; keep the best-sourced copy.
4. **Flag conflicts** where two units disagree on a material fact.
5. **Resolve conflicts**:
   - If one side has primary evidence and the other is assertion-only → keep evidenced side.
   - If both evidenced → call out both, or spawn one verify unit.
   - Never invent a third “compromise fact.”
6. **Structure** to the user's requested format (table, report, code, plan).
7. **List gaps** explicitly. Partial swarms are honest swarms.

## Deliverable patterns

### Research survey

- Exec summary (5–10 lines)
- Comparison table
- Deep notes per topic (optional appendix)
- Sources list
- Recommendation + confidence

### Multi-perspective audit

- Ranked issue list with severity
- Tag each issue with originating perspective unit
- Dedupe cross-perspective duplicates
- Suggested fix order

### Build / scaffold

- Tree of created paths
- How to run / install
- Integration steps if worktrees are still separate
- Known incomplete pieces

## Hallucination controls

- Downrank any claim that lacks Evidence.
- Prefer worker quotes from files/pages over paraphrases when stakes are high.
- If a worker returned `Status: partial` or empty Evidence, treat content as provisional.
- Do not launder weak worker prose into authoritative voice without labels.

## Voice

The final answer is **one voice** (the orchestrator). Do not dump raw worker transcripts unless the user asked for a ledger appendix.

## Minimal quality bar before finishing

- [ ] User's original question is answered directly at the top
- [ ] Stats + unit ledger present
- [ ] Conflicts/gaps section present (even if “none”)
- [ ] No unresolved write-worktrees without a next step
- [ ] Sources or paths cited for non-trivial claims

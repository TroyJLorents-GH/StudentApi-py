# SDD Progress — replica-sync-portfolio-rbac

Plan: docs/superpowers/plans/2026-06-23-replica-sync-portfolio-rbac.md
Branch: feat/replica-sync-portfolio-rbac

## Status
- Phase 0 (DB DDL) — USER-RUN via db/migrations/2026-06-23-replica-sync.sql (both DBs)
- Task 5.1 (seed users) — included in same SQL file

## Completed
Task 1.1-1.4 (RBAC plumbing): complete (commits cc56275..4011a24, review clean)
Task 1.5-1.8 (model columns): complete (commits c283f47..fca9d5d, review clean)
Task 2.1 (analytics single-term): complete (commit 50e220b, review clean)
Task 2.2 (analytics cross-term union): complete (commit 4aa9fda, review clean). RESOLVED: /subjects extra _enroll_sections filter kept (data-quality improvement, intentional).
Task 3.1-3.2 (chat prep): complete (commits 8254c26..e4bf170 + fix 73c9639, review clean after fix)
Task 3.3 (chat read-only port): complete (commit da899a1 + fix 16987da, review clean after fix). RESOLVED: assign_capability kept — it's live SYSTEM_PROMPT context (RBAC-aware), chat has no write tools so structurally read-only.
Task 4.1 (scrub real values): complete (commit 3a0aec0 + BOM fix 01f5ea0, review clean). RESOLVED: TA lump-sum comp figures in calculate_compensation faked to round synthetic values (8093->8000, 17600->16000, 8800->8500, 13461.15->13000, 6730.58->6500, 6636->6000, 7250->7000, 13272->12000, 14500->14000). Grader/IA already session-derived.
Task 5.2 (Login role-picker): complete (commit 0d64854 in ui-student-py, reviewed inline clean). Task 5.3: no-op (analytics components pre-synced). Empty placeholder commit dropped.
ALL PLAN TASKS COMPLETE — final whole-branch review next.
Final whole-branch review: READY TO MERGE (no Critical/Important). M1 ACTIVE_TERM pinned (2254, data lives there). Migration updated to create ClassSchedule2264. Gateway live-tested 200/pong. Open: lump-sum scrub (pre-deploy fast-follow), B trim assign_capability (optional).

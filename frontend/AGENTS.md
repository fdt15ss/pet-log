# AGENTS.md

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- Before hand-rolling core logic, first check proven packages, standard libraries, and existing project utilities.
- If a package or local utility already fits the need, use it instead of custom implementation.
- If custom implementation is still chosen, state the reason and keep the scope narrow.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
# Repository Agents Guide

Keep this file short and repo-wide. Put workflow details in repo-local skills and harness docs.

## What

- Pet Log is an AI-first pet care product. The MVP should prove analysis and action suggestions, not just manual record storage.
- Canonical product source from the repo root: `기획.md` (`frontend` 기준 `../기획.md`).
- Canonical visual references from the repo root: `pet-log-ui.png` and `펫로그_20260428/*` (`frontend` 기준 `../pet-log-ui.png`, `../펫로그_20260428/*`).
- Harness entry point: `.agents/skills/pet-log-mvp-orchestrator/SKILL.md`.
- Team contract: `docs/harness/pet-log-mvp/team-spec.md`.
- Web app path: repo root 기준 `frontend/app/web`, `frontend` 기준 `app/web`, with Next.js App Router, TypeScript, ESLint, Tailwind CSS, and Turbopack dev server.

## Why

- The product differentiator is the loop from record input to interpretation to practical care guidance.
- MVP work should protect that differentiator by prioritizing home summary, natural-language logging, timeline, analysis, AI suggestions, and pet profile.
- Community, commerce, hospital integration, IoT, map, shared care, and money management are expansion candidates unless a task explicitly changes scope.

## How

- Use `_workspace/` markdown handoffs for product, UX, AI, build, and QA artifacts.
- Prefer repo-local Pet Log skills under `.agents/skills/` before generic planning or implementation workflows.
- Web commands run from `frontend/app/web` at repo root, or `app/web` when already inside `frontend`: `npm run dev`, `npm run lint`, `npm run typecheck`, and `npm run build`.
- HTTP/API 통신은 `axios`를 사용한다. 브라우저 클라이언트, Next Route Handler의 서버 간 요청, 통신 경계 테스트 모두 `fetch` 직접 호출보다 기존 axios 경계를 우선한다.

## md 파일 작성 규칙
- 한글로 작성할것

## Git 규칙
- 커밋 메시지 작성
- 승인후 커밋

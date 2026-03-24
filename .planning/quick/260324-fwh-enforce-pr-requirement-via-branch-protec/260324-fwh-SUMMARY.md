---
phase: quick
plan: 260324-fwh
subsystem: github-branch-protection
tags: [branch-protection, rulesets, enforce-admins, security]
dependency_graph:
  requires: [260323-ljx]
  provides: [enforce-admins, no-bypass-ruleset]
  affects: [hdwhdw/sonic-buildcop main branch]
tech_stack:
  added: []
  patterns: [two-layer-branch-protection, ruleset-no-bypass]
key_files:
  created: []
  modified: []
decisions:
  - "Two-layer enforcement: branch protection enforce_admins + repository ruleset with empty bypass_actors"
  - "Ruleset ID 14286894 created for 'Require PR for main'"
metrics:
  duration: 53s
  completed: "2026-03-24T16:32:10Z"
  tasks_completed: 2
  tasks_total: 2
---

# Quick Task 260324-fwh: Enforce PR Requirement via Branch Protection Summary

**One-liner:** Two-layer PR enforcement on `hdwhdw/sonic-buildcop` main — enforce_admins=true plus "Require PR for main" ruleset with zero bypass actors

## What Was Done

### Task 1: Enable enforce_admins and create no-bypass ruleset

1. **Enabled `enforce_admins`** on existing branch protection rule via `POST repos/hdwhdw/sonic-buildcop/branches/main/protection/enforce_admins`
   - Result: `"enabled": true`

2. **Created repository ruleset** "Require PR for main" (ID: 14286894) via `POST repos/hdwhdw/sonic-buildcop/rulesets`
   - Enforcement: `active`
   - Target: `refs/heads/main`
   - Rules: `pull_request` (1 required approval)
   - Bypass actors: `[]` (empty — no one can bypass)
   - `current_user_can_bypass`: `"never"`

### Task 2: Verify full protection state

Final verified state:

**Branch Protection:**
| Setting | Value |
|---------|-------|
| enforce_admins | ✅ true |
| required_pr_reviews | 1 |
| strict_status_checks | true |
| allow_force_pushes | false |
| allow_deletions | false |

**Repository Ruleset "Require PR for main":**
| Setting | Value |
|---------|-------|
| enforcement | active |
| target | branch (refs/heads/main) |
| bypass_actors | [] (empty) |
| current_user_can_bypass | never |
| rules | pull_request (1 approval) |

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

- `enforce_admins: PASS` — enabled is true
- `ruleset: PASS` — "Require PR for main" exists with 0 bypass actors
- `ALL CHECKS PASS: enforce_admins=true, ruleset has 0 bypass actors`

## Why Two Layers

For personal (User-owned) repos, branch protection `enforce_admins` may not fully prevent the owner from bypassing. Repository rulesets with empty `bypass_actors` provide stronger enforcement. Both are applied for defense in depth.

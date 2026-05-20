---
name: verify-answer
description: "Protocol for verifying that every factual claim has a grep-verifiable path:LINE — anchor citation. Use when reviewing answers for citation completeness."
validated-at: 70d99e998b4
---

# Verify-Answer Skill
## Purpose
Protocol for verifying that all factual claims have valid `path:LINE — anchor phrase` citations.

## Verification Rules
1. Every "how does X work" answer must include at least one citation.
2. Citations must be grep-verifiable: `grep -n "anchor phrase" path` must return a match.
3. "I think" / "probably" / "should" are red flags — never use without a citation.
4. Opinions are acceptable for design trade-offs; never for mechanism descriptions.

## Citation Format
```
path/to/file.py:LINE — "anchor_phrase_verbatim_from_source"
```

## How to Verify a Citation
```bash
grep -n "anchor_phrase" path/to/file.py
```
If grep returns nothing: citation is stale. Update it using symbol-locator or question-solver.

## Staleness Detection
- If line number changed but phrase still exists: DRIFT (update line number)
- If phrase missing from file: MISSING (re-investigate)
- If file moved: run `git log --follow -- old_path` to find new location

## Questions.md Update
After verifying a citation:
1. Update `questions.md` status from `open` → `answered-with-proof`
2. Add the citation in the Citation column

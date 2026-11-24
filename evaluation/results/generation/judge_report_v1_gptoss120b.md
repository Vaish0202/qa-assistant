# Generation quality (judge: groq:openai/gpt-oss-120b)

| Output | n | Correctness | Groundedness | Actionability | Judge: ≥1 unsupported claim | Rule check: ≥1 unsupported fact |
|---|---:|---:|---:|---:|---:|---:|
| Jira drafts (bug) | 15 | 4.87 | 2.73 | 4.00 | 100% | 20% |
| Fix suggestions (failed_testcase) | 15 | 4.73 | 2.73 | 4.93 | 100% | 0% |
| All | 30 | 4.80 | 2.73 | 4.47 | 100% | 10% |

## Lowest-scored outputs

| Case | C | G | A | Why (correctness) | Unsupported facts (rule check) |
|---|---:|---:|---:|---|---|
| gh-pechst1-conversationallanguagelearning-813 | 3 | 1 | 3 | Identifies the application (grader) as buggy, matching the reference, but adds speculative |  |
| syn-unit-failed_testcase-012 | 3 | 1 | 4 | Identifies floating‑point precision as the issue but incorrectly blames the apply_coupon i |  |
| syn-playwright-bug-007 | 5 | 1 | 3 | Correctly identifies the application bug causing a 500 error redirect. |  |
| syn-playwright-bug-004 | 5 | 3 | 3 | Correctly identifies the application bug causing a 500 error and redirect to the error pag |  |
| syn-selenium-bug-014 | 5 | 3 | 3 | Correctly identifies the application bug causing the wrong total value. |  |

Scores are 1-5 means. Judge scores are not yet validated against human labels (see Cohen's kappa, Step 5).

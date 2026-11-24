# Generation quality (judge: groq:qwen/qwen3.8-27b)

| Output | n | Correctness | Groundedness | Actionability | Judge: ≥1 unsupported claim | Rule check: ≥1 unsupported fact |
|---|---:|---:|---:|---:|---:|---:|
| Jira drafts (bug) | 15 | 5.00 | 4.60 | 4.87 | 20% | 20% |
| Fix suggestions (failed_testcase) | 15 | 5.00 | 5.00 | 5.00 | 0% | 0% |
| All | 30 | 5.00 | 4.80 | 4.93 | 10% | 10% |

## Lowest-scored outputs

| Case | C | G | A | Why (correctness) | Unsupported facts (rule check) |
|---|---:|---:|---:|---|---|
| syn-unit-bug-011 | 5 | 3 | 5 | The output correctly identifies that the application code is at fault for raising a KeyErr |  |
| syn-playwright-bug-013 | 5 | 3 | 5 | The output correctly identifies that the application is failing by redirecting to an error |  |
| syn-selenium-bug-005 | 5 | 3 | 5 | The output correctly identifies that the application is buggy because the displayed total  |  |
| gh-pechst1-conversationallanguagelearning-813 | 5 | 5 | 3 | The output correctly identifies that the application's grading logic is flawed (returning  |  |
| gh-jaylfc-taos-4259 | 5 | 5 | 5 | The output correctly identifies that the application is at fault for returning a 200 statu |  |

Scores are 1-5 means. Judge scores are not yet validated against human labels (see Cohen's kappa, Step 5).

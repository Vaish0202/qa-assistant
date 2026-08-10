import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.graph import run_analysis
from sample_data.test_cases import TEST_CASES
import json
import time
import csv
from datetime import datetime

def run_full_evaluation():
    results = []
    correct_classifications = 0
    total = len(TEST_CASES)

    print("="*60)
    print("QA ASSISTANT — FULL EVALUATION RUN")
    print(f"Total test cases: {total}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    for i, tc in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{total}] Running {tc['id']}...")

        start_time = time.time()

        try:
            result = run_analysis(
                testcase_logs=tc['testcase_logs'],
                testcase_description=tc['testcase_description'],
                testcase_code=tc['testcase_code'],
                user_id="eval_run"
            )

            elapsed = round(time.time() - start_time, 2)

            got = result.get('classification', 'unknown')
            expected = tc['expected']
            is_correct = got == expected

            if is_correct:
                correct_classifications += 1

            final = result.get('final_output', {})
            action = final.get('action', 'unknown')

            # Suggestion quality — auto score based on content
            suggestions = final.get('suggestions', []) or final.get('changes_made', [])
            improved_code = final.get('improved_code', '') or final.get('fixed_code', '')
            sugg_quality = score_suggestion_quality(suggestions, improved_code)

            row = {
                "test_id": tc['id'],
                "expected": expected,
                "got": got,
                "correct": "✓" if is_correct else "✗",
                "confidence": round(result.get('classification_confidence', 0), 2),
                "analysis_type": result.get('analysis_type', 'N/A'),
                "action": action,
                "suggestion_quality": sugg_quality,
                "time_seconds": elapsed,
                "jira_ticket": final.get('jira_ticket', 'N/A'),
                "reason": tc.get('reason', '')
            }

            results.append(row)

            print(f"  Expected : {expected}")
            print(f"  Got      : {got} {'✓' if is_correct else '✗ WRONG'}")
            print(f"  Time     : {elapsed}s")
            print(f"  Action   : {action}")
            if final.get('jira_ticket'):
                print(f"  Jira     : {final.get('jira_url')}")

        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            print(f"  ERROR: {str(e)}")
            results.append({
                "test_id": tc['id'],
                "expected": tc['expected'],
                "got": "error",
                "correct": "✗",
                "confidence": 0,
                "analysis_type": "error",
                "action": "error",
                "suggestion_quality": 0,
                "time_seconds": elapsed,
                "jira_ticket": "N/A",
                "reason": str(e)
            })

    # Print summary table
    print_summary(results, correct_classifications, total)

    # Save to CSV
    save_csv(results)

    return results, correct_classifications, total

def score_suggestion_quality(suggestions: list, improved_code: str) -> int:
    """
    Auto-score suggestion quality 1-5:
    1 = nothing generated
    2 = minimal content
    3 = suggestions present
    4 = suggestions + code
    5 = suggestions + code + alternatives
    """
    score = 1
    if suggestions:
        score = 3
    if improved_code and len(improved_code) > 50:
        score = 4
    if suggestions and improved_code and len(suggestions) >= 2:
        score = 5
    return score

def print_summary(results, correct, total):
    accuracy = round((correct / total) * 100, 1)
    avg_time = round(sum(r['time_seconds'] for r in results) / total, 2)
    avg_quality = round(sum(r['suggestion_quality'] for r in results) / total, 1)

    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"{'Test ID':<12} {'Expected':<18} {'Got':<18} {'OK':<4} {'Time':>6} {'Quality':>8}")
    print("-"*60)

    for r in results:
        print(
            f"{r['test_id']:<12} "
            f"{r['expected']:<18} "
            f"{r['got']:<18} "
            f"{r['correct']:<4} "
            f"{r['time_seconds']:>5}s "
            f"{r['suggestion_quality']:>7}/5"
        )

    print("-"*60)
    print(f"\nClassification Accuracy : {correct}/{total} = {accuracy}%")
    print(f"Average Processing Time : {avg_time}s")
    print(f"Average Suggestion Qual : {avg_quality}/5")
    print(f"Jira Tickets Created    : {sum(1 for r in results if r['jira_ticket'] != 'N/A')}")

def save_csv(results):
    filename = f"evaluation/eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames = [
        "test_id", "expected", "got", "correct",
        "confidence", "analysis_type", "action",
        "suggestion_quality", "time_seconds", "jira_ticket", "reason"
    ]

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✓ Results saved to: {filename}")
    print("  Use this CSV directly in your paper's evaluation table")

if __name__ == "__main__":
    run_full_evaluation()
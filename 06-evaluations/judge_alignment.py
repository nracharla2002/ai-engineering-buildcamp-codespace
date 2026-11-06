import json
from pathlib import Path

with Path("results_judged.json").open(encoding="utf-8") as f:
    judged_results = json.load(f)

with Path("results_labeled.json").open(encoding="utf-8") as f:
    human_results = json.load(f)

# Build lookup tables and ensure each question is unique.
judge_by_question = {row["question"]: row for row in judged_results}
human_by_question = {row["question"]: row for row in human_results}

if len(judge_by_question) != len(judged_results):
    raise ValueError("Duplicate questions found in results_judged.json")
if len(human_by_question) != len(human_results):
    raise ValueError("Duplicate questions found in results_labeled.json")

if judge_by_question.keys() != human_by_question.keys():
    raise ValueError("The two files do not contain the same questions")

tp = fp = fn = tn = 0

for question, judge_row in judge_by_question.items():
    judge_label = judge_row.get("judge_label")
    human_label = human_by_question[question].get("label")

    if judge_label not in {"good", "bad"} or human_label not in {"good", "bad"}:
        raise ValueError(f"Missing or invalid label for: {question}")

    print(f"\nQuestion: {question}")
    print(f"Human label: {human_label}")
    print(f"Judge label: {judge_label}")
    print(f"Judge reasoning: {judge_row.get('judge_reasoning', 'No reasoning provided')}")

    if judge_label == "bad" and human_label == "bad":
        tp += 1
    elif judge_label == "bad" and human_label == "good":
        fp += 1
    elif judge_label == "good" and human_label == "bad":
        fn += 1
    else:  # judge_label == "good" and human_label == "good"
        tn += 1

total = tp + fp + fn + tn
accuracy = (tp + tn) / total if total else 0
precision = tp / (tp + fp) if (tp + fp) else 0
recall = tp / (tp + fn) if (tp + fn) else 0

print(f"Results compared: {total}")
print(f"TP: {tp}  FP: {fp}")
print(f"FN: {fn}  TN: {tn}")
print(f"Accuracy:  {accuracy:.2%}")
print(f"Precision: {precision:.2%}")
print(f"Recall:    {recall:.2%}")

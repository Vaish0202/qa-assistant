import json
with open("evaluation/results/generation/judgments.jsonl", encoding="utf-8") as f:
    for j in list(map(json.loads, f))[:8]:
        print(f"\n{j['id']}  G={j['groundedness']}  {j['groundedness_reason']}")
        for c in j["unsupported_claims"][:4]:
            print("   -", c)
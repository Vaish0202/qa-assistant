"""
The three classification pipelines the evaluation compares.

    xgboost   the trained XGBoost model (52 hand-made features)
    llm       the LLM alone, using the classifier agent's framework prompt
    hybrid    XGBoost first; if its confidence is below a threshold, ask the
              LLM instead (confidence-gated fallback)

Every predictor takes one dataset record and returns
    {"pred": "bug" | "failed_testcase" | None, "confidence": float | None,
     "seconds": float, "source": str, "error": str | None}
pred=None means "no usable answer"; metrics count it as wrong ("unparsed").
"""
import contextlib
import hashlib
import io
import json
import os
import re
import time

from evaluation.datasets import dataset_io

LABELS = ("bug", "failed_testcase")
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "cache")


# ------------------------------------------------------------------ xgboost
def predict_xgboost(record):
    from ml_classifier.predict import predict_classification
    inp = dataset_io.to_pipeline_input(record)
    start = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()):          # it prints a line
        out = predict_classification(inp["testcase_logs"],
                                     inp["testcase_description"],
                                     inp["testcase_code"])
    return {"pred": out["classification"], "confidence": out["confidence"],
            "seconds": time.perf_counter() - start, "source": "xgboost", "error": None}


# ---------------------------------------------------------------------- llm
def parse_label(text):
    """Read 'bug' or 'failed_testcase' from an LLM answer, or None."""
    text = text or ""
    # 1. a JSON object with "classification"
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            value = str(json.loads(match.group()).get("classification", "")).strip().lower()
            if value in LABELS:
                return value
        except (json.JSONDecodeError, AttributeError):
            pass
    # 2. "classification": "..." without valid JSON around it
    match = re.search(r'"?classification"?\s*[:=]\s*"?(bug|failed_testcase)', text, re.I)
    if match:
        return match.group(1).lower()
    # 3. exactly one of the two labels appears in the text
    found = {lbl for lbl in LABELS if re.search(rf"\b{lbl}\b", text, re.I)}
    return found.pop() if len(found) == 1 else None


class LLMPredictor:
    """The classifier agent's prompt, sent straight to the LLM.

    Answers are cached on disk per model, so re-running the evaluation (or
    the hybrid pipeline after the llm pipeline) doesn't call the LLM again
    for the same case. Delete evaluation/results/cache/ to force fresh calls.
    """

    def __init__(self):
        from agents.llm import get_llm, get_model_info
        info = get_model_info()
        self.name = f"{info['provider']}:{info['model']}"
        with contextlib.redirect_stdout(io.StringIO()):      # get_llm prints a line
            self.llm = get_llm()
        os.makedirs(CACHE_DIR, exist_ok=True)
        safe = re.sub(r"[^\w.-]", "_", self.name)
        self.cache_path = os.path.join(CACHE_DIR, f"llm_{safe}.jsonl")
        self.cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, encoding="utf-8") as f:
                for line in f:
                    row = json.loads(line)
                    self.cache[row["key"]] = row["result"]

    @staticmethod
    def _key(record):
        """Case id + hash of its content: an edited case is asked again."""
        text = json.dumps(dataset_io.to_pipeline_input(record), sort_keys=True)
        return f"{record['id']}:{hashlib.sha256(text.encode()).hexdigest()[:12]}"

    @staticmethod
    def _messages(record):
        from langchain_core.messages import HumanMessage, SystemMessage
        from agents.framework_detector import detect_framework
        from agents.prompts import CLASSIFIER_PROMPTS, get_prompt
        inp = dataset_io.to_pipeline_input(record)
        with contextlib.redirect_stdout(io.StringIO()):
            framework = detect_framework(inp["testcase_logs"], inp["testcase_code"],
                                         inp["testcase_description"])["framework"]
        return [SystemMessage(content=get_prompt(CLASSIFIER_PROMPTS, framework)),
                HumanMessage(content=(
                    f"FRAMEWORK: {framework}\n"
                    f"DESCRIPTION: {inp['testcase_description']}\n"
                    f"LOGS: {inp['testcase_logs']}\n"
                    f"CODE: {inp['testcase_code']}"))]

    def __call__(self, record):
        key = self._key(record)
        if key in self.cache:
            return {**self.cache[key], "cached": True}
        start = time.perf_counter()
        try:
            response = self.llm.invoke(
                self._messages(record),
                config={"tags": ["evaluation"],
                        "metadata": {"case_id": record["id"], "dataset_split": record["split"]}})
            pred, error = parse_label(response.content), None
        except Exception as e:                   # count as wrong, keep going
            pred, error = None, f"{type(e).__name__}: {str(e)[:150]}"
        result = {"pred": pred, "confidence": None,
                  "seconds": time.perf_counter() - start, "source": "llm", "error": error}
        if error is None:                        # never cache a failed call
            with open(self.cache_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "result": result}) + "\n")
            self.cache[key] = result
        return result


# ------------------------------------------------------------------- hybrid
def make_hybrid(llm_predictor, threshold):
    def hybrid(record):
        x = predict_xgboost(record)
        if x["confidence"] >= threshold:
            return x
        answer = llm_predictor(record)
        return {**answer, "seconds": x["seconds"] + answer["seconds"],
                "source": "llm (fallback)"}
    return hybrid
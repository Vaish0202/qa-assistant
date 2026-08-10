import { useState } from "react";
import { analyzeTestcase } from "../api";
import ResultCard from "../components/ResultCard";

export default function Analyze() {
  const [logs, setLogs] = useState("");
  const [description, setDescription] = useState("");
  const [code, setCode] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const userId = localStorage.getItem("user_id") || "default_user";

  const handleAnalyze = async () => {
    if (!logs || !description || !code) {
      setError("Please fill in all three fields");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await analyzeTestcase({
        user_id: userId,
        testcase_logs: logs,
        testcase_description: description,
        testcase_code: code,
      });
      setResult(res.data);
      // setResult(res.data)
      console.log('Full result:', JSON.stringify(res.data,
      null, 2))
    } catch (err) {
      setError(
        err.response?.data?.detail || "Analysis failed. Is the API running?",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setLogs("");
    setDescription("");
    setCode("");
    setResult(null);
    setError("");
  };

  const loadExample = () => {
    setLogs(
      "AssertionError: assert 150.00 == 120.00\nCart total mismatch: expected 120.00 got 150.00",
    );
    setDescription("Test verifies cart total is correct sum of items added");
    setCode(
      `def test_checkout_total(driver):\n    total = driver.find_element(By.ID, 'cart-total').text\n    assert float(total) == 120.00`,
    );
    setResult(null);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">
            Analyze Test Failure
          </h1>
          <p className="text-gray-400 mt-1">
            Paste your failing test details. AI will classify and diagnose
            automatically.
          </p>
        </div>
        <button
          onClick={handleClear}
          className="text-sm bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition"
        >
          Clear / New Analysis
        </button>
      </div>
      <button
        onClick={loadExample}
        className="mb-4 text-sm text-blue-400 hover:text-blue-300 underline"
      >
        Load example test failure
      </button>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Test Logs / Error Output *
          </label>
          <textarea
            rows={4}
            value={logs}
            onChange={(e) => setLogs(e.target.value)}
            placeholder="Paste your test error logs here..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-mono text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Test Case Description *
          </label>
          <textarea
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What is this test supposed to verify?"
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Test Case Code *
          </label>
          <textarea
            rows={6}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Paste your test code here..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-mono text-sm"
          />
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white font-semibold py-4 rounded-lg transition text-lg"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="animate-spin h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8v8H4z"
                />
              </svg>
              Analyzing... (may take 30-60s with local AI)
            </span>
          ) : (
            "Analyze Test Failure"
          )}
        </button>
      </div>
      <ResultCard result={result} />
      
    </div>
  );
}

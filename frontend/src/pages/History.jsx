import { useState, useEffect } from "react";
import { getHistory } from "../api";
import { useNavigate } from "react-router-dom";


export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [search, setSearch] = useState("");
  const userId = localStorage.getItem("user_id") || "default_user";
  const navigate = useNavigate();

  useEffect(() => {
    getHistory(userId)
      .then((res) => setHistory(res.data.analyses || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = history.filter(
    (item) =>
      !search ||
      item.classification?.includes(search.toLowerCase()) ||
      item.analysis_type?.includes(search.toLowerCase()) ||
      item.id?.includes(search),
  );

  const getStatusBadge = (classification) => {
    if (classification === "bug")
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-red-400 bg-red-900/30 border border-red-700 px-2 py-0.5 rounded-full">
          🐛 Bug Detected
        </span>
      );
    if (classification === "failed_testcase")
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-yellow-400 bg-yellow-900/30 border border-yellow-700 px-2 py-0.5 rounded-full">
          ⚠️ Test Issue
        </span>
      );
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-green-400 bg-green-900/30 border border-green-700 px-2 py-0.5 rounded-full">
        ✓ Passed
      </span>
    );
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Analysis History</h1>
        <p className="text-[#6b7280] text-sm mt-1">
          View and manage your past test failure analyses
        </p>
      </div>

      {/* Search + filters */}
      <div className="flex gap-3 mb-6">
        <div className="flex-1 relative">
          <svg
            className="w-4 h-4 absolute left-3 top-3 text-[#6b7280]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by test case, issue, or analysis ID..."
            className="w-full bg-[#13131f] border border-[#2a2a3d] rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>
        <select className="bg-[#13131f] border border-[#2a2a3d] rounded-xl px-4 py-2.5 text-[#9ca3af] text-sm focus:outline-none focus:border-indigo-500">
          <option>All Status</option>
          <option>Bug Detected</option>
          <option>Test Issue</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#2a2a3d]">
              {[
                "ID",
                "Test Case",
                "Status",
                "Classification",
                "Severity",
                "Analyzed On",
                "Actions",
              ].map((h) => (
                <th
                  key={h}
                  className="text-left text-xs font-medium text-[#6b7280] px-4 py-3"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={7}
                  className="text-center text-[#6b7280] py-8 text-sm"
                >
                  Loading...
                </td>
              </tr>
            )}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-16">
                  <div className="text-4xl mb-3">📭</div>
                  <p className="text-[#6b7280] text-sm">No analyses yet</p>
                </td>
              </tr>
            )}
            {filtered.map((item, i) => (
              <>
                <tr
                  key={item.id}
                  onClick={() => {
                    if (item.session_id) {
                      navigate(`/chat/${item.session_id}`);
                    } else {
                      setExpanded(expanded === item.id ? null : item.id);
                    }
                  }}
                  className={`border-b border-[#2a2a3d] hover:bg-[#1e1e30] cursor-pointer transition ${
                    i % 2 === 0 ? "" : "bg-[#13131f]"
                  }`}
                >
                  <td className="px-4 py-3 text-xs text-[#6b7280] font-mono">
                    AN-{item.id?.slice(-8).toUpperCase()}
                  </td>
                  <td className="px-4 py-3 text-sm text-white">
                    {item.analysis_type || "Test Analysis"}
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(item.classification)}
                  </td>
                  <td className="px-4 py-3 text-sm text-[#9ca3af]">
                    {item.classification === "bug"
                      ? "Product Bug"
                      : item.classification === "failed_testcase"
                        ? "Test Issue"
                        : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-orange-400">Medium</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-[#6b7280]">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-[#6b7280] hover:text-white">
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                    </button>
                  </td>
                </tr>
                {expanded === item.id && (
                  <tr key={`${item.id}-expanded`} className="bg-[#1e1e30]">
                    <td colSpan={7} className="px-6 py-4">
                      <div className="text-sm space-y-1">
                        <p className="text-[#6b7280]">
                          Full ID:{" "}
                          <span className="text-white font-mono">
                            {item.id}
                          </span>
                        </p>
                        <p className="text-[#6b7280]">
                          Framework:{" "}
                          <span className="text-indigo-400">
                            {item.framework || "unknown"}
                          </span>
                        </p>
                        {item.alert && (
                          <p className="text-blue-400">{item.alert}</p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>

        {filtered.length > 0 && (
          <div className="px-4 py-3 border-t border-[#2a2a3d] flex justify-between items-center">
            <p className="text-xs text-[#6b7280]">
              Showing 1 to {filtered.length} of {filtered.length} results
            </p>
            <div className="flex gap-1">
              <button className="w-7 h-7 bg-indigo-600 text-white text-xs rounded flex items-center justify-center">
                1
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

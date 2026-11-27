import { useState, useEffect, Fragment } from "react";
import { getHistory } from "../api";
import { useNavigate } from "react-router-dom";

const SEVERITY_COLOR = {
  critical: "text-red-500",
  high: "text-orange-400",
  medium: "text-yellow-400",
  low: "text-green-400",
};

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const navigate = useNavigate();

  useEffect(() => {
    getHistory()
      .then((res) => setHistory(res.data.analyses || []))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = history.filter((item) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      item.classification?.toLowerCase().includes(q) ||
      item.analysis_type?.toLowerCase().includes(q) ||
      item.framework?.toLowerCase().includes(q) ||
      item.id?.toLowerCase().includes(q);
    const matchesStatus = statusFilter === "all" || item.classification === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (classification) => {
    if (classification === "bug")
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-red-400 bg-red-900/30 border border-red-700 px-2 py-0.5 rounded-full w-fit">
          🐛 Bug Detected
        </span>
      );
    if (classification === "failed_testcase")
      return (
        <span className="flex items-center gap-1 text-xs font-medium text-yellow-400 bg-yellow-900/30 border border-yellow-700 px-2 py-0.5 rounded-full w-fit">
          ⚠️ Test Issue
        </span>
      );
    return (
      <span className="flex items-center gap-1 text-xs font-medium text-gray-400 bg-gray-800/40 border border-gray-700 px-2 py-0.5 rounded-full w-fit">
        Unknown
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
            placeholder="Search by type, framework, or analysis ID..."
            className="w-full bg-[#13131f] border border-[#2a2a3d] rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-[#13131f] border border-[#2a2a3d] rounded-xl px-4 py-2.5 text-[#9ca3af] text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="all">All Status</option>
          <option value="bug">Bug Detected</option>
          <option value="failed_testcase">Test Issue</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#2a2a3d]">
              {["ID", "Type", "Status", "Classification", "Severity", "Analyzed On", "Actions"].map((h) => (
                <th key={h} className="text-left text-xs font-medium text-[#6b7280] px-4 py-3">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={7} className="text-center text-[#6b7280] py-8 text-sm">
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
              <Fragment key={item.id}>
                <tr
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
                    {item.analysis_type || "—"}
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(item.classification)}</td>
                  <td className="px-4 py-3 text-sm text-[#9ca3af]">
                    {item.classification === "bug"
                      ? "Product Bug"
                      : item.classification === "failed_testcase"
                        ? "Test Issue"
                        : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs capitalize ${
                        SEVERITY_COLOR[item.severity?.toLowerCase()] || "text-gray-400"
                      }`}
                    >
                      {item.severity || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-[#6b7280]">
                    {item.created_at ? new Date(item.created_at).toLocaleString() : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {item.session_id && (
                      <button
                        title="View full analysis"
                        onClick={(e) => {
                          e.stopPropagation(); // don't also open the chat
                          navigate(`/analysis/${item.session_id}`);
                        }}
                        className="text-[#6b7280] hover:text-white"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
                    )}
                  </td>
                </tr>
                {expanded === item.id && (
                  <tr className="bg-[#1e1e30]">
                    <td colSpan={7} className="px-6 py-4">
                      <div className="text-sm space-y-1">
                        <p className="text-[#6b7280]">
                          Full ID: <span className="text-white font-mono">{item.id}</span>
                        </p>
                        <p className="text-[#6b7280]">
                          Framework:{" "}
                          <span className="text-indigo-400">{item.framework || "unknown"}</span>
                        </p>
                        {item.alert && <p className="text-blue-400">{item.alert}</p>}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>

        {filtered.length > 0 && (
          <div className="px-4 py-3 border-t border-[#2a2a3d]">
            <p className="text-xs text-[#6b7280]">
              Showing {filtered.length} of {history.length} analyses
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
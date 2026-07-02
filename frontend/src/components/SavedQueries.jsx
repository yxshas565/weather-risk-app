import { useEffect, useState } from "react";
import api from "../api";

export default function SavedQueries({ refreshSignal, onSelect, activeId }) {
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletedMsg, setDeletedMsg] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .listWeatherQueries()
      .then((data) => {
        if (!cancelled) setQueries(data);
      })
      .catch((err) => !cancelled && setError(err.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [refreshSignal]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await api.deleteWeatherQuery(id);
      setQueries((qs) => qs.filter((q) => q.id !== id));
      setDeletedMsg("Deleted.");
      setTimeout(() => setDeletedMsg(null), 2000);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <div className="card">Loading saved queries...</div>;
  if (error) return <div className="card error-banner">{error}</div>;
  if (queries.length === 0) return null;

  return (
    <div className="card saved-queries">
      <h3>Saved Weather Queries</h3>
      {deletedMsg && <p className="inline-msg">{deletedMsg}</p>}
      <table className="queries-table">
        <thead>
          <tr>
            <th>Location</th>
            <th>Date Range</th>
            <th>Export</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {queries.map((q) => (
            <tr
              key={q.id}
              className={q.id === activeId ? "active-row" : ""}
              onClick={() => onSelect(q)}
            >
              <td>{q.resolved_name}</td>
              <td>
                {q.start_date.slice(0, 10)} → {q.end_date.slice(0, 10)}
              </td>
              <td onClick={(e) => e.stopPropagation()}>
                {["json", "csv", "xml", "markdown", "pdf"].map((fmt) => (
                  <a
                    key={fmt}
                    href={api.exportUrl(q.id, fmt)}
                    target="_blank"
                    rel="noreferrer"
                    className="export-link"
                  >
                    {fmt}
                  </a>
                ))}
              </td>
              <td>
                <button className="danger-btn small" onClick={(e) => handleDelete(q.id, e)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { useEffect, useState } from "react";
import api from "../api";

const toDateInputValue = (isoString) => isoString.slice(0, 10);

const formatDate = (isoString) => {
  const d = new Date(isoString);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
};

export default function SavedQueries({ refreshSignal, onSelect, activeId }) {
  const [queries, setQueries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletedMsg, setDeletedMsg] = useState(null);

  const [editingId, setEditingId] = useState(null);
  const [editStart, setEditStart] = useState("");
  const [editEnd, setEditEnd] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

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

  const startEdit = (q, e) => {
    e.stopPropagation();
    setEditingId(q.id);
    setEditStart(toDateInputValue(q.start_date));
    setEditEnd(toDateInputValue(q.end_date));
  };

  const cancelEdit = (e) => {
    e.stopPropagation();
    setEditingId(null);
  };

  const saveEdit = async (id, e) => {
    e.stopPropagation();
    if (!editStart || !editEnd) return;
    setSavingEdit(true);
    try {
      const updated = await api.updateWeatherQuery(id, {
        start_date: `${editStart}T00:00:00`,
        end_date: `${editEnd}T00:00:00`,
      });
      setQueries((qs) => qs.map((q) => (q.id === id ? updated : q)));
      setEditingId(null);
      if (activeId === id) onSelect(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingEdit(false);
    }
  };

  if (loading) return <div className="card">Loading saved queries...</div>;
  if (error) return <div className="card error-banner">{error}</div>;
  if (queries.length === 0) return null;

  return (
    <div className="card saved-queries">
      <h3>Saved Weather Queries</h3>
      {deletedMsg && <p className="inline-msg">{deletedMsg}</p>}

      <div className="query-list">
        {queries.map((q) => (
          <div
            key={q.id}
            className={`query-row ${q.id === activeId ? "active-row" : ""}`}
            onClick={() => onSelect(q)}
          >
            <div className="query-row-main">
              <span className="query-location" title={q.resolved_name}>
                {q.resolved_name}
              </span>

              {editingId === q.id ? (
                <div className="edit-date-row" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="date"
                    value={editStart}
                    onChange={(e) => setEditStart(e.target.value)}
                  />
                  <span className="date-sep">to</span>
                  <input
                    type="date"
                    value={editEnd}
                    onChange={(e) => setEditEnd(e.target.value)}
                  />
                </div>
              ) : (
                <span className="date-pill">
                  {formatDate(q.start_date)} <span className="date-arrow">→</span> {formatDate(q.end_date)}
                </span>
              )}

              <div className="export-links" onClick={(e) => e.stopPropagation()}>
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
              </div>
            </div>

            <div className="query-row-actions" onClick={(e) => e.stopPropagation()}>
              {editingId === q.id ? (
                <>
                  <button
                    className="primary-btn small"
                    disabled={savingEdit}
                    onClick={(e) => saveEdit(q.id, e)}
                  >
                    {savingEdit ? "Saving..." : "Save"}
                  </button>
                  <button className="secondary-btn small" onClick={cancelEdit}>
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button className="secondary-btn small" onClick={(e) => startEdit(q, e)}>
                    Edit
                  </button>
                  <button className="danger-btn small" onClick={(e) => handleDelete(q.id, e)}>
                    Delete
                  </button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
// import { useState, useEffect } from "react";
// import api from "../api";

// export default function RiskAssistant({ query }) {


//   function isCoordinatePair(str) {
//   const parts = str.split(",").map((p) => p.trim());
//   if (parts.length !== 2) return false;
//   return parts.every((p) => p !== "" && !isNaN(Number(p)));
// }

// function locationForAgent(resolvedName) {
//   if (isCoordinatePair(resolvedName)) return resolvedName;
//   return resolvedName.split(",")[0].trim();
// }
//   const [question, setQuestion] = useState("");
//   const [messages, setMessages] = useState([]);
//   const [loading, setLoading] = useState(false);

//   useEffect(() => {
//     setMessages([]);
//     setQuestion("");
//   }, [query.id]);

//   const ask = async (e) => {
//     e.preventDefault();
//     if (!question.trim()) return;
//     const q = question.trim();
//     setMessages((m) => [...m, { role: "user", text: q }]);
//     setQuestion("");
//     setLoading(true);
//     try {
//       const result = await api.askAgent(q, locationForAgent(query.resolved_name), query.start_date, query.end_date);
// if (!result) {
//   setMessages((m) => [...m, { role: "agent", text: "No response from the agent. Please try again.", error: true }]);
// } else {
//   setMessages((m) => [...m, { role: "agent", text: result.answer || "I couldn't generate an answer.", error: !!result.error }]);
// }
//     } catch (err) {
//       setMessages((m) => [...m, { role: "agent", text: `Something went wrong: ${err.message}`, error: true }]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const suggestions = [
//     "Should I plan an outdoor event this weekend?",
//     "Is it safe for construction work tomorrow?",
//     "Which day this week has the lowest risk for an outdoor sports event?",
//   ];

//   return (
//     <div className="card risk-assistant">
//       <h3>🤖 Weather Risk Assistant</h3>
//       <p className="assistant-subtitle">
//         Ask decision-oriented questions — this agent reasons over real forecast data for{" "}
//         <strong>{query.resolved_name}</strong> instead of just repeating numbers.
//       </p>

//       <div className="chat-window">
//         {messages.length === 0 && (
//           <div className="suggestions">
//             {suggestions.map((s) => (
//               <button key={s} className="suggestion-chip" onClick={() => setQuestion(s)}>
//                 {s}
//               </button>
//             ))}
//           </div>
//         )}
//         {messages.map((m, i) => (
//           <div key={i} className={`chat-message ${m.role} ${m.error ? "error" : ""}`}>
//             <span className="chat-role">{m.role === "user" ? "You" : "Assistant"}</span>
//             <p>{m.text}</p>
//           </div>
//         ))}
//         {loading && (
//           <div className="chat-message agent loading">
//             <span className="chat-role">Assistant</span>
//             <p>Thinking through the forecast...</p>
//           </div>
//         )}
//       </div>

//       <form onSubmit={ask} className="chat-input-row">
//         <input
//           type="text"
//           placeholder="e.g. Should I cycle to work tomorrow morning?"
//           value={question}
//           onChange={(e) => setQuestion(e.target.value)}
//         />
//         <button type="submit" disabled={loading} className="primary-btn">
//           Ask
//         </button>
//       </form>
//     </div>
//   );
// }



















































import { useState, useEffect } from "react";
import api from "../api";

export default function RiskAssistant({ query }) {


  function isCoordinatePair(str) {
  const parts = str.split(",").map((p) => p.trim());
  if (parts.length !== 2) return false;
  return parts.every((p) => p !== "" && !isNaN(Number(p)));
}

function locationForAgent(resolvedName) {
  if (isCoordinatePair(resolvedName)) return resolvedName;
  return resolvedName.split(",")[0].trim();
}
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMessages([]);
    setQuestion("");
  }, [query.id]);

  const ask = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    const q = question.trim();
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuestion("");
    setLoading(true);
    try {
      const result = await api.askAgent(q, locationForAgent(query.resolved_name), query.start_date, query.end_date);
if (!result) {
  setMessages((m) => [...m, { role: "agent", text: "No response from the agent. Please try again.", error: true }]);
} else {
  setMessages((m) => [...m, { role: "agent", text: result.answer || "I couldn't generate an answer.", error: !!result.error }]);
}
    } catch (err) {
      setMessages((m) => [...m, { role: "agent", text: `Something went wrong: ${err.message}`, error: true }]);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "Should I plan an outdoor event this weekend?",
    "Is it safe for construction work tomorrow?",
    "Which day this week has the lowest risk for an outdoor sports event?",
  ];

  return (
    <div className="card risk-assistant">
      <h3>🤖 Weather Risk Assistant</h3>
      <p className="assistant-subtitle">
        Ask decision-oriented questions — this agent reasons over real forecast data for{" "}
        <strong>{query.resolved_name}</strong> instead of just repeating numbers.
      </p>

      <div className="chat-window">
        {messages.length === 0 && (
          <div className="suggestions">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                className="suggestion-chip"
                onClick={(e) => { setQuestion(s); e.currentTarget.blur(); }}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-message ${m.role} ${m.error ? "error" : ""}`}>
            <span className="chat-role">{m.role === "user" ? "You" : "Assistant"}</span>
            <p>{m.text}</p>
          </div>
        ))}
        {loading && (
          <div className="chat-message agent loading">
            <span className="chat-role">Assistant</span>
            <p>Thinking through the forecast...</p>
          </div>
        )}
      </div>

      <form onSubmit={ask} className="chat-input-row">
        <input
          type="text"
          placeholder="e.g. Should I cycle to work tomorrow morning?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" disabled={loading} className="primary-btn">
          Ask
        </button>
      </form>
    </div>
  );
}
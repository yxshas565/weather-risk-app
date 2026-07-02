// import { useState } from "react";
// import WeatherSearch from "./components/WeatherSearch";
// import CurrentWeather from "./components/CurrentWeather";
// import Forecast from "./components/Forecast";
// import RiskAssistant from "./components/RiskAssistant";
// import SavedQueries from "./components/SavedQueries";
// import "./App.css";

// function App() {
//   const [activeQuery, setActiveQuery] = useState(null);
//   const [error, setError] = useState(null);
//   const [refreshSignal, setRefreshSignal] = useState(0);

//   const handleQueryCreated = (query) => {
//     setActiveQuery(query);
//     setError(null);
//     setRefreshSignal((n) => n + 1);
//   };

//   return (
//     <div className="app">
//       <header className="app-header">
//         <div>
//           <h1>🌦️ Weather Risk Assistant</h1>
//           <p className="subtitle">Built by Yashas Sadananda — PM Accelerator AI Engineer Assessment</p>
//         </div>
//       </header>

//       <section className="pm-blurb">
//         <strong>About PM Accelerator:</strong> The Product Manager Accelerator Program is
//         designed to support PM professionals through every stage of their careers — from
//         students becoming product managers to Directors becoming Chief Product Officers.
//       </section>

//       <main className="app-main">
//         <WeatherSearch onQueryCreated={handleQueryCreated} onError={setError} />

//         {error && <div className="error-banner">⚠ {error}</div>}

//         {activeQuery && (
//           <>
//             <CurrentWeather query={activeQuery} />
//             <Forecast query={activeQuery} onEventCreated={() => setRefreshSignal((n) => n + 1)} />
//             <RiskAssistant query={activeQuery} />
//           </>
//         )}

//         <SavedQueries
//   refreshSignal={refreshSignal}
//   onSelect={(q) => { setActiveQuery(q); setError(null); }}
//   activeId={activeQuery?.id}
// />
//       </main>

//       <footer className="app-footer">
//         <p>Weather Risk Assistant — Full Stack submission (Frontend + Backend + Agent)</p>
//       </footer>
//     </div>
//   );
// }

// export default App;






































// import { useState } from "react";
// import WeatherSearch from "./components/WeatherSearch";
// import CurrentWeather from "./components/CurrentWeather";
// import Forecast from "./components/Forecast";
// import RiskAssistant from "./components/RiskAssistant";
// import SavedQueries from "./components/SavedQueries";
// import "./App.css";

// function App() {
//   const [activeQuery, setActiveQuery] = useState(null);
//   const [error, setError] = useState(null);
//   const [refreshSignal, setRefreshSignal] = useState(0);

//   const handleQueryCreated = (query) => {
//     setActiveQuery(query);
//     setError(null);
//     setRefreshSignal((n) => n + 1);
//   };

//   const scrollToSearch = () => {
//     document.getElementById("search-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
//   };

//   return (
//     <div className="app-shell">
//       <div className="aurora-bg" aria-hidden="true">
//         <span className="aurora-blob blob-1" />
//         <span className="aurora-blob blob-2" />
//         <span className="aurora-blob blob-3" />
//       </div>

//       <nav className="site-nav">
//         <div className="nav-inner">
//           <div className="nav-brand">
//             <span className="nav-mark">🌦️</span>
//             <span>Weather Risk Assistant</span>
//           </div>
//           <button className="nav-cta" onClick={scrollToSearch}>
//             Check a location
//           </button>
//         </div>
//       </nav>

//       <header className="hero">
//         <div className="hero-content">
//           <span className="hero-eyebrow">PM Accelerator · AI Engineer Assessment</span>
//           <h1>
//             Weather that tells you <span className="hero-highlight">what to do</span>,
//             not just what it is.
//           </h1>
//           <p className="hero-sub">
//             Built by Yashas Sadananda — a decision-support layer for event planners and
//             outdoor workers, powered by live forecast data and an LLM reasoning agent.
//           </p>
//           <button className="hero-cta" onClick={scrollToSearch}>
//             Get a risk assessment ↓
//           </button>
//         </div>
//       </header>

//       <section className="pm-blurb">
//         <strong>About PM Accelerator:</strong> The Product Manager Accelerator Program is
//         designed to support PM professionals through every stage of their careers — from
//         students becoming product managers to Directors becoming Chief Product Officers.
//       </section>

//       <main className="app-main">
//         <section id="search-section" className="section-block">
//           <span className="section-eyebrow">01 · Search</span>
//           <WeatherSearch onQueryCreated={handleQueryCreated} onError={setError} />
//         </section>

//         {error && <div className="error-banner">⚠ {error}</div>}

//         {activeQuery && (
//           <>
//             <section className="section-block">
//               <span className="section-eyebrow">02 · Now</span>
//               <CurrentWeather query={activeQuery} />
//             </section>
//             <section className="section-block">
//               <span className="section-eyebrow">03 · Ahead</span>
//               <Forecast query={activeQuery} onEventCreated={() => setRefreshSignal((n) => n + 1)} />
//             </section>
//             <section className="section-block">
//               <span className="section-eyebrow">04 · Ask</span>
//               <RiskAssistant query={activeQuery} />
//             </section>
//           </>
//         )}

//         <section className="section-block">
//           <span className="section-eyebrow">05 · History</span>
//           <SavedQueries
//             refreshSignal={refreshSignal}
//             onSelect={(q) => {
//               setActiveQuery(q);
//               setError(null);
//             }}
//             activeId={activeQuery?.id}
//           />
//         </section>
//       </main>

//       <footer className="app-footer">
//         <p>Weather Risk Assistant — Full Stack submission (Frontend + Backend + Agent)</p>
//       </footer>
//     </div>
//   );
// }

// export default App;























































































import { useState, useEffect } from "react";
import WeatherSearch from "./components/WeatherSearch";
import CurrentWeather from "./components/CurrentWeather";
import Forecast from "./components/Forecast";
import RiskAssistant from "./components/RiskAssistant";
import SavedQueries from "./components/SavedQueries";
import "./App.css";

function App() {
  const [activeQuery, setActiveQuery] = useState(null);
  const [error, setError] = useState(null);
  const [refreshSignal, setRefreshSignal] = useState(0);
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const handleQueryCreated = (query) => {
    setActiveQuery(query);
    if (query) {
      setError(null);
      setRefreshSignal((n) => n + 1);
    }
  };

  const scrollToSearch = () => {
    document.getElementById("search-section")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="app-shell">
      <div className="mesh-bg" aria-hidden="true">
        <span className="mesh-blob b1" />
        <span className="mesh-blob b2" />
        <span className="mesh-blob b3" />
        <span className="mesh-blob b4" />
      </div>

      <nav className="site-nav">
        <div className="nav-inner">
          <div className="nav-brand">
            <span className="nav-mark">⚡</span>
            <span>Weather Risk Assistant</span>
          </div>
          <div className="nav-actions">
            <button
              className="theme-toggle"
              onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
              aria-label="Toggle theme"
            >
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
            <button className="nav-cta" onClick={scrollToSearch}>
              Check a location
            </button>
          </div>
        </div>
      </nav>

      <header className="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <span className="hero-eyebrow">PM Accelerator · AI Engineer Assessment</span>
          <h1>
            Weather that tells you <span className="hero-highlight">what to do</span>,
            not just what it is.
          </h1>
          <p className="hero-sub">
            Built by Yashas Sadananda — a decision-support layer for event planners and
            outdoor workers, powered by live forecast data and an LLM reasoning agent.
          </p>
          <button className="hero-cta" onClick={scrollToSearch}>
            <span>Get a risk assessment →</span>
          </button>
        </div>
      </header>

      <section className="pm-blurb">
        <strong>About PM Accelerator:</strong> The Product Manager Accelerator Program is
        designed to support PM professionals through every stage of their careers — from
        students becoming product managers to Directors becoming Chief Product Officers.
      </section>

      <main className="app-main">
        <section id="search-section" className="section-block">
          <span className="section-eyebrow">01 · Search</span>
          <WeatherSearch onQueryCreated={handleQueryCreated} onError={setError} />
        </section>

        {error && <div className="error-banner">⚠ {error}</div>}

        {activeQuery && (
          <>
            <section className="section-block">
              <span className="section-eyebrow">02 · Now</span>
              <CurrentWeather query={activeQuery} />
            </section>
            <section className="section-block">
              <span className="section-eyebrow">03 · Ahead</span>
              <Forecast query={activeQuery} onEventCreated={() => setRefreshSignal((n) => n + 1)} />
            </section>
            <section className="section-block">
              <span className="section-eyebrow">04 · Ask</span>
              <RiskAssistant query={activeQuery} />
            </section>
          </>
        )}

        <section className="section-block">
          <span className="section-eyebrow">05 · History</span>
          <SavedQueries
            refreshSignal={refreshSignal}
            onSelect={(q) => {
              setActiveQuery(q);
              setError(null);
            }}
            activeId={activeQuery?.id}
          />
        </section>
      </main>

      <footer className="app-footer">
        <p>Weather Risk Assistant — Full Stack submission (Frontend + Backend + Agent)</p>
      </footer>
    </div>
  );
}

export default App;
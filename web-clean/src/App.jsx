import OrthoAnalyzer from './components/ortho-analyzer';
import './App.css';

function App() {
  return (
    <div className="app">
      {/* Navbar */}
      <nav className="navbar" id="navbar">
        <div className="navbar__inner">
          <a href="/" className="navbar__brand">
            <div className="navbar__logo">OC</div>
            <span className="navbar__title">
              Ortho<span>-Check</span>
            </span>
          </a>
          <span className="navbar__badge">MVP</span>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <OrthoAnalyzer />
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          <span>Ortho-Check</span> · Fiscalização Assistida por IA · Powered by GPT-4o
        </p>
      </footer>
    </div>
  );
}

export default App;

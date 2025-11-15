import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Projects from "./pages/Projects";

const App: React.FC = () => {
  return (
    <div style={{ fontFamily: "sans-serif", padding: "1rem" }}>
      <header style={{ marginBottom: "1rem" }}>
        <Link to="/" style={{ textDecoration: "none", fontWeight: "bold" }}>
          Demo App
        </Link>
      </header>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/projects/:username" element={<Projects />} />
      </Routes>
    </div>
  );
};

export default App;

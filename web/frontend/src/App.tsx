import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Projects from "./pages/Projects";

import ProjectDetail from "./pages/ProjectDetail";

const App: React.FC = () => {
  return (
    <div style={{ fontFamily: "sans-serif", padding: "1rem" }}>
      {/* ... existing header ... */}

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/projects/:username" element={<Projects />} />
        <Route
          path="/projects/:username/:projectId"
          element={<ProjectDetail />}
        />
      </Routes>
    </div>
  );
};

export default App;

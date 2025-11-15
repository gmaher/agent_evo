import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import ProjectDetail from "./pages/ProjectDetail";
import TeamDetail from "./pages/TeamDetail";
import AgentDetail from "./pages/AgentDetail";
import RunDetail from "./pages/RunDetail";

const App: React.FC = () => {
  return (
    <div style={{ fontFamily: "sans-serif", padding: "1rem" }}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/projects/:username" element={<Dashboard />} />
        <Route
          path="/projects/:username/:projectId"
          element={<ProjectDetail />}
        />
        <Route path="/teams/:username/:teamId" element={<TeamDetail />} />
        <Route path="/agents/:username/:agentId" element={<AgentDetail />} />
        <Route path="/runs/:username/:runId" element={<RunDetail />} />
      </Routes>
    </div>
  );
};

export default App;

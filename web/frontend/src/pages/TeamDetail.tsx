import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { TeamWithAgents, Agent } from "../types";

const TeamDetail: React.FC = () => {
  const { username, teamId } = useParams<{
    username: string;
    teamId: string;
  }>();
  const navigate = useNavigate();
  const [team, setTeam] = useState<TeamWithAgents | null>(null);
  const [allAgents, setAllAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string>("");

  const fetchTeam = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/teams/${username}/${teamId}`
      );
      const data = await response.json();
      setTeam(data);
    } catch (error) {
      console.error("Failed to fetch team:", error);
    }
  };

  const fetchAllAgents = async () => {
    try {
      const response = await fetch(`http://localhost:8000/agents/${username}`);
      const data = await response.json();
      setAllAgents(data);
    } catch (error) {
      console.error("Failed to fetch agents:", error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTeam(), fetchAllAgents()]);
      setLoading(false);
    };
    loadData();
  }, [username, teamId]);

  const availableAgents = allAgents.filter(
    (agent) => !team?.agent_ids.includes(agent.id)
  );

  const handleAddAgent = async () => {
    if (!selectedAgent || !team) return;

    try {
      // Update team with new agent
      const updatedTeam = {
        ...team,
        agent_ids: [...team.agent_ids, selectedAgent],
      };

      const response = await fetch(
        `http://localhost:8000/teams/${username}/${teamId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: team.name,
            description: team.description,
            agent_ids: updatedTeam.agent_ids,
            edges: team.edges,
            entry_point: team.entry_point || updatedTeam.agent_ids[0],
          }),
        }
      );

      if (response.ok) {
        await fetchTeam();
        setSelectedAgent("");
      }
    } catch (error) {
      console.error("Failed to add agent:", error);
    }
  };

  const handleRemoveAgent = async (agentId: string) => {
    if (!team || !confirm("Remove this agent from the team?")) return;

    try {
      const updatedAgentIds = team.agent_ids.filter((id) => id !== agentId);
      const updatedEdges = team.edges.filter(
        (edge) => edge.from !== agentId && edge.to !== agentId
      );

      const response = await fetch(
        `http://localhost:8000/teams/${username}/${teamId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: team.name,
            description: team.description,
            agent_ids: updatedAgentIds,
            edges: updatedEdges,
            entry_point:
              team.entry_point === agentId && updatedAgentIds.length > 0
                ? updatedAgentIds[0]
                : team.entry_point,
          }),
        }
      );

      if (response.ok) {
        await fetchTeam();
      }
    } catch (error) {
      console.error("Failed to remove agent:", error);
    }
  };

  const handleSetEntryPoint = async (agentId: string) => {
    if (!team) return;

    try {
      const response = await fetch(
        `http://localhost:8000/teams/${username}/${teamId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: team.name,
            description: team.description,
            agent_ids: team.agent_ids,
            edges: team.edges,
            entry_point: agentId,
          }),
        }
      );

      if (response.ok) {
        await fetchTeam();
      }
    } catch (error) {
      console.error("Failed to set entry point:", error);
    }
  };

  if (loading) {
    return <div>Loading team details...</div>;
  }

  if (!team) {
    return <div>Team not found</div>;
  }

  return (
    <div>
      <button
        onClick={() => navigate(`/projects/${username}`)}
        style={{
          padding: "0.5rem 1rem",
          backgroundColor: "#6c757d",
          color: "white",
          border: "none",
          borderRadius: "4px",
          cursor: "pointer",
          marginBottom: "1rem",
        }}
      >
        ← Back to Dashboard
      </button>

      <h1>{team.name}</h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>{team.description}</p>

      {/* Add Agent Section */}
      <div
        style={{
          backgroundColor: "#f8f9fa",
          padding: "1.5rem",
          borderRadius: "8px",
          marginBottom: "2rem",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Add Agent to Team</h3>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            style={{
              flex: 1,
              padding: "0.5rem",
              border: "1px solid #ddd",
              borderRadius: "4px",
            }}
            disabled={availableAgents.length === 0}
          >
            <option value="">
              {availableAgents.length === 0
                ? "No available agents"
                : "Select an agent..."}
            </option>
            {availableAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
          <button
            onClick={handleAddAgent}
            disabled={!selectedAgent}
            style={{
              padding: "0.5rem 1.5rem",
              backgroundColor: selectedAgent ? "#28a745" : "#ccc",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: selectedAgent ? "pointer" : "not-allowed",
            }}
          >
            Add
          </button>
        </div>
      </div>

      {/* Team Agents */}
      <h2>Team Agents ({team.agents.length})</h2>
      {team.agents.length === 0 ? (
        <p style={{ color: "#666" }}>No agents in this team yet.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {team.agents.map((agent) => (
            <div
              key={agent.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: "8px",
                padding: "1.5rem",
                backgroundColor: "white",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "start",
                  marginBottom: "1rem",
                }}
              >
                <div style={{ flex: 1 }}>
                  <h3 style={{ margin: "0 0 0.5rem 0" }}>
                    {agent.name}
                    {team.entry_point === agent.id && (
                      <span
                        style={{
                          marginLeft: "0.5rem",
                          padding: "0.25rem 0.5rem",
                          backgroundColor: "#28a745",
                          color: "white",
                          fontSize: "0.75rem",
                          borderRadius: "4px",
                        }}
                      >
                        ENTRY POINT
                      </span>
                    )}
                  </h3>
                  <p style={{ margin: "0 0 0.5rem 0", color: "#666" }}>
                    Model: {agent.model || "gpt-4o"}
                  </p>
                  <p style={{ margin: 0, color: "#666" }}>
                    Tools:{" "}
                    {agent.tool_names.length > 0
                      ? agent.tool_names.join(", ")
                      : "None"}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {team.entry_point !== agent.id && (
                    <button
                      onClick={() => handleSetEntryPoint(agent.id)}
                      style={{
                        padding: "0.5rem 1rem",
                        backgroundColor: "#007bff",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                      }}
                    >
                      Set Entry Point
                    </button>
                  )}
                  <button
                    onClick={() => handleRemoveAgent(agent.id)}
                    style={{
                      padding: "0.5rem 1rem",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                    }}
                  >
                    Remove
                  </button>
                </div>
              </div>
              <div
                style={{
                  backgroundColor: "#f8f9fa",
                  padding: "1rem",
                  borderRadius: "4px",
                }}
              >
                <strong>System Prompt:</strong>
                <p style={{ margin: "0.5rem 0 0 0", whiteSpace: "pre-wrap" }}>
                  {agent.system_prompt}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TeamDetail;

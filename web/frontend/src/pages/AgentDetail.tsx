import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Agent } from "../types";

const AgentDetail: React.FC = () => {
  const { username, agentId } = useParams<{
    username: string;
    agentId: string;
  }>();
  const navigate = useNavigate();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "",
    system_prompt: "",
    tool_names: "",
    model: "gpt-4o",
    temperature: 1.0,
    max_retries: 3,
  });

  const fetchAgent = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/agents/${username}/${agentId}`
      );
      const data = await response.json();
      setAgent(data);
      setEditForm({
        name: data.name,
        system_prompt: data.system_prompt,
        tool_names: data.tool_names.join(", "),
        model: data.model || "gpt-4o",
        temperature: data.temperature || 1.0,
        max_retries: data.max_retries || 3,
      });
    } catch (error) {
      console.error("Failed to fetch agent:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgent();
  }, [username, agentId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(
        `http://localhost:8000/agents/${username}/${agentId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: editForm.name,
            system_prompt: editForm.system_prompt,
            tool_names: editForm.tool_names
              .split(",")
              .map((t) => t.trim())
              .filter(Boolean),
            model: editForm.model,
            temperature: editForm.temperature,
            max_retries: editForm.max_retries,
          }),
        }
      );

      if (response.ok) {
        await fetchAgent();
        setIsEditing(false);
      }
    } catch (error) {
      console.error("Failed to update agent:", error);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this agent?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/agents/${username}/${agentId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        navigate(`/projects/${username}`);
      }
    } catch (error) {
      console.error("Failed to delete agent:", error);
    }
  };

  if (loading) {
    return <div>Loading agent details...</div>;
  }

  if (!agent) {
    return <div>Agent not found</div>;
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

      {!isEditing ? (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "start",
              marginBottom: "2rem",
            }}
          >
            <div>
              <h1 style={{ marginBottom: "0.5rem" }}>{agent.name}</h1>
              <p style={{ color: "#666", margin: 0 }}>
                Model: {agent.model || "gpt-4o"} | Temperature:{" "}
                {agent.temperature || 1.0} | Max Retries:{" "}
                {agent.max_retries || 3}
              </p>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                onClick={() => setIsEditing(true)}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#007bff",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#dc3545",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Delete
              </button>
            </div>
          </div>

          <div
            style={{
              backgroundColor: "#f8f9fa",
              padding: "1.5rem",
              borderRadius: "8px",
              marginBottom: "1.5rem",
            }}
          >
            <h3 style={{ marginTop: 0 }}>System Prompt</h3>
            <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>
              {agent.system_prompt}
            </p>
          </div>

          <div
            style={{
              backgroundColor: "#f8f9fa",
              padding: "1.5rem",
              borderRadius: "8px",
            }}
          >
            <h3 style={{ marginTop: 0 }}>Tools</h3>
            {agent.tool_names.length > 0 ? (
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {agent.tool_names.map((tool) => (
                  <span
                    key={tool}
                    style={{
                      padding: "0.25rem 0.75rem",
                      backgroundColor: "#007bff",
                      color: "white",
                      borderRadius: "4px",
                      fontSize: "0.9rem",
                    }}
                  >
                    {tool}
                  </span>
                ))}
              </div>
            ) : (
              <p style={{ margin: 0, color: "#666" }}>No tools configured</p>
            )}
          </div>
        </div>
      ) : (
        <div>
          <h1>Edit Agent</h1>
          <form onSubmit={handleUpdate}>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Name
              </label>
              <input
                type="text"
                value={editForm.name}
                onChange={(e) =>
                  setEditForm({ ...editForm, name: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
                required
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                System Prompt
              </label>
              <textarea
                value={editForm.system_prompt}
                onChange={(e) =>
                  setEditForm({ ...editForm, system_prompt: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                  minHeight: "150px",
                }}
                required
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Model
              </label>
              <select
                value={editForm.model}
                onChange={(e) =>
                  setEditForm({ ...editForm, model: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
              >
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              </select>
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Tool Names (comma-separated)
              </label>
              <input
                type="text"
                value={editForm.tool_names}
                onChange={(e) =>
                  setEditForm({ ...editForm, tool_names: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                }}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "1rem",
                marginBottom: "1rem",
              }}
            >
              <div>
                <label style={{ display: "block", marginBottom: "0.5rem" }}>
                  Temperature
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={editForm.temperature}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      temperature: parseFloat(e.target.value),
                    })
                  }
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: "0.5rem" }}>
                  Max Retries
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={editForm.max_retries}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      max_retries: parseInt(e.target.value),
                    })
                  }
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                  }}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor: "#28a745",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default AgentDetail;

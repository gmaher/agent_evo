import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Run, Project, Team, ExecutionEntry, ChatMessage } from "../types";

const RunDetail: React.FC = () => {
  const { username, runId } = useParams<{ username: string; runId: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<Run | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<
    "overview" | "execution" | "chat" | "outputs" | "files"
  >("overview");

  useEffect(() => {
    fetchRunDetails();
  }, [username, runId]);

  const fetchRunDetails = async () => {
    try {
      const runRes = await fetch(
        `http://localhost:8000/runs/${username}/${runId}`
      );
      const runData = await runRes.json();
      setRun(runData);

      // Fetch related project and team
      const [projectRes, teamRes] = await Promise.all([
        fetch(
          `http://localhost:8000/projects/${username}/${runData.project_id}`
        ),
        fetch(`http://localhost:8000/teams/${username}/${runData.team_id}`),
      ]);
      const projectData = await projectRes.json();
      const teamData = await teamRes.json();
      setProject(projectData);
      setTeam(teamData);
    } catch (error) {
      console.error("Failed to fetch run details:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this run?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/runs/${username}/${runId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        navigate(`/projects/${username}`);
      }
    } catch (error) {
      console.error("Failed to delete run:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "#28a745";
      case "failed":
        return "#dc3545";
      case "running":
        return "#ffc107";
      default:
        return "#6c757d";
    }
  };

  const tabStyle = (tab: typeof selectedTab) => ({
    padding: "0.75rem 1.5rem",
    backgroundColor: selectedTab === tab ? "#007bff" : "#f8f9fa",
    color: selectedTab === tab ? "white" : "#333",
    border: "none",
    borderBottom: selectedTab === tab ? "none" : "2px solid #ddd",
    cursor: "pointer",
    fontSize: "1rem",
    fontWeight: selectedTab === tab ? "bold" : "normal",
  });

  if (loading) {
    return <div>Loading run details...</div>;
  }

  if (!run) {
    return <div>Run not found</div>;
  }

  const isCompleted = run.status === "completed";
  const isFailed = run.status === "failed";
  const result = isCompleted ? (run.result as any) : null;

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

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "start",
          marginBottom: "2rem",
        }}
      >
        <div>
          <h1 style={{ marginBottom: "0.5rem" }}>{run.run_name}</h1>
          <p style={{ color: "#666", margin: "0 0 0.5rem 0" }}>
            {new Date(run.timestamp).toLocaleString()}
          </p>
          <span
            style={{
              padding: "0.25rem 0.75rem",
              backgroundColor: getStatusColor(run.status),
              color: "white",
              borderRadius: "4px",
              fontSize: "0.9rem",
              textTransform: "uppercase",
            }}
          >
            {run.status}
          </span>
        </div>
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

      {/* Score Display - Show if completed and score exists */}
      {isCompleted && run.score !== null && run.score !== undefined && (
        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
            border: "2px solid #007bff",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div>
              <h2 style={{ margin: "0 0 0.5rem 0" }}>Performance Score</h2>
              <div
                style={{
                  fontSize: "3rem",
                  fontWeight: "bold",
                  color:
                    run.score >= 7
                      ? "#28a745"
                      : run.score >= 4
                      ? "#ffc107"
                      : "#dc3545",
                }}
              >
                {run.score}/10
              </div>
            </div>
            {run.score_reasoning && (
              <div style={{ flex: 1, marginLeft: "2rem" }}>
                <h4 style={{ margin: "0 0 0.5rem 0" }}>Reasoning</h4>
                <p style={{ margin: 0, color: "#666", lineHeight: "1.6" }}>
                  {run.score_reasoning}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Run Info */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "1.5rem",
            borderRadius: "8px",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Project</h3>
          {project ? (
            <div>
              <p style={{ margin: "0 0 0.5rem 0", fontWeight: "bold" }}>
                {project.name}
              </p>
              <p style={{ margin: 0, color: "#666" }}>{project.description}</p>
            </div>
          ) : (
            <p style={{ margin: 0, color: "#666" }}>Loading...</p>
          )}
        </div>

        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "1.5rem",
            borderRadius: "8px",
          }}
        >
          <h3 style={{ marginTop: 0 }}>Team</h3>
          {team ? (
            <div>
              <p style={{ margin: "0 0 0.5rem 0", fontWeight: "bold" }}>
                {team.name}
              </p>
              <p style={{ margin: 0, color: "#666" }}>
                {team.agent_ids.length} agent
                {team.agent_ids.length !== 1 ? "s" : ""}
              </p>
            </div>
          ) : (
            <p style={{ margin: 0, color: "#666" }}>Loading...</p>
          )}
        </div>
      </div>

      {/* Failed Error Display */}
      {isFailed && (
        <div
          style={{
            backgroundColor: "#f8d7da",
            border: "1px solid #f5c6cb",
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
          }}
        >
          <h3 style={{ marginTop: 0, color: "#721c24" }}>Run Failed</h3>
          <pre
            style={{
              backgroundColor: "#fff",
              padding: "1rem",
              borderRadius: "4px",
              overflow: "auto",
              border: "1px solid #ddd",
              color: "#721c24",
            }}
          >
            {JSON.stringify(run.result, null, 2)}
          </pre>
        </div>
      )}

      {/* Results Tabs - Only show if completed */}
      {isCompleted && result && (
        <>
          <div
            style={{ borderBottom: "2px solid #ddd", marginBottom: "1.5rem" }}
          >
            <button
              onClick={() => setSelectedTab("overview")}
              style={tabStyle("overview")}
            >
              Overview
            </button>
            <button
              onClick={() => setSelectedTab("execution")}
              style={tabStyle("execution")}
            >
              Execution History
            </button>
            <button
              onClick={() => setSelectedTab("chat")}
              style={tabStyle("chat")}
            >
              Chat History
            </button>
            <button
              onClick={() => setSelectedTab("outputs")}
              style={tabStyle("outputs")}
            >
              Agent Outputs
            </button>
            {result.modified_files &&
              Object.keys(result.modified_files).length > 0 && (
                <button
                  onClick={() => setSelectedTab("files")}
                  style={tabStyle("files")}
                >
                  Modified Files
                </button>
              )}
          </div>

          {/* Overview Tab */}
          {selectedTab === "overview" && (
            <div
              style={{
                backgroundColor: "#f8f9fa",
                padding: "1.5rem",
                borderRadius: "8px",
              }}
            >
              <h3 style={{ marginTop: 0 }}>Run Summary</h3>
              <div style={{ marginBottom: "1rem" }}>
                <strong>Total Rounds:</strong> {result.rounds}
              </div>
              <div style={{ marginBottom: "1rem" }}>
                <strong>Agents Involved:</strong>{" "}
                {Object.keys(result.agent_outputs || {}).length}
              </div>
              {result.execution_history &&
                result.execution_history.length > 0 && (
                  <div>
                    <strong>Execution Flow:</strong>
                    <ol style={{ marginTop: "0.5rem" }}>
                      {result.execution_history.map(
                        (entry: ExecutionEntry, idx: number) => (
                          <li key={idx} style={{ marginBottom: "0.5rem" }}>
                            <strong>{entry.agent_name}</strong> -{" "}
                            {entry.result.iterations} iteration(s)
                            {entry.result.delegation && (
                              <span
                                style={{
                                  color: "#007bff",
                                  marginLeft: "0.5rem",
                                }}
                              >
                                → Delegated to{" "}
                                {entry.result.delegation.to_agent}
                              </span>
                            )}
                          </li>
                        )
                      )}
                    </ol>
                  </div>
                )}
            </div>
          )}

          {/* Execution History Tab */}
          {selectedTab === "execution" && (
            <div>
              {result.execution_history &&
              result.execution_history.length > 0 ? (
                result.execution_history.map(
                  (entry: ExecutionEntry, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        backgroundColor: "#f8f9fa",
                        padding: "1.5rem",
                        borderRadius: "8px",
                        marginBottom: "1rem",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: "1rem",
                        }}
                      >
                        <h3 style={{ margin: 0 }}>
                          Round {entry.round + 1}: {entry.agent_name}
                        </h3>
                        <span style={{ color: "#666" }}>
                          {entry.result.iterations} iteration(s)
                        </span>
                      </div>
                      <div style={{ marginBottom: "1rem" }}>
                        <strong>Task:</strong>
                        <p style={{ margin: "0.5rem 0", color: "#666" }}>
                          {entry.task}
                        </p>
                      </div>
                      <div style={{ marginBottom: "1rem" }}>
                        <strong>Response:</strong>
                        <pre
                          style={{
                            backgroundColor: "#fff",
                            padding: "1rem",
                            borderRadius: "4px",
                            overflow: "auto",
                            border: "1px solid #ddd",
                            whiteSpace: "pre-wrap",
                            marginTop: "0.5rem",
                          }}
                        >
                          {entry.result.final_response}
                        </pre>
                      </div>
                      {entry.result.delegation && (
                        <div
                          style={{
                            backgroundColor: "#e7f3ff",
                            padding: "1rem",
                            borderRadius: "4px",
                            border: "1px solid #007bff",
                          }}
                        >
                          <strong style={{ color: "#007bff" }}>
                            Delegated to:
                          </strong>{" "}
                          {entry.result.delegation.to_agent}
                          <p style={{ margin: "0.5rem 0 0 0", color: "#666" }}>
                            {entry.result.delegation.task}
                          </p>
                        </div>
                      )}
                    </div>
                  )
                )
              ) : (
                <p>No execution history available</p>
              )}
            </div>
          )}

          {/* Chat History Tab */}
          {selectedTab === "chat" && (
            <div
              style={{
                backgroundColor: "#f8f9fa",
                padding: "1.5rem",
                borderRadius: "8px",
              }}
            >
              <h3 style={{ marginTop: 0 }}>Chat History</h3>
              {result.chat_history && result.chat_history.length > 0 ? (
                <div>
                  {result.chat_history.map((msg: ChatMessage, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        backgroundColor:
                          msg.role === "assistant" ? "#e3f2fd" : "#fff",
                        padding: "1rem",
                        borderRadius: "4px",
                        marginBottom: "0.5rem",
                        border: "1px solid #ddd",
                      }}
                    >
                      <div style={{ marginBottom: "0.5rem" }}>
                        <strong style={{ color: "#007bff" }}>
                          {msg.agent_name}
                        </strong>
                        <span style={{ color: "#666", marginLeft: "0.5rem" }}>
                          ({msg.role})
                        </span>
                      </div>
                      <pre
                        style={{
                          margin: 0,
                          whiteSpace: "pre-wrap",
                          fontFamily: "inherit",
                        }}
                      >
                        {msg.content}
                      </pre>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No chat history available</p>
              )}
            </div>
          )}

          {/* Agent Outputs Tab */}
          {selectedTab === "outputs" && (
            <div>
              {result.agent_outputs &&
              Object.keys(result.agent_outputs).length > 0 ? (
                Object.entries(result.agent_outputs).map(
                  ([agentId, output]) => (
                    <div
                      key={agentId}
                      style={{
                        backgroundColor: "#f8f9fa",
                        padding: "1.5rem",
                        borderRadius: "8px",
                        marginBottom: "1rem",
                      }}
                    >
                      <h3 style={{ marginTop: 0 }}>Agent: {agentId}</h3>
                      <pre
                        style={{
                          backgroundColor: "#fff",
                          padding: "1rem",
                          borderRadius: "4px",
                          overflow: "auto",
                          border: "1px solid #ddd",
                          whiteSpace: "pre-wrap",
                        }}
                      >
                        {output as string}
                      </pre>
                    </div>
                  )
                )
              ) : (
                <p>No agent outputs available</p>
              )}
            </div>
          )}

          {/* Modified Files Tab */}
          {selectedTab === "files" && result.modified_files && (
            <div>
              {Object.entries(result.modified_files).map(
                ([filename, content]) => (
                  <div
                    key={filename}
                    style={{
                      backgroundColor: "#f8f9fa",
                      padding: "1.5rem",
                      borderRadius: "8px",
                      marginBottom: "1rem",
                    }}
                  >
                    <h3 style={{ marginTop: 0 }}>{filename}</h3>
                    <pre
                      style={{
                        backgroundColor: "#fff",
                        padding: "1rem",
                        borderRadius: "4px",
                        overflow: "auto",
                        border: "1px solid #ddd",
                        maxHeight: "400px",
                      }}
                    >
                      {content as string}
                    </pre>
                  </div>
                )
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RunDetail;

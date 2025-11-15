import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Evolution, Project, Team, Run } from "../types";

const EvolutionDetail: React.FC = () => {
  const { username, evolutionId } = useParams<{
    username: string;
    evolutionId: string;
  }>();
  const navigate = useNavigate();
  const [evolution, setEvolution] = useState<Evolution | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvolutionDetails();
  }, [username, evolutionId]);

  const fetchEvolutionDetails = async () => {
    try {
      const evolutionRes = await fetch(
        `http://localhost:8000/evolutions/${username}/${evolutionId}`
      );
      const evolutionData = await evolutionRes.json();
      setEvolution(evolutionData);

      // Set runs from the evolution response
      if (evolutionData.runs) {
        setRuns(evolutionData.runs);
      }

      // Fetch related project
      const projectRes = await fetch(
        `http://localhost:8000/projects/${username}/${evolutionData.project_id}`
      );
      const projectData = await projectRes.json();
      setProject(projectData);

      // Fetch all teams
      if (evolutionData.team_ids.length > 0) {
        const teamPromises = evolutionData.team_ids.map((teamId: string) =>
          fetch(`http://localhost:8000/teams/${username}/${teamId}`).then((r) =>
            r.json()
          )
        );
        const teamsData = await Promise.all(teamPromises);
        setTeams(teamsData);
      }
    } catch (error) {
      console.error("Failed to fetch evolution details:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this evolution?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/evolutions/${username}/${evolutionId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        navigate(`/projects/${username}`);
      }
    } catch (error) {
      console.error("Failed to delete evolution:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "#28a745";
      case "failed":
        return "#dc3545";
      case "generating":
        return "#ffc107";
      default:
        return "#6c757d";
    }
  };

  // Get completed runs with scores
  const completedRuns = runs.filter(
    (run) =>
      run.status === "completed" &&
      run.score !== null &&
      run.score !== undefined
  );

  // Calculate statistics
  const avgScore =
    completedRuns.length > 0
      ? completedRuns.reduce((sum, run) => sum + (run.score || 0), 0) /
        completedRuns.length
      : 0;

  const maxScore =
    completedRuns.length > 0
      ? Math.max(...completedRuns.map((run) => run.score || 0))
      : 0;

  const minScore =
    completedRuns.length > 0
      ? Math.min(...completedRuns.map((run) => run.score || 0))
      : 0;

  if (loading) {
    return <div>Loading evolution details...</div>;
  }

  if (!evolution) {
    return <div>Evolution not found</div>;
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

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "start",
          marginBottom: "2rem",
        }}
      >
        <div>
          <h1 style={{ marginBottom: "0.5rem" }}>
            Evolution - Generation {evolution.generation}
          </h1>
          <p style={{ color: "#666", margin: "0 0 0.5rem 0" }}>
            {new Date(evolution.timestamp).toLocaleString()}
          </p>
          <span
            style={{
              padding: "0.25rem 0.75rem",
              backgroundColor: getStatusColor(evolution.status),
              color: "white",
              borderRadius: "4px",
              fontSize: "0.9rem",
              textTransform: "uppercase",
            }}
          >
            {evolution.status}
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

      {/* Performance Graph */}
      {completedRuns.length > 0 && (
        <div
          style={{
            backgroundColor: "#f8f9fa",
            padding: "1.5rem",
            borderRadius: "8px",
            marginBottom: "2rem",
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: "1rem" }}>
            Performance Overview
          </h3>

          {/* Statistics */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "1rem",
              marginBottom: "1.5rem",
            }}
          >
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.9rem", color: "#666" }}>
                Average Score
              </div>
              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: "bold",
                  color: "#007bff",
                }}
              >
                {avgScore.toFixed(1)}/10
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.9rem", color: "#666" }}>
                Best Score
              </div>
              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: "bold",
                  color: "#28a745",
                }}
              >
                {maxScore.toFixed(1)}/10
              </div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: "0.9rem", color: "#666" }}>
                Lowest Score
              </div>
              <div
                style={{
                  fontSize: "2rem",
                  fontWeight: "bold",
                  color: "#dc3545",
                }}
              >
                {minScore.toFixed(1)}/10
              </div>
            </div>
          </div>

          {/* Bar Chart */}
          <div>
            <h4 style={{ margin: "0 0 1rem 0" }}>Score Distribution</h4>
            <div
              style={{
                display: "flex",
                alignItems: "flex-end",
                gap: "0.5rem",
                height: "200px",
              }}
            >
              {completedRuns.map((run, index) => {
                const heightPercent = ((run.score || 0) / 10) * 100;
                const barColor =
                  (run.score || 0) >= 7
                    ? "#28a745"
                    : (run.score || 0) >= 4
                    ? "#ffc107"
                    : "#dc3545";

                return (
                  <div
                    key={run.id}
                    style={{
                      flex: 1,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "flex-end",
                      height: "100%",
                    }}
                  >
                    <Link
                      to={`/runs/${username}/${run.id}`}
                      style={{
                        width: "100%",
                        textDecoration: "none",
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        justifyContent: "flex-end",
                        height: "100%",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "0.75rem",
                          fontWeight: "bold",
                          marginBottom: "0.25rem",
                          color: barColor,
                        }}
                      >
                        {run.score?.toFixed(1)}
                      </div>
                      <div
                        style={{
                          width: "100%",
                          height: `${heightPercent}%`,
                          backgroundColor: barColor,
                          borderRadius: "4px 4px 0 0",
                          transition: "all 0.2s",
                          cursor: "pointer",
                          position: "relative",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.opacity = "0.8";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.opacity = "1";
                        }}
                        title={`Run ${index + 1}: ${run.score}/10`}
                      />
                      <div
                        style={{
                          fontSize: "0.7rem",
                          color: "#666",
                          marginTop: "0.25rem",
                        }}
                      >
                        {index + 1}
                      </div>
                    </Link>
                  </div>
                );
              })}
            </div>
            <div
              style={{
                borderTop: "2px solid #333",
                marginTop: "0.5rem",
                paddingTop: "0.5rem",
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.8rem",
                color: "#666",
              }}
            >
              <span>Run Number</span>
            </div>
          </div>
        </div>
      )}

      {/* Evolution Info */}
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
          <h3 style={{ marginTop: 0 }}>Configuration</h3>
          <div style={{ marginBottom: "0.5rem" }}>
            <strong>Initial Teams (K):</strong> {evolution.K}
          </div>
          <div style={{ marginBottom: "0.5rem" }}>
            <strong>Max Rounds:</strong> {evolution.max_rounds}
          </div>
          <div style={{ marginBottom: "0.5rem" }}>
            <strong>Current Generation:</strong> {evolution.generation}
          </div>
          <div style={{ marginBottom: "0.5rem" }}>
            <strong>Total Teams:</strong> {evolution.team_ids.length}
          </div>
          <div>
            <strong>Total Runs:</strong> {runs.length}
          </div>
        </div>

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
      </div>

      {/* Generated Teams */}
      <div
        style={{
          backgroundColor: "#f8f9fa",
          padding: "1.5rem",
          borderRadius: "8px",
          marginBottom: "2rem",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Generated Teams</h3>
        {teams.length === 0 ? (
          <p style={{ color: "#666" }}>No teams generated yet</p>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
              gap: "1rem",
            }}
          >
            {teams.map((team, index) => {
              // Find the run for this team
              const teamRun = runs.find((run) => run.team_id === team.id);

              return (
                <Link
                  key={team.id}
                  to={`/teams/${username}/${team.id}`}
                  style={{ textDecoration: "none", color: "inherit" }}
                >
                  <div
                    style={{
                      backgroundColor: "white",
                      border: "1px solid #ddd",
                      borderRadius: "8px",
                      padding: "1rem",
                      transition: "all 0.2s",
                      cursor: "pointer",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.boxShadow =
                        "0 4px 8px rgba(0,0,0,0.1)";
                      e.currentTarget.style.transform = "translateY(-2px)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.boxShadow = "none";
                      e.currentTarget.style.transform = "translateY(0)";
                    }}
                  >
                    <h4 style={{ margin: "0 0 0.5rem 0" }}>{team.name}</h4>
                    <p
                      style={{
                        margin: "0 0 0.5rem 0",
                        color: "#666",
                        fontSize: "0.9rem",
                      }}
                    >
                      {team.description}
                    </p>
                    <p
                      style={{
                        margin: "0 0 0.5rem 0",
                        fontSize: "0.85rem",
                        color: "#999",
                      }}
                    >
                      {team.agent_ids.length} agent
                      {team.agent_ids.length !== 1 ? "s" : ""} |{" "}
                      {team.edges.length} connection
                      {team.edges.length !== 1 ? "s" : ""}
                    </p>
                    {teamRun &&
                      teamRun.score !== null &&
                      teamRun.score !== undefined && (
                        <div
                          style={{
                            marginTop: "0.5rem",
                            padding: "0.5rem",
                            backgroundColor: "#e3f2fd",
                            borderRadius: "4px",
                            fontSize: "0.9rem",
                            fontWeight: "bold",
                            color: "#007bff",
                          }}
                        >
                          Score: {teamRun.score.toFixed(1)}/10
                        </div>
                      )}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {evolution.status === "failed" && (
        <div
          style={{
            backgroundColor: "#f8d7da",
            border: "1px solid #f5c6cb",
            padding: "1.5rem",
            borderRadius: "8px",
          }}
        >
          <h3 style={{ marginTop: 0, color: "#721c24" }}>
            Evolution Generation Failed
          </h3>
          <p style={{ margin: 0, color: "#721c24" }}>
            There was an error generating the teams. Please try again or check
            the server logs for more details.
          </p>
        </div>
      )}
    </div>
  );
};

export default EvolutionDetail;

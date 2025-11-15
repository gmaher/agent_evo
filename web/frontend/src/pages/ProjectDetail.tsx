import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Project, File } from "../types";

const ProjectDetail: React.FC = () => {
  const { username, projectId } = useParams<{
    username: string;
    projectId: string;
  }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "",
    description: "",
    files: [] as File[],
  });

  const fetchProject = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}`
      );
      const data = await response.json();
      setProject(data);
      setEditForm({
        name: data.name,
        description: data.description,
        files: data.files || [],
      });
    } catch (error) {
      console.error("Failed to fetch project:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();
  }, [username, projectId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(editForm),
        }
      );

      if (response.ok) {
        await fetchProject();
        setIsEditing(false);
      }
    } catch (error) {
      console.error("Failed to update project:", error);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this project?")) return;

    try {
      const response = await fetch(
        `http://localhost:8000/projects/${username}/${projectId}`,
        { method: "DELETE" }
      );

      if (response.ok) {
        navigate(`/projects/${username}`);
      }
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
  };

  const handleAddFile = () => {
    setEditForm({
      ...editForm,
      files: [...editForm.files, { filename: "", content: "" }],
    });
  };

  const handleRemoveFile = (index: number) => {
    setEditForm({
      ...editForm,
      files: editForm.files.filter((_, i) => i !== index),
    });
  };

  const handleFileChange = (
    index: number,
    field: "filename" | "content",
    value: string
  ) => {
    const updatedFiles = [...editForm.files];
    updatedFiles[index][field] = value;
    setEditForm({ ...editForm, files: updatedFiles });
  };

  if (loading) return <p>Loading project details...</p>;
  if (!project) return <p>Project not found</p>;

  return (
    <div>
      <Link
        to={`/projects/${username}`}
        style={{ textDecoration: "none", color: "#007bff" }}
      >
        ← Back to Projects
      </Link>

      {!isEditing ? (
        <>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "start",
              marginTop: "1rem",
              marginBottom: "2rem",
            }}
          >
            <div>
              <h1 style={{ marginBottom: "0.5rem" }}>{project.name}</h1>
              <p style={{ color: "#666", margin: 0 }}>{project.description}</p>
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

          <h2>Files ({project.files.length})</h2>
          {project.files.length === 0 ? (
            <p>No files in this project yet.</p>
          ) : (
            <div>
              {project.files.map((file, index) => (
                <div
                  key={index}
                  style={{
                    marginBottom: "1rem",
                    backgroundColor: "white",
                    border: "1px solid #ddd",
                    borderRadius: "8px",
                    padding: "1.5rem",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "bold",
                      marginBottom: "0.5rem",
                      color: "#333",
                      fontSize: "1.1rem",
                    }}
                  >
                    {file.filename}
                  </div>
                  <pre
                    style={{
                      backgroundColor: "#f5f5f5",
                      padding: "1rem",
                      borderRadius: "4px",
                      overflow: "auto",
                      margin: 0,
                    }}
                  >
                    <code>{file.content}</code>
                  </pre>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <div style={{ marginTop: "1rem" }}>
          <h1>Edit Project</h1>
          <form onSubmit={handleUpdate}>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", marginBottom: "0.5rem" }}>
                Project Name
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
                Description
              </label>
              <textarea
                value={editForm.description}
                onChange={(e) =>
                  setEditForm({ ...editForm, description: e.target.value })
                }
                style={{
                  width: "100%",
                  padding: "0.5rem",
                  border: "1px solid #ddd",
                  borderRadius: "4px",
                  minHeight: "100px",
                }}
                required
              />
            </div>

            <div style={{ marginBottom: "1rem" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem",
                }}
              >
                <label style={{ fontWeight: "bold" }}>Files</label>
                <button
                  type="button"
                  onClick={handleAddFile}
                  style={{
                    padding: "0.25rem 0.75rem",
                    backgroundColor: "#28a745",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                  }}
                >
                  + Add File
                </button>
              </div>

              {editForm.files.map((file, index) => (
                <div
                  key={index}
                  style={{
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    padding: "1rem",
                    marginBottom: "1rem",
                    backgroundColor: "#f9f9f9",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <span style={{ fontWeight: "bold", fontSize: "0.9rem" }}>
                      File #{index + 1}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(index)}
                      style={{
                        padding: "0.25rem 0.5rem",
                        backgroundColor: "#dc3545",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "0.8rem",
                      }}
                    >
                      Remove
                    </button>
                  </div>
                  <div style={{ marginBottom: "0.5rem" }}>
                    <label
                      style={{
                        display: "block",
                        marginBottom: "0.25rem",
                        fontSize: "0.9rem",
                      }}
                    >
                      Filename
                    </label>
                    <input
                      type="text"
                      value={file.filename}
                      onChange={(e) =>
                        handleFileChange(index, "filename", e.target.value)
                      }
                      placeholder="e.g., main.py"
                      style={{
                        width: "100%",
                        padding: "0.5rem",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                      }}
                    />
                  </div>
                  <div>
                    <label
                      style={{
                        display: "block",
                        marginBottom: "0.25rem",
                        fontSize: "0.9rem",
                      }}
                    >
                      Content
                    </label>
                    <textarea
                      value={file.content}
                      onChange={(e) =>
                        handleFileChange(index, "content", e.target.value)
                      }
                      placeholder="Paste file content here..."
                      style={{
                        width: "100%",
                        padding: "0.5rem",
                        border: "1px solid #ddd",
                        borderRadius: "4px",
                        minHeight: "120px",
                        fontFamily: "monospace",
                        fontSize: "0.85rem",
                      }}
                    />
                  </div>
                </div>
              ))}
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

export default ProjectDetail;

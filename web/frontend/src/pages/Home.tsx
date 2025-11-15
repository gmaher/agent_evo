import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const Home: React.FC = () => {
  const [username, setUsername] = useState("");
  const navigate = useNavigate();

  const handleLogin = () => {
    const trimmed = username.trim();
    if (!trimmed) return;
    navigate(`/projects/${encodeURIComponent(trimmed)}`);
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === "Enter") {
      handleLogin();
    }
  };

  return (
    <main>
      <h1>Welcome</h1>
      <p>Enter a username to view projects.</p>
      <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={handleKeyDown}
          style={{ padding: "0.4rem", minWidth: "200px" }}
        />
        <button onClick={handleLogin} style={{ padding: "0.4rem 0.8rem" }}>
          Login
        </button>
      </div>
      <p style={{ marginTop: "0.5rem", fontSize: "0.9rem", color: "#555" }}>
        Try usernames like <code>alice</code> or <code>bob</code>, or any name.
      </p>
    </main>
  );
};

export default Home;

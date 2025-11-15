export interface Project {
  id: number;
  name: string;
  description: string;
}

export interface File {
  filename: string;
  content: string;
}

export interface Task {
  id: number;
  project_id: number;
  description: string;
  files: File[];
}

export interface Agent {
  id: string;
  name: string;
  system_prompt: string;
  tool_names: string[];
  model?: string;
  temperature?: number;
  max_retries?: number;
}

export interface TeamEdge {
  from: string;
  to: string;
  description?: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  agent_ids: string[];
  edges: TeamEdge[];
  entry_point: string;
}

export interface TeamWithAgents extends Team {
  agents: Agent[];
}

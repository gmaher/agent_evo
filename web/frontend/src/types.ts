export interface File {
  filename: string;
  content: string;
}

export interface Project {
  id: number;
  name: string;
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

// Run result types matching AgentEvo structure
export interface ChatMessage {
  agent_id: string;
  agent_name: string;
  role: string;
  content: string;
}

export interface AgentResult {
  agent_id: string;
  agent_name: string;
  final_response: string;
  iterations: number;
  delegation?: {
    to_agent: string;
    task: string;
  };
  finished: boolean;
}

export interface ExecutionEntry {
  round: number;
  agent_id: string;
  agent_name: string;
  task: string;
  result: AgentResult;
}

export interface TeamResult {
  team_id: string;
  team_name: string;
  rounds: number;
  agent_outputs: Record<string, string>;
  execution_history: ExecutionEntry[];
  chat_history: ChatMessage[];
  modified_files?: Record<string, string>;
}

export interface Run {
  id: string;
  username: string;
  team_id: string;
  project_id: number;
  run_name: string;
  timestamp: string;
  status: "running" | "completed" | "failed";
  result: TeamResult | { error: string };
}

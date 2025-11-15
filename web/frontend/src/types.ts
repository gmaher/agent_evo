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

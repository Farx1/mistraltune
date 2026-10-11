export type Job = {
  id: string;
  model: string;
  status: string;
  fine_tuned_model?: string | null;
  created_at?: number;
  updated_at?: number;
  [k: string]: any;
};

export type Dataset = {
  id?: string;
  filename?: string;
  name?: string;
  created_at?: number;
  size_bytes?: number;
  [k: string]: any;
};

const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function fetchJSON<T>(path: string, init?: RequestInit, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      signal: controller.signal,
    });

    const text = await res.text().catch(() => "");
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);

    return text ? (JSON.parse(text) as T) : ({} as T);
  } finally {
    clearTimeout(t);
  }
}

async function fetchForm<T>(path: string, form: FormData, timeoutMs = 30000): Promise<T> {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${API}${path}`, { method: "POST", body: form, signal: controller.signal });
    const text = await res.text().catch(() => "");
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
    return text ? (JSON.parse(text) as T) : ({} as T);
  } finally {
    clearTimeout(t);
  }
}

export const apiClient = {
  listJobs: () => fetchJSON<{ jobs: Job[] }>("/api/jobs", { method: "GET" }),
  getJob: async (id: string) => {
    const res = await fetchJSON<any>(`/api/jobs/${encodeURIComponent(id)}`, { method: "GET" });
    return (res?.job ?? res) as Job;
  },
  createJob: (payload: any) => fetchJSON<any>("/api/jobs", { method: "POST", body: JSON.stringify(payload) }),
  cancelJob: (id: string) => fetchJSON<any>(`/api/jobs/${encodeURIComponent(id)}/cancel`, { method: "POST" }),

  listDatasets: () => fetchJSON<{ datasets: Dataset[] }>("/api/datasets", { method: "GET" }),
  uploadDataset: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchForm<any>("/api/datasets/upload", form);
  },
};

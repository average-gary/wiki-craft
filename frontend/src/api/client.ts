const API_BASE = '/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = response.statusText;
    try {
      const errorData = await response.json();
      message = errorData.detail || errorData.message || message;
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, response.statusText, message);
  }
  return response.json();
}

export async function apiGet<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  return handleResponse<T>(response);
}

export async function apiPost<T, B = unknown>(endpoint: string, body?: B): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  return handleResponse<T>(response);
}

export async function apiDelete<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'DELETE',
    headers: {
      'Accept': 'application/json',
    },
  });

  return handleResponse<T>(response);
}

export async function apiUpload<T>(endpoint: string, file: File, metadata?: Record<string, unknown>): Promise<T> {
  const formData = new FormData();
  formData.append('file', file);
  
  if (metadata) {
    formData.append('custom_metadata', JSON.stringify(metadata));
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<T>(response);
}

export async function apiUploadMultiple<T>(endpoint: string, files: File[]): Promise<T> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<T>(response);
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const response = await fetch('/health');
  return handleResponse(response);
}

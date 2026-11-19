
const API_URL = 'http://127.0.0.1:8000';

export async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = Object.values(data)
      .flat()
      .join(' ');

    throw new Error(message || 'Ocurrió un error en el servidor.');
  }

  return data;
}

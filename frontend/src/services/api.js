const defaultApiUrl = typeof window === 'undefined'
  ? 'http://127.0.0.1:8000'
  : `${window.location.protocol}//${window.location.hostname}:8000`;
const API_URL = import.meta.env.VITE_API_URL || defaultApiUrl;
const REFRESH_COOKIE_HEADER = 'X-Refresh-Token-Cookie';
const PUBLIC_ENDPOINTS = [
  '/api/token/',
  '/api/token/refresh/',
  '/api/auth/registro/',
  '/api/auth/verificar-correo/',
  '/api/auth/verificar-correo/reenviar/',
  '/api/auth/recuperar-contrasena/',
  '/api/auth/recuperar-contrasena/confirmar/',
  '/api/auth/cerrar-sesion/'
];

let accessToken = null;
let refreshRequest = null;

export function setAccessToken(token) {
  accessToken = token || null;
}

export function clearAccessToken() {
  accessToken = null;
}

function isPublicEndpoint(endpoint) {
  return PUBLIC_ENDPOINTS.includes(endpoint);
}

function resolveUrl(endpoint) {
  const url = new URL(endpoint, API_URL);
  if (url.origin !== new URL(API_URL).origin) {
    throw new Error('La API devolvió una URL de paginación no válida.');
  }
  return url.toString();
}

async function readResponse(response) {
  if (response.status === 204) return null;
  const contentType = response.headers.get('Content-Type') || '';
  if (!contentType.toLowerCase().includes('json')) return null;
  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

function errorMessage(status, data) {
  if (status === 500 || status === 502) {
    return 'El servidor encontró un error. Inténtalo más tarde.';
  }
  const details = data && typeof data === 'object'
    ? Object.entries(data)
      .map(([field, messages]) => {
        const message = Array.isArray(messages) ? messages.join(' ') : messages;
        if (typeof message !== 'string') return '';
        return field === 'detail' || field === 'error'
          ? message
          : `${field}: ${message}`;
      })
      .filter(Boolean)
      .join(' ')
    : '';

  if (details) return details;
  if (status === 400) return 'Revisa los datos ingresados.';
  if (status === 401) return 'Tu sesión venció o las credenciales no son válidas. Inicia sesión nuevamente.';
  if (status === 403) return 'Tu rol no tiene permiso para realizar esta acción.';
  if (status === 404) return 'No se encontró el recurso solicitado.';
  if (status === 409) return 'La operación entra en conflicto con los datos actuales. Actualiza e inténtalo de nuevo.';
  if (status === 503) return 'El servicio no está disponible temporalmente. Inténtalo más tarde.';
  return 'Ocurrió un error al comunicarse con el servidor.';
}

function apiError(status, data) {
  const error = new Error(errorMessage(status, data));
  error.status = status;
  return error;
}

function notifyAuthenticationExpired() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('planificai:auth-expired'));
  }
}

async function sendRequest(endpoint, options, token = accessToken) {
  const headers = new Headers(options.headers || {});
  headers.set('Accept', 'application/json');
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  headers.delete('Authorization');
  headers.delete('X-Workspace-ID');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const workspaceId = localStorage.getItem('planificai_workspace');
  if (workspaceId) headers.set('X-Workspace-ID', workspaceId);

  if (endpoint === '/api/token/' || endpoint === '/api/token/refresh/') {
    headers.set(REFRESH_COOKIE_HEADER, '1');
  }

  return fetch(resolveUrl(endpoint), {
    ...options,
    credentials: 'include',
    headers
  });
}

async function refreshAccessToken() {
  if (!refreshRequest) {
    refreshRequest = (async () => {
      try {
        const response = await sendRequest('/api/token/refresh/', {
          method: 'POST',
          body: JSON.stringify({})
        }, null);
        const data = await readResponse(response);
        if (!response.ok || !data?.access) {
          clearAccessToken();
          const error = apiError(response.status, data);
          if (response.status === 400 || response.status === 401) {
            notifyAuthenticationExpired();
          }
          throw error;
        }
        setAccessToken(data.access);
        return data.access;
      } catch (error) {
        clearAccessToken();
        if (error instanceof TypeError) {
          throw new Error('No se pudo conectar con el servidor.');
        }
        throw error;
      } finally {
        refreshRequest = null;
      }
    })();
  }
  return refreshRequest;
}

export async function apiRequest(endpoint, options = {}) {
  if (!isPublicEndpoint(endpoint) && !accessToken) {
    await refreshAccessToken();
  }

  let response;
  try {
    response = await sendRequest(endpoint, options);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error('No se pudo conectar con el servidor.');
    }
    throw error;
  }

  if (response.status === 401 && !isPublicEndpoint(endpoint)) {
    try {
      await refreshAccessToken();
      response = await sendRequest(endpoint, options);
      if (response.status === 401) {
        clearAccessToken();
        notifyAuthenticationExpired();
      }
    } catch (error) {
      clearAccessToken();
      throw error;
    }
  }

  const data = await readResponse(response);
  if (!response.ok) {
    throw apiError(response.status, data);
  }
  return data;
}

export async function apiList(endpoint) {
  const items = [];
  let next = endpoint;

  while (next) {
    const data = await apiRequest(next);
    if (Array.isArray(data)) return items.concat(data);
    if (!data || !Array.isArray(data.results)) {
      throw new Error('La respuesta de la API tiene un formato de lista no válido.');
    }

    items.push(...data.results);
    next = data.next;
  }

  return items;
}

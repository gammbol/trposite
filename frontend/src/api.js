// The containerized frontend and backend share one public origin through
// nginx. A relative base URL avoids CORS, mixed-content and localhost:8000
// mistakes in production builds.
const API_BASE_URL = (process.env.REACT_APP_API_URL || '/api').replace(/\/$/, '');

async function parseResponse(response) {
  let data = {};

  if (response.status !== 204) {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const body = await response.text();
      throw new Error(
        `Сервер вернул неожиданный ответ (${response.status})${body ? `: ${body.slice(0, 160)}` : ''}`
      );
    }
  }

  if (!response.ok) {
    const message = data.error || data.detail || `Ошибка сервера (${response.status})`;
    const requestError = new Error(message);
    requestError.data = data;
    requestError.status = response.status;
    throw requestError;
  }

  return data;
}

async function apiFetch(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      credentials: 'same-origin',
      ...options,
    });
  } catch (error) {
    throw new Error('Не удалось связаться с backend. Проверьте состояние контейнеров.');
  }
  return parseResponse(response);
}

export const solveEquation = (data) => apiFetch('/solve/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});

export const explainWithAI = (data) => apiFetch('/explain/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});

export const verifyWithConsensus = (data) => apiFetch('/consensus/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});

export const getHistory = (limit = 50) => apiFetch(`/history/?limit=${encodeURIComponent(limit)}`);

export const deleteHistoryEntry = (id) => apiFetch(`/history/${encodeURIComponent(id)}/`, {
  method: 'DELETE',
});

export const clearHistory = () => apiFetch('/history/', {
  method: 'DELETE',
});

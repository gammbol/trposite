import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

async function parseResponse(response) {
  let data = {};

  try {
    data = await response.json();
  } catch (error) {
    throw new Error(`Сервер вернул некорректный ответ (${response.status})`);
  }

  if (!response.ok) {
    const message = data.error || data.detail || `Ошибка сервера (${response.status})`;
    const requestError = new Error(message);
    requestError.data = data;
    throw requestError;
  }

  return data;
}

export const solveEquation = async (data) => {
  const response = await fetch(`${API_BASE_URL}/solve/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return parseResponse(response);
};

export const explainWithAI = async (data) => {
  const response = await fetch(`${API_BASE_URL}/explain/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return parseResponse(response);
};

export const getHistory = async () => {
  const response = await axios.get(`${API_BASE_URL}/history/`);
  return response.data;
};

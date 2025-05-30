import axios from 'axios';

const API_URL = 'http://109.120.187.72:5999/api';

export const solveEquation = async (equation, variable = 'x') => {
  const response = await axios.post(`${API_URL}/solve`, {equation, variable}, {
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: false
  });
  return response.data;
};

export const getHistory = async () => {
  const response = await axios.get(`${API_URL}/history`);
  return response.data;
};

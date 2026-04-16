import axios from 'axios';

export const solveEquation = async (equation, variable = 'x') => {
  const response = await axios.post(`${process.env.REACT_APP_API_URL || "http://localhost:8000/api"}/solve`, {
    equation,
    variable
  });
  return response.data;
};

export const getHistory = async () => {
  const response = await axios.get(`${process.env.REACT_APP_API_URL || "http://localhost:8000/api"}/history`);
  return response.data;
};


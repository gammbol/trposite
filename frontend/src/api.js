import axios from 'axios';

export const solveEquation = async (data) => {
  const response = await fetch("http://localhost:8000/api/solve/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  return response.json();
};

export const getHistory = async () => {
  const response = await axios.get(`${process.env.REACT_APP_API_URL || "http://localhost:8000/api"}/history`);
  return response.data;
};


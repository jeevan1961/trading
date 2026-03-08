import axios from "axios";

const API_BASE = import.meta.env.VITE_BACKEND_URL;

const api = axios.create({
  baseURL: API_BASE
});

export async function getRadar() {
  const res = await api.get("/api/radar");
  return res.data;
}

export async function checkBackend() {
  const res = await api.get("/");
  return res.data;
}

export default api;

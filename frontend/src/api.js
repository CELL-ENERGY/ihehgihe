import axios from 'axios';

// Use VITE_API_URL if set; otherwise use same origin in production or localhost in dev
const envUrl = import.meta.env.VITE_API_URL;
const API_URL = (envUrl && envUrl.trim() !== '')
  ? envUrl
  : (typeof window !== 'undefined' && window.location.origin ? window.location.origin : 'http://localhost:8000');

const api = axios.create({
  baseURL: API_URL,
});

// Automatically inject JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
export { API_URL };

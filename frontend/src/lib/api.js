/**
 * Axios instance pre-configured with the backend base URL.
 * Token refresh interceptor will be implemented in Phase 4.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

export default api;

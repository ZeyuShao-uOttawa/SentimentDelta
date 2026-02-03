import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_FLASK_URL || 'http://localhost:4000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Optional: Add interceptors for global error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Flask API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default axiosInstance;
import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Candidate API URLs
const DEFAULT_URL = Platform.select({
  android: 'http://10.0.2.2:8000/api', // Android Emulator default
  default: 'http://127.0.0.1:8000/api', // Web / iOS / Local
});

const LAN_URL = 'http://192.168.1.2:8000/api'; // WiFi IP for physical Android devices

let currentBaseUrl = DEFAULT_URL;

export const setApiBaseUrl = async (url: string) => {
  currentBaseUrl = url;
  await AsyncStorage.setItem('RAAH_API_URL', url);
};

export const getApiBaseUrl = () => currentBaseUrl;

// Initialize from storage or default
AsyncStorage.getItem('RAAH_API_URL').then((stored) => {
  if (stored) {
    currentBaseUrl = stored;
  }
});

const client = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use(async (config) => {
  config.baseURL = currentBaseUrl;
  return config;
});

// Response interceptor with auto-fallback from 10.0.2.2 to LAN IP if network fails
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      !originalRequest._retry &&
      error.message &&
      (error.message.includes('Network Error') || error.code === 'ECONNABORTED') &&
      currentBaseUrl !== LAN_URL
    ) {
      originalRequest._retry = true;
      currentBaseUrl = LAN_URL;
      originalRequest.baseURL = LAN_URL;
      return client(originalRequest);
    }
    return Promise.reject(error);
  }
);

export const ApiService = {
  // QR & Scan
  resolveQR: async (qrContent: string, userId: string = 'user_default_01') => {
    const res = await client.post('/scan/resolve', { qr_content: qrContent, user_id: userId });
    return res.data;
  },

  // Payments
  createTestOrder: async (payload: {
    merchant_id: string;
    amount: number;
    user_id?: string;
    force_scenario?: string;
    idempotency_key?: string;
    acknowledged_duplicate?: boolean;
  }) => {
    const res = await client.post('/payments/test-order', payload);
    return res.data;
  },

  listTransactions: async (limit: number = 20) => {
    const res = await client.get('/payments/list', { params: { limit } });
    return res.data;
  },

  getTransaction: async (txId: string) => {
    const res = await client.get(`/payments/${txId}`);
    return res.data;
  },

  getPaymentJourney: async (txId: string) => {
    const res = await client.get(`/payments/${txId}/journey`);
    return res.data;
  },

  verifyPayment: async (txId: string, simulateNetworkDrop: boolean = false) => {
    const res = await client.post(`/payments/${txId}/verify`, {
      simulate_network_drop: simulateNetworkDrop,
    });
    return res.data;
  },

  // Cases
  getCase: async (caseId: string) => {
    const res = await client.get(`/cases/${caseId}`);
    return res.data;
  },

  getCaseActions: async (caseId: string) => {
    const res = await client.get(`/cases/${caseId}/actions`);
    return res.data;
  },

  triggerCaseFollowup: async (caseId: string, reason?: string) => {
    const res = await client.post(`/cases/${caseId}/followup`, { reason });
    return res.data;
  },

  escalateCase: async (caseId: string, reason: string) => {
    const res = await client.post(`/cases/${caseId}/escalate`, { reason });
    return res.data;
  },

  // Raah Pulse (Operations)
  getSystemHealth: async () => {
    const res = await client.get('/incidents/health');
    return res.data;
  },

  listIncidents: async () => {
    const res = await client.get('/incidents');
    return res.data;
  },

  getIncident: async (incidentId: string) => {
    const res = await client.get(`/incidents/${incidentId}`);
    return res.data;
  },

  reviewIncident: async (incidentId: string, action: string, notes?: string) => {
    const res = await client.post(`/incidents/${incidentId}/review`, { action, notes });
    return res.data;
  },

  // Ask Raah (Contextual Chat)
  createChatSession: async (payload: {
    user_id?: string;
    transaction_id?: string;
    case_id?: string;
    initial_message?: string;
  }) => {
    const res = await client.post('/chat/sessions', payload);
    return res.data;
  },

  listChatSessions: async (userId: string = 'user_default_01') => {
    const res = await client.get('/chat/sessions', { params: { user_id: userId } });
    return res.data;
  },

  getSessionMessages: async (sessionId: string) => {
    const res = await client.get(`/chat/sessions/${sessionId}/messages`);
    return res.data;
  },

  sendMessage: async (sessionId: string, content: string, transactionId?: string) => {
    const res = await client.post(`/chat/sessions/${sessionId}/messages`, {
      content,
      transaction_id: transactionId,
    });
    return res.data;
  },

  // Demo Scenarios Control
  listScenarios: async () => {
    const res = await client.get('/demo/scenarios');
    return res.data;
  },

  triggerScenario: async (scenarioId: string, amount: number = 4000.0) => {
    const res = await client.post(`/demo/scenarios/${scenarioId}/trigger`, { amount });
    return res.data;
  },

  resetDemo: async () => {
    const res = await client.post('/demo/reset');
    return res.data;
  },

  seedDemo: async () => {
    const res = await client.post('/demo/seed');
    return res.data;
  },
};

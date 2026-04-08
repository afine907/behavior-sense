import ky, { type KyInstance, type Options } from 'ky';

// Use proxy paths in browser to avoid CORS issues
// In SSR, use direct URLs
const getApiBaseUrl = (service: string, directUrl: string): string => {
  if (typeof window !== 'undefined') {
    // Browser: use proxy path
    return `/api/${service}`;
  }
  // SSR: use direct URL
  return directUrl;
};

// Environment-based API base URLs
const API_DIRECT_URLS = {
  mock: process.env.NEXT_PUBLIC_API_MOCK || 'http://localhost:8001',
  rules: process.env.NEXT_PUBLIC_API_RULES || 'http://localhost:8002',
  insight: process.env.NEXT_PUBLIC_API_INSIGHT || 'http://localhost:8003',
  audit: process.env.NEXT_PUBLIC_API_AUDIT || 'http://localhost:8004',
  logs: process.env.NEXT_PUBLIC_API_LOGS || 'http://localhost:8005',
} as const;

// Custom error class for API errors
export class ApiClientError extends Error {
  public code: number;
  public traceId?: string;

  constructor(message: string, code: number, traceId?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
    this.traceId = traceId;
  }
}

// Create API client factory
function createApiClient(baseUrl: string): KyInstance {
  return ky.create({
    prefixUrl: baseUrl,
    timeout: 30000,
    hooks: {
      beforeRequest: [
        (request) => {
          // Add auth token if available
          if (typeof window !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token) {
              request.headers.set('Authorization', `Bearer ${token}`);
            }
          }
          // Add trace ID for debugging
          request.headers.set('X-Request-Id', crypto.randomUUID());
        },
      ],
      afterResponse: [
        (_request, _options, response) => {
          // Handle 401 unauthorized
          if (response.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem('token');
            // Only redirect if not already on login page
            if (!window.location.pathname.includes('/login')) {
              window.location.href = '/login';
            }
          }
          return response;
        },
      ],
    },
  });
}

// Create API clients for each service
// Use proxy paths in browser to avoid CORS issues
export const mockApi = createApiClient(getApiBaseUrl('mock', API_DIRECT_URLS.mock));
export const rulesApi = createApiClient(getApiBaseUrl('rules', API_DIRECT_URLS.rules));
export const insightApi = createApiClient(getApiBaseUrl('insight', API_DIRECT_URLS.insight));
export const auditApi = createApiClient(getApiBaseUrl('audit', API_DIRECT_URLS.audit));
export const logsApi = createApiClient(getApiBaseUrl('logs', API_DIRECT_URLS.logs));

// Re-export types
export type { KyInstance, Options };

// API Service - Connects frontend to FastAPI backend
// Uses environment variable for API base URL

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface AnalysisResult {
  id: string;
  type: "url" | "cti" | "ip" | "device";
  input: string;
  score: number;
  severity: "low" | "medium" | "high" | "critical";
  verdict: string;
  indicators: string[];
  iocs: { type: string; value: string }[];
  mitre?: { id: string; name: string }[];
  recommendations: string[];
  timestamp: number;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Request Failed:', error);
      throw error;
    }
  }

  async analyzeUrl(url: string): Promise<AnalysisResult> {
    return this.request('/analyze/url', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  }

  async analyzeIP(ip: string): Promise<AnalysisResult> {
    return this.request('/analyze/ip', {
      method: 'POST',
      body: JSON.stringify({ ip }),
    });
  }

  async analyzeCTI(report: string): Promise<AnalysisResult> {
    return this.request('/analyze/report', {
      method: 'POST',
      body: JSON.stringify({ report }),
    });
  }

  async analyzeDevice(deviceInfo: Record<string, unknown>): Promise<AnalysisResult> {
    return this.request('/analyze/device', {
      method: 'POST',
      body: JSON.stringify(deviceInfo),
    });
  }

  async analyzePCAP(file: File): Promise<AnalysisResult> {
    const formData = new FormData();
    formData.append('file', file);

    return fetch(`${this.baseUrl}/analyze/pcap`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json());
  }

  async getHistory(): Promise<AnalysisResult[]> {
    return this.request('/history');
  }

  async saveHistory(result: AnalysisResult): Promise<void> {
    return this.request('/history', {
      method: 'POST',
      body: JSON.stringify(result),
    });
  }

  async healthCheck(): Promise<{ status: string }> {
    return this.request('/')
      .catch(() => ({ status: 'Backend unavailable' }));
  }
}

export const api = new APIClient(API_BASE_URL);

// Export for debugging
export { API_BASE_URL };

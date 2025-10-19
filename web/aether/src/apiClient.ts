
export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

export type RequestBody =
  | { type: "json"; data: unknown }
  | { type: "formUrlEncode"; data: Record<string, string> };

export interface Endpoint {
  path: string;
  method: HttpMethod;
  body?: RequestBody;
  requireAuth: boolean;
}

export interface INetworkService {
  request<T>(endpoint: Endpoint): Promise<T>;
}

export class NetworkService implements INetworkService {
  private readonly baseUrl: string;
  private readonly authService: AuthService;

  constructor(baseUrl: string, authService: AuthService) {
    this.baseUrl = baseUrl;
    this.authService = authService;
  }

  async request<T>(endpoint: Endpoint): Promise<T> {
    const url = `${this.baseUrl}${endpoint.path}`;
    const headers = new Headers();

    if (endpoint.requireAuth) {
      const token = this.authService.getAccessToken();
      if (!token) {
        throw new Error("Authentication token not found");
      }
      headers.append("Authorization", `Bearer ${token}`);
    }
  }
}

export interface RegisterRequest {
    name: string;
    email: string;
    password: string;
}

export interface RawRegisterResponse {
    id: string;
    name: string;
    email: string;
    created_at: string;
}

export interface RegisterResponse {
    id: string;
    name: string;
    email: string;
    createdAt: string;
}

export interface loginRequest {
    email: string;
    password: string;
}

export interface TokenResponse {
    accessToken: string;
    refreshToken: string;
    tokenType: string;
}

export interface RawTokenResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface ErrorResponse {
    detail: string;
}

export interface User {
    id: string;
    name: string;
    email: string;
}

import Foundation


enum AuthError: Error {
    case invalidURL
    case invalidCredentials(String)
    case serverError(String)
    case decodingError
    case unknownError
}


class AuthService {
    private let baseURL = "http://192.168.2.13:8000"
    
    func login(credentials: LoginRequest) async throws -> TokenResponse {
        guard let url = URL(string: "\(baseURL)/login") else {
            throw AuthError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        request.httpBody = try JSONEncoder().encode(credentials)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.unknownError
        }
        
        switch httpResponse.statusCode {
        case 200...299:
            do {
                let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
                return tokenResponse
            } catch {
                throw AuthError.decodingError
            }
            
        case 401:
            do {
                let errorResponse = try JSONDecoder().decode(ErrorResponse.self, from: data)
                throw AuthError.invalidCredentials(errorResponse.detail)
            } catch {
                throw AuthError.invalidCredentials("incorrect email or password")
            }
            
        default:
            throw AuthError.serverError("server error: status code: \(httpResponse.statusCode)")
        }
    }
}


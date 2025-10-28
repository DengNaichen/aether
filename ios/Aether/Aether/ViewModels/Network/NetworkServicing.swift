import Foundation
import Combine
import OSLog


enum LogLevel: String {
    case debug = "🔍"
    case info = "ℹ️"
    case warning = "⚠️"
    case error = "❌"
    case success = "✅"
}


struct NetworkLogger {
    private static let subsystem = Bundle.main.bundleIdentifier ?? "com." // TODO: what is this mean ?
    private static let logger = Logger(subsystem: subsystem, category: "Network")
    
    static func log(_ message: String, level: LogLevel = .info, error: Error? = nil) {
        let logMessage = "\(level.rawValue) [Network] \(message)"
        switch level {
        case .debug:
            logger.debug("\(logMessage)")
        case .info:
            logger.info("\(logMessage)")
        case .warning:
            logger.warning("\(logMessage)")
        case .error:
            if let error = error {
                logger.error("\(logMessage): \(error.localizedDescription)")
            } else {
                logger.error("\(logMessage)")
            }
        case .success:
            logger.info("\(logMessage)")
        }
        #if DEBUG
        print(logMessage)
        if let error {
            print("Error details: \(error)")
        }
        #endif
    }
}


protocol NetworkServicing {
    func request<T: Decodable> (
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T
}


struct NetworkConfiguration {
    let baseURL: URL
    let session: URLSession
    let retryLimit: Int
    let requestTimeout: TimeInterval
    
    init(
        baseURL: URL,
        session: URLSession = .shared,
        retryLimit: Int = 3,
        requestTimeout: TimeInterval = 30
    ) {
        self.baseURL = baseURL
        self.session = session
        self.retryLimit = retryLimit
        self.requestTimeout = requestTimeout
    }
}

class NetworkService: NetworkServicing {
    private let configuration: NetworkConfiguration
    private let authService: AuthService
    private let decoder: JSONDecoder
    
    init(
        configuration: NetworkConfiguration,
        authService: AuthService
    ) {
        self.configuration = configuration
        self.authService = authService
        self.decoder = JSONDecoder()
        self.decoder.dateDecodingStrategy = .iso8601
    }
    
    convenience init(
        baseURL: URL,
        session: URLSession = .shared,
        authService: AuthService
    ) {
        self.init(
            configuration: NetworkConfiguration(baseURL: baseURL, session: session),
            authService: authService
        )
    }
    
    // Conformance: exact signature required by the protocol
    func request<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        try await performRequest(
            endpoint: endpoint,
            responseType: responseType,
            attemptCount: 0)
    }
    
    private func performRequest<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type,
        attemptCount: Int
    ) async throws -> T {
        let urlRequest = try await buildURLREquest(for: endpoint)
        
        logRequest(urlRequest, endpoint: endpoint)
        
        let (data, response) = try await configuration.session.data(for: urlRequest)
        
        return try await handleResponse(
            data: data,
            response: response,
            endpoint: endpoint,
            responseType: responseType,
            attemptCount: attemptCount
        )
    }
    
    
    private func buildURLREquest(for endpoint: Endpoint) async throws -> URLRequest {
        guard let url = URL(string: endpoint.path, relativeTo: configuration.baseURL) else {
            NetworkLogger.log("Invalid URL for endpoint: \(endpoint.path)", level: .error)
            throw NetworkError.invalidURL
        }
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = endpoint.method.rawValue
        urlRequest.timeoutInterval = configuration.requestTimeout
        
        if endpoint.requiredAuth {
            guard let token = await authService.accessToken else {
                NetworkLogger.log("Token not found for authenticated endpoint", level: .error)
                throw NetworkError.tokenNotFound
            }
            // Debug: Log the token being used (first 20 chars only for security)
            let tokenPreview = String(token.prefix(20))
            NetworkLogger.log("Using access token: \(tokenPreview)...", level: .debug)
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let body = endpoint.body {
            try addBody(body, to: &urlRequest)
        }
        return urlRequest
    }
    
    private func addBody(_ body: RequestBody, to urlRequest: inout URLRequest) throws {
        // TODO why this RequestBody so important here
        switch body {
        case .json(let encodableData):
            urlRequest.httpBody = try JSONEncoder().encode(encodableData)
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
        case .formUrlEncoded(let formData):
            let bodyString = formData.map { key, value in
                let encodedKey = key.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
                let encodedValue = value.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
                return "\(encodedKey)=\(encodedValue)"
            }.joined(separator: "&")
            
            urlRequest.httpBody = bodyString.data(using: .utf8)
            urlRequest.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        }
    }
        
    private func handleResponse<T: Decodable>(
        data: Data,
        response: URLResponse,
        endpoint: Endpoint,
        responseType: T.Type,
        attemptCount: Int
    ) async throws -> T {
        guard let httpResponse = response as? HTTPURLResponse else {
            NetworkLogger.log("Invalid response type", level: .error)
            throw NetworkError.unknownError
        }
        
        logResponse(httpResponse, data: data)
        
        switch httpResponse.statusCode {
        case 200...299:
            return try decodeResponse(data: data, responseType: responseType)
            
        case 401:
            return try await handleUnauthorized(
                endpoint: endpoint,
                responseType: responseType,
                attemptCount: attemptCount
            )
            
        case 402...499:
            throw try handleClientError(data: data)
            
        case 500...599:
            throw try handleServerError(data: data)
            
        default:
            NetworkLogger.log("Unexpected status code: \(httpResponse.statusCode)", level: .error)
            throw NetworkError.unknownError
        }
    }
        
    private func decodeResponse<T: Decodable>(
        data: Data,
        responseType: T.Type
    ) throws -> T {
        do {
            let decodedResponse = try decoder.decode(T.self, from: data)
            NetworkLogger.log("Successfully decoded response", level: .success)
            return decodedResponse
        } catch {
            logDecodingError(data: data, error: error)
            throw NetworkError.decodingFailed
        }
    }
        
    private func handleUnauthorized<T: Decodable>(
            endpoint: Endpoint,
            responseType: T.Type,
            attemptCount: Int
    ) async throws -> T {
        // Check if this is a retry
        guard attemptCount < configuration.retryLimit else {
            NetworkLogger.log("Max retry attempts reached, logging out", level: .warning)
            await MainActor.run {
                Task {
                    await authService.logout()
                }
            }
            throw NetworkError.tokenNotFound
        }
        
        NetworkLogger.log("Attempting to refresh token...", level: .info)
        
        do {
            let refreshSuccess = try await authService.refreshTokens(networkService: self)

            if refreshSuccess {
                NetworkLogger.log("Token refreshed successfully, retrying request", level: .success)

                // Debug: Check what token we'll use for retry
                if let retryToken = await authService.accessToken {
                    let retryTokenPreview = String(retryToken.prefix(20))
                    NetworkLogger.log("About to retry with token: \(retryTokenPreview)...", level: .debug)
                } else {
                    NetworkLogger.log("WARNING: No access token available for retry!", level: .warning)
                }

                return try await performRequest(
                    endpoint: endpoint,
                    responseType: responseType,
                    attemptCount: attemptCount + 1
                )
            } else {
                NetworkLogger.log("Token refresh failed", level: .error)
                await MainActor.run {
                    Task {
                        await authService.logout()
                    }
                }
                throw NetworkError.tokenNotFound
            }
        } catch {
            NetworkLogger.log("Token refresh error", level: .error, error: error)
            await MainActor.run {
                Task {
                    await authService.logout()
                }
            }
            throw NetworkError.tokenNotFound
        }
    }
        
    private func handleClientError(data: Data) throws -> Error {
        if let errorDetail = try? decoder.decode(ErrorDetail.self, from: data) {
            NetworkLogger.log("Client error: \(errorDetail.detail)", level: .error)
            throw NetworkError.clientError(errorDetail.detail)
        } else {
            NetworkLogger.log("Client error: Unable to parse error details", level: .error)
            throw NetworkError.clientError("Failed to parse server info")
        }
    }


    private func handleServerError(data: Data) throws -> Error {
        if let errorDetail = try? decoder.decode(ErrorDetail.self, from: data) {
            NetworkLogger.log("Server error: \(errorDetail.detail)", level: .error)
            throw NetworkError.serverError(errorDetail.detail)
        } else {
            NetworkLogger.log("Server error: Unable to parse error details", level: .error)
            throw NetworkError.serverError("Failed to parse server info")
        }
    }

        
    // MARK: - Logging Helpers
    
    private func logRequest(_ request: URLRequest, endpoint: Endpoint) {
        let method = request.httpMethod ?? "UNKNOWN"
        let url = request.url?.absoluteString ?? "Invalid URL"
        
        NetworkLogger.log("\(method) \(url)", level: .info)
        
        #if DEBUG
        if let body = request.httpBody,
           let bodyString = String(data: body, encoding: .utf8) {
            NetworkLogger.log("Request Body: \(bodyString)", level: .debug)
        }
        #endif
    }
        
    private func logResponse(_ response: HTTPURLResponse, data: Data) {
        let statusCode = response.statusCode
        let url = response.url?.absoluteString ?? "Unknown URL"
        
        let level: LogLevel = (200...299).contains(statusCode) ? .success : .warning
        NetworkLogger.log("Response [\(statusCode)] from \(url)", level: level)
        
        #if DEBUG
        if let responseString = String(data: data, encoding: .utf8) {
            NetworkLogger.log("Response Body: \(responseString)", level: .debug)
        }
        #endif
    }
        
    private func logDecodingError(data: Data, error: Error) {
        NetworkLogger.log("Decoding failed", level: .error, error: error)
        
        #if DEBUG
        if let jsonString = String(data: data, encoding: .utf8) {
            NetworkLogger.log("Raw JSON: \(jsonString)", level: .debug)
        }
        #endif
    }
}

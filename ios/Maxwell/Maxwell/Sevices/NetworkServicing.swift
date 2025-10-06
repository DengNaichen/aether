import Foundation


enum HTTPMethod: String {
    case GET, POST, PUT, DELETE
}

protocol NetworkServicing {
    func request<T: Decodable, U: Encodable> (
        endpoint: String,
        method: HTTPMethod,
        body: U?,
        responseType: T.Type
    ) async throws -> T
}


class NetworkService: NetworkServicing {
    private let baseURL: URL
    private let session: URLSession
    
    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }
    
    func request<T: Decodable, U: Encodable>(
        endpoint: String,
        method: HTTPMethod,
        body: U?,
        responseType: T.Type
    ) async throws -> T {
        
        guard let url = URL(string: endpoint, relativeTo: baseURL) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.unknownError
        }
        
        switch httpResponse.statusCode {
        case 200...299:
            do {
                return try JSONDecoder().decode(T.self, from: data)
            } catch {
                throw NetworkError.decodingFailed
            }

        case 400...499:
            if let errorDetail = try? JSONDecoder().decode(ErrorDetail.self, from: data) {
                throw NetworkError.clientError(errorDetail.detail)
            } else {
                throw NetworkError.clientError("Failed to parse server info")
            }
            
        case 500...599:
            if let errorDetail = try? JSONDecoder().decode(ErrorDetail.self, from: data) {
                throw NetworkError.serverError(errorDetail.detail)
            } else {
                throw NetworkError.serverError("Failed to parse server info")
            }
        default:
            throw NetworkError.unknownError
        }
    }
}

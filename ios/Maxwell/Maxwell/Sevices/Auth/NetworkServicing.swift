import Foundation

enum RequestBody {
    case json(Encodable)
    case formUrlEncoded([String: String])
}

enum HTTPMethod: String {
    case GET, POST, PUT, DELETE
}

protocol NetworkServicing {
    func request<T: Decodable> (
        endpoint: String,
        method: HTTPMethod,
        body: RequestBody?,
        responseType: T.Type
    ) async throws -> T

//    func requestToken(endpoint: String,
//                      fromData: [String: String]
//    ) async throws -> TokenResponse
}


class NetworkService: NetworkServicing {
    private let baseURL: URL
    private let session: URLSession
    
    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }
    
    func request<T: Decodable>(
        endpoint: String,
        method: HTTPMethod,
        body: RequestBody?,
        responseType: T.Type
    ) async throws -> T {
        
        guard let url = URL(string: endpoint, relativeTo: baseURL) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            switch body {
            case .json(let encodableData):
                request.httpBody = try JSONEncoder().encode(encodableData)
                request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            
            case .formUrlEncoded(let formData):
                let bodyString = formData.map { key, value in
                    "\(key.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")=\(value.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")"
                }.joined(separator: "&")
                request.httpBody = bodyString.data(using: .utf8)
                request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            }
            
        }

        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.unknownError
        }
        
        switch httpResponse.statusCode {
        case 200...299:
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                return try decoder.decode(T.self, from: data)
            } catch {
                print("==================== 🐛DECODING ERROR ====================")
                print("Failed to decode JSON. Server returned the following data:")
                if let jsonString = String(data: data, encoding: .utf8) {
                    print(jsonString)
                } else {
                    print("Could not convert data to a readable string.")
                }
                print("==========================================================")
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

import Foundation
import Combine



protocol NetworkServicing {
    func request<T: Decodable> (
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T
}

class NetworkService: NetworkServicing, ObservableObject {
    private let baseURL: URL
    private let session: URLSession
    private let authService: AuthService
    
    init(baseURL: URL, session: URLSession = .shared, authService: AuthService) {
        self.baseURL = baseURL
        self.session = session
        self.authService = authService
    }
    
    func request<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        
        guard let url = URL(string: endpoint.path, relativeTo: baseURL) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        
        if endpoint.requiredAuth {
            print("➡️ [NetworkService] Endpoint '\(endpoint.path)' requires auth. Asking AuthService for token...")
            guard let token = authService.accessToken else {
                print("🛑 [NetworkService] CRITICAL: Token not found from AuthService!")
                throw NetworkError.tokenNotFound
            }
            print("✅ [NetworkService] Got token from AuthService. Adding to header.")
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            print("➡️ [NetworkService] Endpoint '\(endpoint.path)' does not require auth.")
        }
        
        if let body = endpoint.body {
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
            // TODO: delete this later, and do the refresh token.
        case 401:
            // 如果是 401 Unauthorized 错误
            // 立即通知 AuthService 用户需要重新登录
            await MainActor.run {
                authService.logout()
            }
            throw NetworkError.tokenNotFound

        case 402...499:
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


enum MockNetworkError: Error, LocalizedError {
    case generalError
    var errorDescription: String? {
        "A mock network error occurred."
    }
}


class MockNetworkService: NetworkServicing, ObservableObject {
    
    var mockResponse: Decodable?
    
    var mockError: Error?
    
    var latency: TimeInterval = 0.5
    
    init() {
        self.mockResponse = FetchAllCoursesResponse(
            courses: [
                FetchCourseResponse(
                    courseId: "swiftui-101",
                    courseName: "SwiftUI 完全指南",
                    courseDescription: "从入门到精通，构建漂亮的iOS应用。",
                    isEnrolled: true,
                    numOfKnowledgeNode: 35),
                FetchCourseResponse(
                    courseId: "swiftdata-201",
                    courseName: "精通 SwiftData",
                    courseDescription: "掌握现代化的数据持久化方案。",
                    isEnrolled: false,
                    numOfKnowledgeNode: 52),
                FetchCourseResponse(
                    courseId: "combine-301",
                    courseName: "响应式编程与 Combine",
                    courseDescription: "学习苹果官方的响应式编程框架。",
                    isEnrolled: false, numOfKnowledgeNode: 48)
                            
            ]
        )
    }

    func request<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        try await Task.sleep(for: .seconds(latency))
        
        if let error = mockError {
            throw error
        }
        
        guard let response = mockResponse as? T else {
            throw MockNetworkError.generalError
        }
        return response
    }
}

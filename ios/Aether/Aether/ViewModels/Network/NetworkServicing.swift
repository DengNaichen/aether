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
    
    // Conformance: exact signature required by the protocol
    func request<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        try await request(endpoint: endpoint, responseType: responseType, isRetry: false)
    }
    
    func request<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type,
        isRetry: Bool = false
    ) async throws -> T {

        guard let url = URL(string: endpoint.path, relativeTo: baseURL) else {
            throw NetworkError.invalidURL
        }

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = endpoint.method.rawValue

        if endpoint.requiredAuth {
            guard let token = authService.accessToken else {
                throw NetworkError.tokenNotFound
            }
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        } else {
            print("➡️ [NetworkService] Endpoint '\(endpoint.path)' does not require auth.")
        }

        if let body = endpoint.body {
            switch body {
            case .json(let encodableData):
                urlRequest.httpBody = try JSONEncoder().encode(encodableData)
                urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")

            case .formUrlEncoded(let formData):
                let bodyString = formData.map { key, value in
                    "\(key.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")=\(value.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")"
                }.joined(separator: "&")
                urlRequest.httpBody = bodyString.data(using: .utf8)
                urlRequest.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
            }
        }


        let (data, response) = try await session.data(for: urlRequest)
        
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
        case 401:
            if isRetry {
                await MainActor.run {
                    authService.logout()
                }
                throw NetworkError.tokenNotFound
            }

            // 尝试刷新 token
            print("🔄 [NetworkService] Attempting to refresh token...")
            do {
                let refreshSuccess = try await authService.refreshTokens(networkService: self)

                if refreshSuccess {
                    // 刷新成功，重试原请求
                    return try await request(
                        endpoint: endpoint,
                        responseType: responseType,
                        isRetry: true  // 标记为重试，防止无限循环
                    )
                } else {
                    await MainActor.run {
                        authService.logout()
                    }
                    throw NetworkError.tokenNotFound
                }
            } catch {
                print("❌ [NetworkService] Token refresh failed: \(error), logging out")
                await MainActor.run {
                    authService.logout()
                }
                throw NetworkError.tokenNotFound
            }
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
    
    /// Configure mock to return quiz questions - MCQ only
    func configureMockQuiz(for courseId: String, questionNum: Int = 10) {
        // Create a pool of MCQ questions to avoid index out of bounds issues
        let mockQuestions: [AnyQuestion] = [
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What is 2 + 2?",
                details: MultipleChoiceDetails(options: ["3", "4", "5", "6"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which of the following is a SwiftUI view modifier?",
                details: MultipleChoiceDetails(options: [".padding()", ".forEach()", ".map()", ".filter()"], correctAnswer: 0)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What does @State do in SwiftUI?",
                details: MultipleChoiceDetails(options: ["Creates a constant value", "Manages view state", "Handles navigation", "Performs networking"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which is the correct way to create a VStack?",
                details: MultipleChoiceDetails(options: ["VStack { }", "VStack()", "VStack[]", "VStack<>"], correctAnswer: 0)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What is the primary purpose of @ObservedObject?",
                details: MultipleChoiceDetails(options: ["Store local state", "Observe external objects", "Handle user input", "Manage animations"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which navigation method is preferred in modern SwiftUI?",
                details: MultipleChoiceDetails(options: ["NavigationView", "NavigationStack", "NavigationLink only", "TabView"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What does the .task modifier do?",
                details: MultipleChoiceDetails(options: ["Handles user taps", "Runs async code when view appears", "Creates animations", "Manages state"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which property wrapper is used for environment values?",
                details: MultipleChoiceDetails(options: ["@State", "@Binding", "@Environment", "@Published"], correctAnswer: 2)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What is SwiftData used for?",
                details: MultipleChoiceDetails(options: ["Networking", "Data persistence", "UI animations", "Image processing"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which is the correct way to handle optional values in Swift?",
                details: MultipleChoiceDetails(options: ["Force unwrapping always", "Optional binding with if let", "Ignoring optionals", "Converting to strings"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What is the purpose of @Published in SwiftUI?",
                details: MultipleChoiceDetails(options: ["Publishes books", "Notifies views of changes", "Handles navigation", "Manages memory"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which SwiftUI container stacks views horizontally?",
                details: MultipleChoiceDetails(options: ["VStack", "HStack", "ZStack", "LazyStack"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What is the correct syntax for a SwiftUI Button?",
                details: MultipleChoiceDetails(options: ["Button(action: {}) { Text(\"Tap\") }", "Button { Text(\"Tap\") }", "Button(\"Tap\") { }", "Button.create(\"Tap\")"], correctAnswer: 0)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "Which modifier adds spacing around a view?",
                details: MultipleChoiceDetails(options: [".margin()", ".padding()", ".spacing()", ".offset()"], correctAnswer: 1)
            )),
            .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: "What does @Binding do in SwiftUI?",
                details: MultipleChoiceDetails(options: ["Creates local state", "Creates two-way binding", "Handles networking", "Manages animations"], correctAnswer: 1)
            ))
        ]
        
        // Ensure we have enough questions, repeat if necessary
        var selectedQuestions: [AnyQuestion] = []
        let availableQuestions = mockQuestions.count
        
        for i in 0..<questionNum {
            let questionIndex = i % availableQuestions
            let originalQuestion = mockQuestions[questionIndex]
            
            // Create a new question with unique ID to avoid conflicts
            let newQuestion: AnyQuestion
            switch originalQuestion {
            case .multipleChoice(let mcq):
                newQuestion = .multipleChoice(MultipleChoiceQuestion(
                    id: UUID(), // Always generate new UUID
                    text: mcq.text,
                    details: mcq.details
                ))
            default:
                // Fallback to a simple MCQ if somehow a non-MCQ slips through
                newQuestion = .multipleChoice(MultipleChoiceQuestion(
                    id: UUID(),
                    text: "Fallback question: What is SwiftUI?",
                    details: MultipleChoiceDetails(options: ["A framework", "A language", "A tool", "A platform"], correctAnswer: 0)
                ))
            }
            selectedQuestions.append(newQuestion)
        }
        
        self.mockResponse = QuizResponse(
            attemptId: UUID(),
            userId: UUID(),
            courseId: courseId,
            questionNum: selectedQuestions.count,
            status: .inProgress,
            createdAt: Date(),
            questions: selectedQuestions
        )
    }
    
    /// Configure mock to return submission response
    func configureMockSubmission() {
        self.mockResponse = QuizSubmissionResponse(
            attemptId: UUID(),
            message: "Your answers have been submitted and are pending grading"
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

import Foundation
import OSLog


enum MockNetworkError: Error, LocalizedError {
    case generalError
    var errorDescription: String? {
        "A mock network error occurred."
    }
}

// MARK: - Mock Network Service

class MockNetworkService: NetworkServicing {
    
    // MARK: - Properties
    
    var mockResponse: Decodable?
    var mockError: Error?
    var latency: TimeInterval = 0.5
    
    private let decoder: JSONDecoder
    
    // MARK: - Initialization
    
    init() {
        self.decoder = JSONDecoder()
        self.decoder.dateDecodingStrategy = .iso8601
        
        configureMockCourses()
    }
    
    // MARK: - NetworkServicing Protocol
    
    func request<T: Decodable>(
        endpoint: Endpoint,
        responseType: T.Type
    ) async throws -> T {
        // Log request
        NetworkLogger.log("[Mock] Request to \(endpoint.path)", level: .info)
        
        // Simulate network latency
        try await simulateNetworkDelay()
        
        // Check for mock error
        if let error = mockError {
            NetworkLogger.log("[Mock] Returning configured error", level: .error, error: error)
            throw error
        }
        
        // Return mock response
        guard let response = mockResponse as? T else {
            NetworkLogger.log("[Mock] No appropriate mock response configured for type \(T.self)", level: .error)
            throw MockNetworkError.generalError
        }
        
        NetworkLogger.log("[Mock] Successfully returning mock response", level: .success)
        return response
    }
    
    // MARK: - Configuration Methods
    
    /// Configure default mock courses
    private func configureMockCourses() {
        self.mockResponse = createMockCourses()
    }
    
    /// Configure mock to return quiz questions
    func configureMockQuiz(for courseId: String, questionNum: Int = 10) {
        NetworkLogger.log("[Mock] Configuring quiz with \(questionNum) questions for course: \(courseId)", level: .info)
        
        let questions = generateQuizQuestions(count: questionNum)
        
        self.mockResponse = QuizResponse(
            attemptId: UUID(),
            userId: UUID(),
            courseId: courseId,
            questionNum: questions.count,
            status: .inProgress,
            createdAt: Date(),
            questions: questions
        )
    }
    
    /// Configure mock to return submission response
    func configureMockSubmission() {
        NetworkLogger.log("[Mock] Configuring quiz submission response", level: .info)
        
        self.mockResponse = QuizSubmissionResponse(
            attemptId: UUID(),
            message: "Your answers have been submitted and are pending grading"
        )
    }
    
    /// Configure custom mock response
    func configureMockResponse<T: Decodable>(_ response: T) {
        NetworkLogger.log("[Mock] Configuring custom response of type \(T.self)", level: .info)
        self.mockResponse = response
    }
    
    /// Configure mock error
    func configureMockError(_ error: Error) {
        NetworkLogger.log("[Mock] Configuring mock error", level: .warning)
        self.mockError = error
    }
    
    /// Reset mock to default state
    func reset() {
        NetworkLogger.log("[Mock] Resetting to default configuration", level: .info)
        self.mockResponse = nil
        self.mockError = nil
        self.latency = 0.5
        configureMockCourses()
    }
    
    // MARK: - Private Helper Methods
    
    private func simulateNetworkDelay() async throws {
        try await Task.sleep(for: .seconds(latency))
    }
    
    private func createMockCourses() -> [FetchCourseResponse] {
        return [
            FetchCourseResponse(
                courseId: "swiftui-101",
                courseName: "SwiftUI 完全指南",
                courseDescription: "从入门到精通，构建漂亮的iOS应用。",
                isEnrolled: true,
                numOfKnowledgeNode: 35
            ),
            FetchCourseResponse(
                courseId: "swiftdata-201",
                courseName: "精通 SwiftData",
                courseDescription: "掌握现代化的数据持久化方案。",
                isEnrolled: false,
                numOfKnowledgeNode: 52
            ),
            FetchCourseResponse(
                courseId: "combine-301",
                courseName: "响应式编程与 Combine",
                courseDescription: "学习苹果官方的响应式编程框架。",
                isEnrolled: false,
                numOfKnowledgeNode: 48
            )
        ]
    }
    
    private func generateQuizQuestions(count: Int) -> [AnyQuestion] {
        let questionPool = createQuestionPool()
        var selectedQuestions: [AnyQuestion] = []
        
        for i in 0..<count {
            let questionIndex = i % questionPool.count
            let templateQuestion = questionPool[questionIndex]
            
            // Create new instance with unique ID
            let newQuestion = createQuestionInstance(from: templateQuestion, index: i)
            selectedQuestions.append(newQuestion)
        }
        
        return selectedQuestions
    }
    
    private func createQuestionInstance(from template: AnyQuestion, index: Int) -> AnyQuestion {
        switch template {
        case .multipleChoice(let mcq):
            return .multipleChoice(MultipleChoiceQuestion(
                id: UUID(),
                text: mcq.text,
                details: mcq.details
            ))
        default:
            // Fallback for any future question types
            return createFallbackQuestion()
        }
    }
    
    private func createFallbackQuestion() -> AnyQuestion {
        return .multipleChoice(MultipleChoiceQuestion(
            id: UUID(),
            text: "Fallback question: What is SwiftUI?",
            details: MultipleChoiceDetails(
                options: ["A framework", "A language", "A tool", "A platform"],
                correctAnswer: 0
            )
        ))
    }
    
    private func createQuestionPool() -> [AnyQuestion] {
        return [
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
    }
}

// MARK: - Mock Network Error Extension

extension MockNetworkError {
    static var responseTypeMismatch: MockNetworkError {
        .generalError
    }
    
    static var noMockConfigured: MockNetworkError {
        .generalError
    }
}

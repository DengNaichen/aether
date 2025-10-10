import Foundation
import Combine

@MainActor
class DashboardViewModel: ObservableObject {
    
    private let networkService: NetworkService

    // UI state parameters
    @Published var isEnrolling: Bool = false
    @Published var isStartingSession: Bool = false
    @Published var quizProblems: [QuizProblem] = []
    
    //
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var alertItem: AlertItem?
    
    init (network: NetworkService) {
        self.networkService = network
    }
    
    func handleError(_ error: Error, title: String) {
        let errorMessage: String
        if let networkError = error as? NetworkError {
            errorMessage = networkError.message
        } else {
            errorMessage = "An unknown error happen: \(error.localizedDescription)"
        }
        alertItem = AlertItem(title: "Enrollment Failed",
                              message: errorMessage)
    }
    
    func enrollInCourse(courseId: String) async {
        isEnrolling = true
        defer { isEnrolling = false }
        alertItem = nil
        enrollmentResponse = nil
        
        do {
            let endpoint = EnrollCourseEndpoint(courseId: courseId)
            let response: EnrollmentResponse = try await networkService.request(endpoint: endpoint, responseType: EnrollmentResponse.self)
            
            self.enrollmentResponse = response
        } catch {
            handleError(error, title: "Enrollment Failed")
        }
    }
    
//    func startSession(courseId: String, questionCount: Int) async throws -> SessionStartResponse {
//        isStartingSession = true
//        defer { isStartingSession = false }
//        alartItem = nil
//        
//        let requestData = SessionStartRequest(courseId: courseId)
//        let endpoint = SessionStartEndpoint(startSessionRequest: requestData)
//        let response: SessionStartResponse = try await networkService.request(
//            endpoint: endpoint,
//            responseType: SessionStartResponse.self
//        )
//        return response
//    }
    func startSession(courseId: String, questionCount: Int) async {
            isStartingSession = true
            alertItem = nil
            self.quizProblems = [] // 每次开始都清空旧数据
            defer { isStartingSession = false }

            do {
                // 1. 获取原始 API 数据
                let requestData = SessionStartRequest(courseId: courseId)
                let endpoint = SessionStartEndpoint(startSessionRequest: requestData)
                let response: SessionStartResponse = try await networkService.request(endpoint: endpoint, responseType: SessionStartResponse.self)
                
                // 2. 在内部直接进行数据转换
                let mappedProblems = self.mapToUIModels(from: response.questions)
                
                // 3. 更新发布的属性，这将通知 View 数据已准备好
                self.quizProblems = mappedProblems
                
            } catch {
                // 4. 在内部直接处理错误
                handleError(error, title: "Session Start Failed")
            }
        }
    private func mapToUIModels(from apiQuestions: [AnyQuestion]) -> [QuizProblem] {
            var uiProblems: [QuizProblem] = []
            for apiQuestion in apiQuestions {
                if case .multipleChoice(let mcq) = apiQuestion {
                    let problem = QuizProblem(
                        id: mcq.id,
                        text: mcq.text,
                        options: mcq.details.options,
                        correctAnswerIndex: mcq.details.correctAnswer
                    )
                    uiProblems.append(problem)
                }
            }
            return uiProblems
        }
}

import Foundation
import Combine

@MainActor
class DashboardViewModel: ObservableObject {
    
    private let networkService: NetworkServicing

    // UI state parameters
    @Published var isEnrolling: Bool = false
    @Published var isStartingSession: Bool = false
    @Published var quizProblemsForNavigation: [QuizProblem]? = nil
    
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var alertItem: AlertItem?
    
    init (network: NetworkServicing) {
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

    func startSession(courseId: String, questionCount: Int) async {
        isStartingSession = true
        alertItem = nil
        self.quizProblemsForNavigation = nil
        defer { isStartingSession = false }

        do {
            let requestData = SessionStartRequest(courseId: courseId)
            let endpoint = QuizEndpoint(startSessionRequest: requestData)
            let response: SessionStartResponse = try await networkService.request(endpoint: endpoint, responseType: SessionStartResponse.self)
                
            let mappedProblems = self.mapToUIModels(from: response.questions)
                
            self.quizProblemsForNavigation = mappedProblems
                
            } catch {
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

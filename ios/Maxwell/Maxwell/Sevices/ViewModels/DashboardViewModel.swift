import Foundation
import Combine

@MainActor
class DashboardViewModel: ObservableObject {
    
    private let networkService: NetworkService

    // UI state parameters
    @Published var isEnrolling: Bool = false
    @Published var isStartingSession: Bool = false
    
    //
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var alartItem: AlertItem?
    
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
        alartItem = AlertItem(title: "Enrollment Failed",
                              message: errorMessage)
    }
    
    func enrollInCourse(courseId: String) async {
        isEnrolling = true
        defer { isEnrolling = false }
        alartItem = nil
        enrollmentResponse = nil
        
        do {
            let endpoint = EnrollCourseEndpoint(courseId: courseId)
            let response: EnrollmentResponse = try await networkService.request(endpoint: endpoint, responseType: EnrollmentResponse.self)
            
            self.enrollmentResponse = response
        } catch {
            handleError(error, title: "Enrollment Failed")
        }
    }
    
    func startSession(courseId: String, questionCount: Int) async throws -> SessionStartResponse {
        isStartingSession = true
        defer { isStartingSession = false }
        alartItem = nil
        
        let requestData = SessionStartRequest(courseId: courseId)
        let endpoint = SessionStartEndpoint(startSessionRequest: requestData)
        let response: SessionStartResponse = try await networkService.request(
            endpoint: endpoint,
            responseType: SessionStartResponse.self
        )
        return response
    }
}

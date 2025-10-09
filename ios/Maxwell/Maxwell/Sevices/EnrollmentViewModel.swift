import Foundation
import Combine


@MainActor
class EnrollmentViewModel: ObservableObject {
    
    private let network: NetworkServicing
    
    @Published var isLoading: Bool = false
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var alartItem: AlertItem?
    
    
    
    init(network: NetworkServicing) {
        self.network = network
    }
    
    func enrollInCourse(courseId: String) async {
        isLoading = true
        defer { isLoading = false }
        alartItem = nil
        enrollmentResponse = nil
        
        do {
            let enrollmentEndpoint = EnrollCourseEndpoint(courseId: courseId)
            let response: EnrollmentResponse = try await network.request(endpoint: enrollmentEndpoint, responseType: EnrollmentResponse.self)
            
            self.enrollmentResponse = response
        } catch {
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "An unknown error happen: \(error.localizedDescription)"
            }
            alartItem = AlertItem(title: "Enrollment Failed",
                                  message: errorMessage)
        }
    }
}

import Foundation
import Combine


@MainActor
class EnrollmentViewModel: ObservableObject, NetworkViewModeling {
    
    private let network: NetworkServicing
    
    @Published var isLoading: Bool = false
    @Published var alertItem: AlertItem?
    
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    
    init(network: NetworkServicing) {
        self.network = network
    }
    
    func enrollInCourse(courseId: String) async {

        enrollmentResponse = nil
        
        let response = await performTask(errorTitle: "Enrollment Failed") {
            let endpoint = EnrollCourseEndpoint(courseId: courseId)
            return try await self.network.request(endpoint: endpoint, responseType: EnrollmentResponse.self)
        }
        if let response {
            self.enrollmentResponse = response
        }
    }
}

        
//        do {
//            let enrollmentEndpoint = EnrollCourseEndpoint(courseId: courseId)
//            let response: EnrollmentResponse = try await network.request(endpoint: enrollmentEndpoint, responseType: EnrollmentResponse.self)
//            
//            self.enrollmentResponse = response
//        } catch {
//            let errorMessage: String
//            if let networkError = error as? NetworkError {
//                errorMessage = networkError.message
//            } else {
//                errorMessage = "An unknown error happen: \(error.localizedDescription)"
//            }
//            alartItem = AlertItem(title: "Enrollment Failed",
//                                  message: errorMessage)
//        }


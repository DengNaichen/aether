import Foundation
import Combine

@MainActor
class DashboardViewModel: ObservableObject {
    
    private let networkService: NetworkServicing

    // UI state parameters
    @Published var isEnrolling: Bool = false
    @Published var isStartingSession: Bool = false
    
    @Published var enrollmentResponse: EnrollmentResponse? = nil
    @Published var alertItem: AlertItem?
    
    init (network: NetworkServicing) {
        self.networkService = network
    }
}

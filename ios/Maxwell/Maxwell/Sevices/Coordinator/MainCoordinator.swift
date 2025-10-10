import Foundation
import Combine
import SwiftUI

enum MainState {
    case dashboard
    case inQuiz(sessionData: SessionStartResponse)
    case inEnroll
}

@MainActor
class MainCoordinator: ObservableObject {
    
    var dashboardViewModel: DashboardViewModel

    private let networkService: NetworkService
    var onLogout: () -> Void
    
    init(networkService: NetworkService, onLogout: @escaping () -> Void) {
        self.networkService = networkService
        self.onLogout = onLogout
        // TODO: Do I need the onLogout here ??
        self.dashboardViewModel = DashboardViewModel(network: networkService)
    }
}

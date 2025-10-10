import SwiftUI

struct MainCoordinatorView: View {
    
    @StateObject var coordinator: MainCoordinator
    
    var body: some View {
        // For now, it directly shows the DashboardView.
        // In the future, this can be a switch statement based on the coordinator's state.
        DashboardView(viewModel: coordinator.dashboardViewModel)
    }
}

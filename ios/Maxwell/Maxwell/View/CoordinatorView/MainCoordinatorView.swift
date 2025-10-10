import SwiftUI

struct MainCoordinatorView: View {
    
    @StateObject var coordinator: MainCoordinator
    
    var body: some View {
        DashboardView(viewModel: coordinator.dashboardViewModel)
    }
}

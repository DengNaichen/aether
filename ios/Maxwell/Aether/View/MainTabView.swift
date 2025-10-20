import SwiftUI

struct MainTabView: View {
    var network: NetworkService
    var body: some View {
        TabView {
            DashboardView(viewModel: DashboardViewModel(network: network))
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }
            
            CoursesListView()
                .tabItem {
                    Label("Course", systemImage: "graduationcap.fill")
                }
        }
    }
}

#Preview {
    MainTabView(network: MockNetworkService())
}

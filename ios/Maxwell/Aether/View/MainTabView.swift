import SwiftUI

struct MainTabView: View {
    var network: NetworkService
    var body: some View {
        TabView {
             HomeView(viewModel: DashboardViewModel(network: network))
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }
            
            CoursesListView(viewModel: CourseViewModel(network: network))
                .tabItem {
                    Label("Course", systemImage: "graduationcap.fill")
                }
        }
    }
}

#Preview {
    MainTabView(network: MockNetworkService())
}

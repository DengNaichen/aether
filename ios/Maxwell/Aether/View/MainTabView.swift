import SwiftUI

struct MainTabView: View {
    @Environment(\.modelContext) private var modelContext
    var network: NetworkServicing
    var body: some View {
        TabView {
             HomeView(viewModel: DashboardViewModel(network: network))
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }
            
            CoursesListView(viewModel: CourseViewModel(
                network: network,
                modelContext: modelContext
            ))
                .tabItem {
                    Label("Course", systemImage: "graduationcap.fill")
                }
        }
    }
}

//#Preview {
//    MainTabView(network: MockNetworkService())
//}

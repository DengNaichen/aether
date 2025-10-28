import SwiftUI

struct MainTabView: View {
    @Environment(\.modelContext) private var modelContext
    var network: NetworkServicing
    var body: some View {
        TabView {
             HomeView(network: network, modelContext: modelContext)
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

//#if DEBUG
//import SwiftData
//
//@MainActor
//struct MainTabView_Previews: PreviewProvider {
//    
//    static func createMockDataAndContainer() -> (NetworkServicing, ModelContainer) {
//        // 创建Mock网络服务
//        let mockNetwork = MockNetworkService()
//        
//        // 配置Mock数据 - 包含一些已注册和未注册的课程
//        mockNetwork.mockResponse = FetchAllCoursesResponse(courses: [
//            FetchCourseResponse(
//                courseId: "swift-fundamentals",
//                courseName: "Swift Fundamentals",
//                courseDescription: "Learn the basics of Swift programming language",
//                isEnrolled: true,
//                numOfKnowledgeNode: 30
//            ),
//            FetchCourseResponse(
//                courseId: "ios-development",
//                courseName: "iOS App Development",
//                courseDescription: "Build your first iOS applications",
//                isEnrolled: true,
//                numOfKnowledgeNode: 45
//            ),
//            FetchCourseResponse(
//                courseId: "swiftui-basics",
//                courseName: "SwiftUI Basics",
//                courseDescription: "Create beautiful user interfaces with SwiftUI",
//                isEnrolled: false,
//                numOfKnowledgeNode: 35
//            ),
//            FetchCourseResponse(
//                courseId: "advanced-swift",
//                courseName: "Advanced Swift Concepts",
//                courseDescription: "Master advanced Swift programming techniques",
//                isEnrolled: false,
//                numOfKnowledgeNode: 50
//            ),
//            FetchCourseResponse(
//                courseId: "core-data",
//                courseName: "Core Data Mastery",
//                courseDescription: "Learn data persistence with Core Data",
//                isEnrolled: true,
//                numOfKnowledgeNode: 25
//            )
//        ])
//        
//        // 创建内存中的数据容器
//        let container = try! ModelContainer(
//            for: CourseModel.self, QuizAttempt.self, StoredQuestion.self,
//            configurations: .init(isStoredInMemoryOnly: true)
//        )
//        
//        return (mockNetwork, container)
//    }
//    
//    static var previews: some View {
//        let (mockNetwork, container) = createMockDataAndContainer()
//        
//        // 主要的TabView预览
//        MainTabView(network: mockNetwork)
//            .modelContainer(container)
//            .previewDisplayName("Main Tab View")
//        
//        // iPhone SE预览 - 测试小屏幕
//        MainTabView(network: mockNetwork)
//            .modelContainer(container)
//            .previewDevice(PreviewDevice(rawValue: "iPhone SE (3rd generation)"))
//            .previewDisplayName("iPhone SE")
//        
//        // iPad预览 - 测试大屏幕
//        MainTabView(network: mockNetwork)
//            .modelContainer(container)
//            .previewDevice(PreviewDevice(rawValue: "iPad Pro (11-inch) (4th generation)"))
//            .previewDisplayName("iPad Pro")
//        
//        // 深色模式预览
//        MainTabView(network: mockNetwork)
//            .modelContainer(container)
//            .preferredColorScheme(.dark)
//            .previewDisplayName("Dark Mode")
//    }
//}
//#endif

import SwiftUI

struct CourseRowView: View {
    let course: Course
    
    var body: some View {
        HStack(spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                
                Text(course.courseName)
                    .font(.headline)
                    .fontWeight(.bold)
                
                Text("\(course.numOfKnowledgeNodes) nodes")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
            }
            Spacer()
        }
        .padding(.vertical, 8)
    }
}

struct CourseDetailView: View {
    let course: Course
    @ObservedObject var viewModel: CourseViewModel
    
    
    var body: some View {
        Button("Enroll in \(course.courseName)") {
            Task {
                await viewModel.enrollInCourse(courseId: course.courseId)
            }
        }
    }
}


struct CoursesListView: View {
    
    @StateObject private var viewModel: CourseViewModel
    
    init(viewModel: CourseViewModel) {
        self._viewModel = StateObject(wrappedValue: viewModel)
    }
    
    var body: some View {
        NavigationView{
            List(viewModel.courses) { course in
                NavigationLink(
                    destination: CourseDetailView(
                        course: course,
                        viewModel: viewModel
                    )
                ) {
                    CourseRowView(course: course)
                }
            }
            .listStyle(.plain)
            .navigationTitle(Text("Courses"))
            .onAppear {
                Task {
                    // TODO: if this fail, we need a new error handler
                    await viewModel.fetchAllCourses()
                }
            }
        }
    }
}


//#if DEBUG
//import SwiftUI
//import SwiftData
//
//@MainActor
//struct CoursesListView_Previews: PreviewProvider {
//
//    // MARK: - Helper for creating ViewModel
//    
//    /// 一个辅助方法，用于创建配置好的 ViewModel 和 Container
//    static func createViewModel(for scenario: Scenario) -> (CourseViewModel, ModelContainer) {
//        // 1. 为预览创建一个临时的、只在内存中的数据库容器
//        let inMemoryContainer = try! ModelContainer(for: CourseModel.self, configurations: .init(isStoredInMemoryOnly: true))
//        
//        // 2. 创建 Mock 网络服务
//        let mockNetwork = MockNetworkService()
//        
//        // 3. 根据不同场景配置 Mock 服务
//        switch scenario {
//        case .loading:
//            // 为了静态预览加载状态，我们可以直接创建一个 isLoading=true 的 ViewModel
//            // 或者像下面这样设置一个超长的延迟，让加载动画持续显示
//             mockNetwork.latency = 1000
//        case .success:
//            // MockNetworkService 默认返回成功数据，无需额外配置
//            break
//        case .empty:
//            // 返回一个空的课程列表
//            mockNetwork.mockResponse = FetchAllCoursesResponse(courses: [])
//        case .failure:
//            // 模拟一个网络错误
//            mockNetwork.mockError = MockNetworkError.generalError
//        }
//        
//        let viewModel = CourseViewModel(
//            network: mockNetwork,
//            modelContext: inMemoryContainer.mainContext
//        )
//        
//        return (viewModel, inMemoryContainer)
//    }
//    
//    enum Scenario {
//        case loading, success, empty, failure
//    }
//
//    // MARK: - Previews
//    
//    static var previews: some View {
//        // --- 成功场景 ---
//        let (successVM, successContainer) = createViewModel(for: .success)
//        CoursesListView(viewModel: successVM)
//            .modelContainer(successContainer)
//            .previewDisplayName("Success State")
//        
//        // --- 加载中场景 ---
//        let (loadingVM, loadingContainer) = createViewModel(for: .loading)
//        // 手动设置 isLoading=true 可以更稳定地预览加载UI
//        let _ = loadingVM.isLoading = true
//        CoursesListView(viewModel: loadingVM)
//            .modelContainer(loadingContainer)
//            .previewDisplayName("Loading State")
//        
//        // --- 列表为空场景 ---
//        let (emptyVM, emptyContainer) = createViewModel(for: .empty)
//        CoursesListView(viewModel: emptyVM)
//            .modelContainer(emptyContainer)
//            .previewDisplayName("Empty State")
//
//        // --- 失败场景 ---
//        let (failureVM, failureContainer) = createViewModel(for: .failure)
//        CoursesListView(viewModel: failureVM)
//            .modelContainer(failureContainer)
//            .previewDisplayName("Failure State")
//    }
//}
//#endif

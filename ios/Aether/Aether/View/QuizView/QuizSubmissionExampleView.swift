import SwiftUI
import SwiftData

/// 展示如何在实际应用中使用Quiz Submission功能的示例视图
//struct QuizSubmissionExampleView: View {
//    @StateObject private var viewModel = QuizViewModel(
//        network: NetworkService(
//            baseURL: URL(string: "https://your-api-domain.com")!,
//            authService: AuthService()
//        ),
//        modelContext: ModelContext() // 需要从实际的ModelContainer获取
//    )
//    
//    @State private var selectedCourse = "swiftui-101"
//    @State private var questionCount = 10
//    
//    var body: some View {
//        NavigationView {
//            VStack(spacing: 20) {
//                Text("测验提交功能演示")
//                    .font(.largeTitle)
//                    .fontWeight(.bold)
//                
//                // 测验配置
//                Group {
//                    HStack {
//                        Text("课程ID:")
//                        TextField("Course ID", text: $selectedCourse)
//                            .textFieldStyle(RoundedBorderTextFieldStyle())
//                    }
//                    
//                    HStack {
//                        Text("题目数量:")
//                        Stepper("\(questionCount)", value: $questionCount, in: 5...20)
//                    }
//                }
//                
//                // 开始测验按钮
//                Button("开始测验") {
//                    Task {
//                        await viewModel.startQuiz(courseId: selectedCourse, questionNum: questionCount)
//                    }
//                }
//                .buttonStyle(.borderedProminent)
//                .disabled(viewModel.isLoading)
//                
//                Spacer()
//                
//                // 测验状态信息
//                if let attempt = viewModel.activeAttempt {
//                    VStack(alignment: .leading, spacing: 10) {
//                        Text("当前测验状态")
//                            .font(.headline)
//                        
//                        Text("状态: \(attempt.status.rawValue)")
//                        Text("分数: \(viewModel.score) / \(viewModel.questions.count)")
//                        Text("当前题目: \(viewModel.currentQuestionIndex + 1) / \(viewModel.questions.count)")
//                        
//                        if attempt.status == .completed {
//                            Button("提交答案到服务器") {
//                                Task {
//                                    await viewModel.submitQuiz()
//                                }
//                            }
//                            .buttonStyle(.borderedProminent)
//                            .disabled(viewModel.isLoading)
//                        }
//                    }
//                    .padding()
//                    .background(Color.gray.opacity(0.1))
//                    .cornerRadius(10)
//                }
//                
//                Spacer()
//            }
//            .padding()
//            .navigationTitle("Quiz Demo")
//            .overlay(
//                // 加载指示器
//                Group {
//                    if viewModel.isLoading {
//                        Color.black.opacity(0.3)
//                        ProgressView("处理中...")
//                            .padding()
//                            .background(Color.white)
//                            .cornerRadius(10)
//                    }
//                }
//            )
//        }
//        .alert(item: $viewModel.alertItem) { alertItem in
//            Alert(
//                title: Text(alertItem.title),
//                message: Text(alertItem.message),
//                dismissButton: .default(Text("确定"))
//            )
//        }
//    }
//}
//
//// MARK: - 模拟数据和网络服务的设置示例
//extension QuizSubmissionExampleView {
//    
//    /// 创建用于演示的Mock网络服务
//    static func createMockViewModel() -> QuizViewModel {
//        let mockNetwork = MockNetworkService()
//        
//        // 配置模拟测验数据
//        mockNetwork.configureMockQuiz(for: "demo-course", questionNum: 5)
//        
//        // 创建内存模型容器
//        let container = try! ModelContainer(
//            for: QuizAttempt.self, StoredQuestion.self,
//            configurations: .init(isStoredInMemoryOnly: true)
//        )
//        
//        return QuizViewModel(network: mockNetwork, modelContext: container.mainContext)
//    }
//}
//
//// MARK: - 预览
//#if DEBUG
//struct QuizSubmissionExampleView_Previews: PreviewProvider {
//    static var previews: some View {
//        Group {
//            // 常规预览
//            QuizSubmissionExampleView()
//                .previewDisplayName("Quiz Submission Demo")
//            
//            // 使用Mock数据的预览
//            QuizSubmissionExampleView()
//                .environmentObject(QuizSubmissionExampleView.createMockViewModel())
//                .previewDisplayName("With Mock Data")
//        }
//    }
//}
//#endif

// MARK: - 使用示例和最佳实践

/*
 使用这个Quiz Submission功能的最佳实践：
 
 1. 初始化ViewModels：
    ```swift
    let viewModel = QuizViewModel(
        network: yourNetworkService,
        modelContext: yourModelContext
    )
    ```
 
 2. 开始测验：
    ```swift
    await viewModel.startQuiz(courseId: "course-id", questionNum: 10)
    ```
 
 3. 提交答案：
    ```swift
    await viewModel.submitQuiz()
    ```
 
 4. 错误处理：
    - 监听 viewModel.alertItem 来显示错误
    - 检查 viewModel.isLoading 来显示加载状态
 
 5. 状态管理：
    - activeAttempt: 当前测验尝试
    - questions: 题目列表
    - score: 当前分数
    - currentQuestionIndex: 当前题目索引
 
 6. 测试：
    - 使用MockNetworkService进行单元测试
    - 配置不同的mock响应来测试各种场景
 
 7. 网络配置：
    - 确保设置正确的baseURL
    - 配置适当的认证服务
    - 处理网络超时和重试逻辑
*/

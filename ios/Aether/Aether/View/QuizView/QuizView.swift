import SwiftUI
import SwiftData

struct QuizView: View {
    
    @StateObject var viewModel: QuizViewModel
    private let network: NetworkServicing
    private let courseId: String
    
    /// 新的 init：
    /// 它需要 courseId 和 modelContext
    /// 它为你创建了正确的 ViewModel
    init(courseId: String,
         network: NetworkServicing,
         modelContext: ModelContext) {
        self.courseId = courseId
        self.network = network
        
        // 假设你有一个 NetworkService() 实例
        // 如果 NetworkService 在你的环境中，你可以从那里获取
        
        _viewModel = StateObject(wrappedValue: QuizViewModel(
            network: network,
            modelContext: modelContext
        ))
    }
    
    var body: some View {
        VStack(spacing: 20) {
            
            // 1. 优先显示加载状态
            if viewModel.isLoading {
                Text("Loading Quiz ...")
                ProgressView()
            }
            
            // 2. 检查测验是否结束
            // (得益于我们添加的 'isQuizFinished' 属性)
            else if viewModel.isQuizFinished {
                QuizCompletionView(viewModel: viewModel)
            }
            
            // 3. 检查是否成功加载了当前问题
            // (得益于我们添加的 'currentQuestion' 属性)
            else if let question = viewModel.currentQuestion {
                
                // MARK: - Question Text
                Text(question.text)
                    .font(.title2)
                    .fontWeight(.bold)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                
                Spacer()
                
                // MARK: - Option Button
                // 你的 OptionButtonView 会从 viewModel 中
                // 读取 question.details, question.isSubmitted,
                // 和 viewModel.selectedOptionIndex
                OptionButtonView(viewModel: viewModel)
                    .padding(.horizontal)
                
                Spacer()
                
                // MARK: - Submission Button
                // 你的 SubmissionButtonView 会调用
                // viewModel.submitAnswer() 或 viewModel.advanceToNextQuestion()
                SubmissionButtonView(viewModel: viewModel)
                    .padding()
                
            }
            
            // 4. 加载失败或无数据时的状态
            else {
                // 如果没有加载，没完成，也没问题，
                // 这通常意味着网络请求失败了 (Alert 会显示)
                Text("Could not load quiz.")
                    .font(.headline)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .navigationTitle("🙄")
        // 5. 使用 .task 在 View 出现时启动测验
        .task {
            // 只有在还没有 activeAttempt 时才加载
            // (防止在 sheet/navigation 中返回时重复加载)
            if viewModel.activeAttempt == nil {
                // 你可以按需修改 questionNum
                await viewModel.startQuiz(courseId: self.courseId, questionNum: 10)
            }
        }
        // 6. 显示 viewModel 发出的任何警报
        .alert(item: $viewModel.alertItem) { alertItem in
            Alert(
                title: Text(alertItem.title),
                message: Text(alertItem.message),
                dismissButton: .default(Text("OK"))
            )
        }
    }
}

#if DEBUG
import SwiftData

@MainActor
struct QuizView_Previews: PreviewProvider {
    
    // MARK: - Helper for creating ViewModel
    
    /// 一个辅助方法，用于创建配置好的 ViewModel 和 Container
    static func createViewModel(for scenario: Scenario, courseId: String = "swiftui-101") -> (QuizViewModel, ModelContainer, MockNetworkService) {
        // 1. 为预览创建一个临时的、只在内存中的数据库容器
        let inMemoryContainer = try! ModelContainer(
            for: QuizAttempt.self, StoredQuestion.self,
            configurations: .init(isStoredInMemoryOnly: true)
        )
        
        // 2. 创建 Mock 网络服务
        let mockNetwork = MockNetworkService()
        
        // 3. 根据不同场景配置 Mock 服务
        switch scenario {
        case .loading:
            // 为了静态预览加载状态，设置长延迟
            mockNetwork.latency = 1000
            mockNetwork.configureMockQuiz(for: courseId, questionNum: 5)
        case .success:
            // 配置成功的测验数据，确保足够的问题数量
            mockNetwork.latency = 0.1 // 减少延迟以便预览
            mockNetwork.configureMockQuiz(for: courseId, questionNum: 10)
        case .empty:
            // 返回一个空的测验（理论上不应该发生，但可以测试错误处理）
            mockNetwork.mockResponse = QuizResponse(
                attemptId: UUID(),
                userId: UUID(),
                courseId: courseId,
                questionNum: 0,
                status: .inProgress,
                createdAt: Date(),
                questions: []
            )
        case .failure:
            // 模拟一个网络错误
            mockNetwork.mockError = MockNetworkError.generalError
        }
        
        let viewModel = QuizViewModel(
            network: mockNetwork,
            modelContext: inMemoryContainer.mainContext
        )
        
        return (viewModel, inMemoryContainer, mockNetwork)
    }
    
    enum Scenario {
        case loading, success, empty, failure
    }
    
    // MARK: - Previews
    
    static var previews: some View {
        // --- 成功场景 ---
        let (successVM, successContainer, successMockNetwork) = createViewModel(for: .success)
        QuizView(
            courseId: "swiftui-101",
            network: successMockNetwork,
            modelContext: successContainer.mainContext
        )
        .modelContainer(successContainer)
        .previewDisplayName("Success State")
        
        // --- 加载中场景 ---
        let (loadingVM, loadingContainer, loadingMockNetwork) = createViewModel(for: .loading)
        // 手动设置 isLoading=true 可以更稳定地预览加载UI
        let _ = loadingVM.isLoading = true
        QuizView(
            courseId: "swiftui-101",
            network: loadingMockNetwork,
            modelContext: loadingContainer.mainContext
        )
        .modelContainer(loadingContainer)
        .previewDisplayName("Loading State")
        
        // --- 失败场景 ---
        let (failureVM, failureContainer, failureMockNetwork) = createViewModel(for: .failure)
        QuizView(
            courseId: "swiftui-101",
            network: failureMockNetwork,
            modelContext: failureContainer.mainContext
        )
        .modelContainer(failureContainer)
        .previewDisplayName("Failure State")
        
        // --- 预配置有问题的测验场景 ---
        Group {
            let (preConfiguredVM, preConfiguredContainer, mockNetwork) = createViewModel(for: .success)
            
            QuizView(
                courseId: "swiftui-101",
                network: mockNetwork,
                modelContext: preConfiguredContainer.mainContext
            )
            .modelContainer(preConfiguredContainer)
            .previewDisplayName("Quiz In Progress")
        }
    }
}
#endif

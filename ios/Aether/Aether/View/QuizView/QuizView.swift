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

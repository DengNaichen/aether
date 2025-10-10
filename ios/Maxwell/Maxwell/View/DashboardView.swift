import SwiftUI

struct DashboardView: View {

    // 💡 提示: 当一个 View 创建或持有其 ViewModel 的生命周期时，
    // 使用 @StateObject 更安全，可以防止因 View 重绘而导致 ViewModel 被意外销毁。
    @StateObject private var viewModel: DashboardViewModel
    
    // 用于触发导航的状态
    @State private var navigateToQuiz = false

    init(viewModel: DashboardViewModel) {
        // 使用 _viewModel 来初始化 @StateObject
        self._viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                Text("😅😒🤯")
                    .font(.largeTitle)
              
                // ... (Enroll Button 保持不变)
                Button("Enroll in Default Course(G11 Physics)") {
                                Task{
                                    await viewModel.enrollInCourse(courseId: "g11_phys")
                                }
                            }
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(10)
              
                // ✨ 简化后的 Button
                Button("Start Test Session (G11 Physics)") {
                    Task {
                        // 只需要调用方法，不需要返回值，也不需要 try-catch
                        await viewModel.startSession(courseId: "g11_phys", questionCount: 2)
                    }
                }
                .padding()
                .background(Color.purple)
                .foregroundColor(.white)
                .cornerRadius(10)
              
                // ✨ 简化后的状态显示区域
                VStack {
                    if viewModel.isEnrolling || viewModel.isStartingSession {
                        ProgressView(viewModel.isEnrolling ? "Enrolling..." : "Starting Session...")
                    }
                    
                    if let response = viewModel.enrollmentResponse {
                        Text("✅ Success! Enrolled with ID: \(response.id.uuidString)")
                            .foregroundColor(.green)
                            .padding()
                    }
                }
                .frame(height: 100)
            }
            .padding()
            .navigationTitle("Welcome")
            // ✨ 新增: 响应式导航逻辑
            .onChange(of: viewModel.quizProblems) { newProblems in
                // 当 ViewModel 准备好数据后，我们在这里更新导航状态
                if !newProblems.isEmpty {
                    self.navigateToQuiz = true
                }
            }
            .navigationDestination(isPresented: $navigateToQuiz) {
                // 当导航被触发时，创建下一个页面和它的 ViewModel
                if !viewModel.quizProblems.isEmpty {
                    let quizViewModel = QuizViewModel(problems: viewModel.quizProblems)
                    QuizView(viewModel: quizViewModel)
                }
            }
            // ✨ 新增: 显示来自 ViewModel 的弹窗
            .alert(item: $viewModel.alertItem) { alertItem in
                Alert(title: Text(alertItem.title), message: Text(alertItem.message), dismissButton: .default(Text("OK")))
            }
        }
    }
}

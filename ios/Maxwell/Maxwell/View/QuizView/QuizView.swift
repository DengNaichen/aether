import SwiftUI

struct QuizView: View {
    // 接收我们从 DashboardView 创建并传递过来的 ViewModel
    @StateObject var viewModel: QuizViewModel
    
    var body: some View {
        // 使用 List 可以很方便地展示列表数据，并且自带滚动
        List {
            // Section 1: 一个简单的标题，确认我们成功跳转了
            Section(header: Text("调试信息").font(.headline)) {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text("成功导航到 QuizView!")
                }
                Text("收到了 \(viewModel.problems.count) 个问题。")
            }
            
            // Section 2: 循环展示所有接收到的问题数据
            Section(header: Text("问题内容").font(.headline)) {
                // 遍历 ViewModel 中的 problems 数组
                ForEach(viewModel.problems) { problem in
                    // 为每个问题创建一个垂直堆栈来显示其内容
                    VStack(alignment: .leading, spacing: 10) {
                        
                        // 1. 显示问题文本
                        Text("Q: \(problem.text)")
                            .fontWeight(.bold)
                            .padding(.bottom, 5)
                        
                        // 2. 遍历并显示所有选项
                        ForEach(Array(problem.options.enumerated()), id: \.offset) { index, optionText in
                            HStack {
                                // 检查这个选项是不是正确答案，如果是，就加一个对勾图标
                                if index == problem.correctAnswerIndex {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundColor(.green)
                                } else {
                                    Image(systemName: "circle")
                                        .foregroundColor(.gray)
                                }
                                Text(optionText)
                            }
                        }
                        
                        // 3. 显示问题的 UUID 作为额外调试信息
                        Text("ID: \(problem.id.uuidString)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .padding(.top, 5)
                    }
                    .padding(.vertical, 10) // 给每个问题上下增加一些间距
                }
            }
        }
        .navigationTitle("流程测试页面") // 清晰的导航栏标题
        .navigationBarTitleDisplayMode(.inline)
    }
}

// Multiple Choice View
//struct QuizView: View {
//    
////    @StateObject private var viewModel = QuizViewModel()
//    
//    var body: some View {
//        Text("This is the Quiz View")
//        VStack(spacing: 20) {
//            // check if the quiz is over
//            if viewModel.isQuizFinished {
//                QuizCompletionView(viewModel: viewModel)
//            }
//            // if the quiz is not over
//            else {
//                if let question = viewModel.currentQuestion {
//                    // safely unwrap the current question
//                    // MARK: - Question Text
////                    QuestionTextView(viewModel: questionViewModel)
//                    Text(question.text)
//                        .font(.title2)
//                        .fontWeight(.bold)
//                        .multilineTextAlignment(.center)
//                        .padding(.horizontal)
//                    
//                    Spacer()
//                    // MARK: - Option Button
//                    OptionButtonView(viewModel: viewModel)
//                        .padding(.horizontal)
//                    Spacer()
//                    // MARK: - Submission Button
//                    SubmissionButtonView(viewModel: viewModel)
//                        .padding()
//                } else {
//                    // show a loading view or message if questions aren't loaded yet
//                    Text("Loading Quiz ...")
//                    ProgressView()
//                }
//            }
//        }
//        .padding()
//        .navigationTitle("🙄")
//    }
//}
//
//
//// MARK: - Preview
//struct MultipleChoiceQuestionView_Previews: PreviewProvider {
//    static var previews: some View {
//        QuizView()
//    }
//}

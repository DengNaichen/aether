import SwiftUI

//struct QuizView: View {
//    
//    @StateObject var viewModel: QuizViewModel
//    
//    init(problems: [QuizProblem]) {
//        _viewModel = StateObject(wrappedValue: QuizViewModel(problems: problems))
//    }
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

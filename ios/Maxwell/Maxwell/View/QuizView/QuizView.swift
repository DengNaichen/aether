import SwiftUI

// Multiple Choice View
struct QuizView: View {
    
    @StateObject private var viewModel = QuizViewModel()
    
    var body: some View {
        VStack(spacing: 20) {
            // check if the quiz is over
            if viewModel.isQuizFinished {
                QuizCompletionView(viewModel: viewModel)
            }
            // if the quiz is not over
            else {
                if let question = viewModel.currentQuestion {
                    // safely unwrap the current question
                    // MARK: - Question Text
//                    QuestionTextView(viewModel: questionViewModel)
                    Text(question.text)
                        .font(.title2)
                        .fontWeight(.bold)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                    
                    Spacer()
                    // MARK: - Option Button
                    OptionButtonView(viewModel: viewModel)
                        .padding(.horizontal)
                    Spacer()
                    // MARK: - Submission Button
                    SubmissionButtonView(viewModel: viewModel)
                        .padding()
                } else {
                    // show a loading view or message if questions aren't loaded yet
                    Text("Loading Quiz ...")
                    ProgressView()
                }
            }
        }
        .padding()
        .navigationTitle("🙄")
    }
}


// MARK: - Preview
struct MultipleChoiceQuestionView_Previews: PreviewProvider {
    static var previews: some View {
        QuizView()
    }
}

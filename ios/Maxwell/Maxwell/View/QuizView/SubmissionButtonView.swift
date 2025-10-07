import SwiftUI

struct SubmissionButtonView: View {
    let notAbleSubmissionColor: Color = Color.gray
    let AbleSubmissionColor: Color = Color.blue
    
    @ObservedObject var viewModel: QuizViewModel
    
    var body: some View {
        Button(action: {
            if viewModel.isAnswerSubmitted {
                viewModel.nextQuestion()
            } else {
                viewModel.submitAnswer()
            }
        }) {
            Text(viewModel.isAnswerSubmitted ? "Next" : "Submit")
                .font(.headline)
                .fontWeight(.bold)
                .padding()
                .frame(maxWidth: .infinity)
                .background(viewModel.selectedOptionIndex == nil ? notAbleSubmissionColor : AbleSubmissionColor)
                .foregroundColor(Color.white)
                .cornerRadius(10)
        }
        .disabled(viewModel.selectedOptionIndex == nil)
    }
}

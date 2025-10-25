import SwiftUI

struct SubmissionButtonView: View {
    let notAbleSubmissionColor: Color = Color.gray
    let AbleSubmissionColor: Color = Color.blue
    let nextButtonColor: Color = Color.green // Added a color for the "Next" state
    
    @ObservedObject var viewModel: QuizViewModel
    
    /// Helper to check if the current question is an MCQ
    private var isCurrentTypeSupported: Bool {
        guard let question = viewModel.currentQuestion else { return false }
        if case .multipleChoice = question.details {
            return true
        }
        return false // Other types are not supported
    }
    
    var body: some View {
        Button(action: {
            if isCurrentTypeSupported {
                // It's an MCQ, do the normal logic
                if viewModel.isAnswerSubmitted {
                    viewModel.advanceToNextQuestion() // <-- Fixed function name
                } else {
                    viewModel.submitAnswer()
                }
            } else {
                // It's a placeholder, just "Skip"
                viewModel.advanceToNextQuestion() // <-- The action is to skip
            }
        }) {
            // Text changes based on state
            Text(buttonText())
                .font(.headline)
                .fontWeight(.bold)
                .padding()
                .frame(maxWidth: .infinity)
                .background(buttonBackgroundColor()) // <-- Updated logic
                .foregroundColor(Color.white)
                .cornerRadius(10)
        }
        .disabled(isButtonDisabled()) // <-- Updated logic
    }
    
    // MARK: - Helper Functions
    
    /// Determines the correct text for the button
    private func buttonText() -> String {
        if !isCurrentTypeSupported {
            return "Skip" // <-- Show "Skip" for placeholders
        }
        return viewModel.isAnswerSubmitted ? "Next" : "Submit"
    }
    
    /// Determines if the button should be disabled
    private func isButtonDisabled() -> Bool {
        if !isCurrentTypeSupported {
            return false // "Skip" button is never disabled
        }
        
        if viewModel.isAnswerSubmitted {
            return false // "Next" button is never disabled
        }
        
        // "Submit" button is disabled if no option is selected
        return viewModel.selectedOptionIndex == nil
    }
    
    /// Determines the correct background color
    private func buttonBackgroundColor() -> Color {
        if !isCurrentTypeSupported {
            return notAbleSubmissionColor // "Skip" is gray
        }
        
        if viewModel.isAnswerSubmitted {
            return nextButtonColor // "Next" is green
        }
        
        // "Submit" button uses your original logic
        return viewModel.selectedOptionIndex == nil ? notAbleSubmissionColor : AbleSubmissionColor
    }
}

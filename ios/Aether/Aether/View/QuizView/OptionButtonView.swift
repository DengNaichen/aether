import SwiftUI

struct OptionButtonView: View {
    
    // @StateObject creates and owns the ViewModel instance.
    // Use @ObservedObject if the ViewModel is passed in from a parent view.
    @ObservedObject var viewModel: QuizViewModel
    
    var body: some View {
        // must safely unwrap the current question
        if let question = viewModel.currentQuestion {
            
            switch question.details {
            case .multipleChoice(let details):
                VStack(spacing: 15) {
                    ForEach(0..<details.options.count, id: \.self) { index in
                        Button(action: {
                            // Action is now simpler: just select the option.
                            // The view doesn't care about the logic.
                            if !viewModel.isAnswerSubmitted {
                                viewModel.selectedOptionIndex = index
                            }
                        }) {
                            HStack {
                                Text(details.options[index])
                                Spacer()
                                // logic to show checkmark / xmark or selection circle
                                if viewModel.isAnswerSubmitted {
                                    if index == details.correctAnswer {
                                        Image(systemName: "checkmark.circle.fill")
                                            .foregroundColor(.green)
                                    } else if index == viewModel.selectedOptionIndex {
                                        Image(systemName: "xmark.circle.fill")
                                            .foregroundColor(.red)
                                    }
                                } else {
                                    Image(systemName: viewModel.selectedOptionIndex == index ? "largecircle.fill.circle" : "circle")
                                }
                            }
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(backgroundColor(for: index))
                            .cornerRadius(10)
                            .overlay(
                                RoundedRectangle(cornerRadius: 10)
                                    .stroke(borderColor(for: index), lineWidth: 2)
                            )
                            .foregroundColor(.primary)
                        }
                        .disabled(viewModel.isAnswerSubmitted)
                    }
                }
            case .fillInTheBlank, .calculation:
                VStack {
                    Text("Unsupported Question Type")
                        .font(.headline)
                        .foregroundColor(.gray)
                    
                    Text("This view is not build yet.")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                .padding()
                .frame(maxWidth: .infinity, minHeight: 150) // Give it some space
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)
                
            }
        }
    }
    
    private func backgroundColor(for index: Int) -> Color {
        guard let question = viewModel.currentQuestion else { return .clear }
        
        switch question.details {
        case .multipleChoice(let details):
            if viewModel.isAnswerSubmitted {
                if index == details.correctAnswer { return .green.opacity(0.1) }
                if index == viewModel.selectedOptionIndex { return .red.opacity(0.1) }
            } else if viewModel.selectedOptionIndex == index {
                return .blue.opacity(0.1)
            }
            return .clear
        
        default:
            return .clear
        }
    }
    
    
    private func borderColor(for index: Int) -> Color {
        guard let question = viewModel.currentQuestion else { return .gray.opacity(0.3) }
        
        switch question.details {
        case.multipleChoice(let details):
            if viewModel.isAnswerSubmitted {
                if index == details.correctAnswer { return .green }
                if index == viewModel.selectedOptionIndex { return .red }
            } else if viewModel.selectedOptionIndex == index {
                return .blue
            }
            return .gray.opacity(0.3)
            
        default:
            return .gray.opacity(0.3)
        }
    }
}

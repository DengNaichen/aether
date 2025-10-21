import SwiftUI

struct OptionButtonView: View {
    
    // @StateObject creates and owns the ViewModel instance.
    // Use @ObservedObject if the ViewModel is passed in from a parent view.
    @ObservedObject var viewModel: QuizViewModel
    
    var body: some View {
        // must safely unwrap the current question
        if let question = viewModel.currentQuestion {
            VStack(spacing: 15) {
                ForEach(0..<question.options.count, id: \.self) { index in
                    Button(action: {
                        // Action is now simpler: just select the option.
                        // The view doesn't care about the logic.
                        if !viewModel.isAnswerSubmitted {
                            viewModel.selectedOptionIndex = index
                        }
                    }) {
                        HStack {
                            Text(question.options[index])
                            Spacer()
                            // logic to show checkmark / xmark or selection circle
                            if viewModel.isAnswerSubmitted {
                                if index == question.correctAnswerIndex {
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
                }
            }
        }
    }
    
    private func backgroundColor(for index: Int) -> Color {
        guard let question = viewModel.currentQuestion else {return .clear}
        
        if viewModel.isAnswerSubmitted {
            if index == question.correctAnswerIndex { return .green.opacity(0.1) }
            if index == viewModel.selectedOptionIndex { return .red.opacity(0.1) }
        } else if viewModel.selectedOptionIndex == index {
            return .blue.opacity(0.1)
        }
        return .clear
    }
    
    
    private func borderColor(for index: Int) -> Color {
        guard let question = viewModel.currentQuestion else { return .gray.opacity(0.3) }
        
        if viewModel.isAnswerSubmitted {
            if index == question.correctAnswerIndex { return .green }
            if index == viewModel.selectedOptionIndex { return .red }
        } else if viewModel.selectedOptionIndex == index {
            return .blue
        }
        return .gray.opacity(0.3)
    }
}

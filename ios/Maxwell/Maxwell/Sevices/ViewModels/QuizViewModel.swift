import Foundation
import Combine

@MainActor
class QuizViewModel: ObservableObject {
    let problems: [QuizProblem]
    @Published var currentProblemIndex = 0
    
    init(problems: [QuizProblem]) {
        self.problems = problems
    }
    
    var currentProblem: QuizProblem? {
        guard currentProblemIndex < problems.count else { return nil }
        return problems[currentProblemIndex]
    }
}

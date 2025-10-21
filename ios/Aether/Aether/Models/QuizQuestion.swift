import Foundation

struct QuizProblemSet {
    let problems: [QuizProblem]
}

struct QuizProblem: Codable, Identifiable, Hashable {
    let id: UUID
    let text: String
    let options: [String]
    let correctAnswerIndex: Int
}

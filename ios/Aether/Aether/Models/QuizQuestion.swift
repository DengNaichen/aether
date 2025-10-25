import Foundation

struct QuizProblemSet {
    let problems: [mcqQuestion]
}

struct mcqQuestion: Codable, Identifiable, Hashable {
    let id: UUID
    let text: String
    let options: [String]
    let correctAnswerIndex: Int
}

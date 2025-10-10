import Foundation

struct QuizProblemSet { // 名字可以更具体
    let problems: [QuizProblem]
}

// 我们可以叫它 QuizProblem，更清晰地表达其用途
struct QuizProblem: Codable, Identifiable, Equatable {
    let id: UUID // 让它直接使用 API 返回的 ID
    let text: String
    let options: [String]
    let correctAnswerIndex: Int
    // 可以在这里添加 UI 状态，比如 var selectedAnswerIndex: Int?
}

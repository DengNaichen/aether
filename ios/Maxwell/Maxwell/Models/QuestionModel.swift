import Foundation

enum QuestionDifficulty: String, Codable {
    case easy = "easy"
    case medium = "medium"
    case hard = "hard"
}

struct MultipleChoiceDetails: Codable, Equatable {
    let options: [String]
    let correctAnswer: Int
    
    enum CodingKeys: String, CodingKey {
        case options
        case correctAnswer = "correct_answer"
    }
}

struct FillInTheBlankDetails: Codable, Equatable {
    // TODO: The backend not finish this part
}

struct MultipleChoiceQuestion: Codable, Equatable {
    let id: UUID
    let text: String
    let difficulty: QuestionDifficulty
    let knowledgePointId: String
    let questionType: String // "multiple_choice"
    let details: MultipleChoiceDetails
    
    enum CodingKeys: String, CodingKey {
        case id, text, difficulty, details
        case knowledgePointId = "knowledge_point_id"
        case questionType = "question_type"
    }
}

struct FillInTheBlankQuestion: Codable, Equatable {
    let id: UUID
    let text: String
    let difficulty: QuestionDifficulty
    let knowledgePointId: String
    let questionType: String // "fill_in_the_blank"
    let details: FillInTheBlankDetails

    enum CodingKeys: String, CodingKey {
        case id, text, difficulty, details
        case knowledgePointId = "knowledge_point_id"
        case questionType = "question_type"
    }
}

enum AnyQuestion: Codable, Equatable {
    case multipleChoice(MultipleChoiceQuestion)
        case fillInTheBlank(FillInTheBlankQuestion)

        // 用于解码时识别类型的 Key
        private enum CodingKeys: String, CodingKey {
            case questionType = "question_type"
        }
        
        // 自定义解码逻辑
        init(from decoder: Decoder) throws {
            // 1. 先读取 "question_type" 字段的值
            let container = try decoder.container(keyedBy: CodingKeys.self)
            let type = try container.decode(String.self, forKey: .questionType)

            // 2. 根据 "question_type" 的值，决定将整个 JSON 解码成哪个具体的结构体
            switch type {
            case "multiple_choice":
                let question = try MultipleChoiceQuestion(from: decoder)
                self = .multipleChoice(question)
            case "fill_in_the_blank":
                let question = try FillInTheBlankQuestion(from: decoder)
                self = .fillInTheBlank(question)
            default:
                throw DecodingError.dataCorruptedError(
                    forKey: .questionType,
                    in: container,
                    debugDescription: "Invalid question type: \(type)"
                )
            }
        }

        // 自定义编码逻辑
        func encode(to encoder: Encoder) throws {
            // 直接将关联的具体问题对象进行编码即可
            var container = encoder.singleValueContainer()
            switch self {
            case .multipleChoice(let question):
                try container.encode(question)
            case .fillInTheBlank(let question):
                try container.encode(question)
            }
        }
    }

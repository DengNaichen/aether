




















enum AnyAnswer: Codable {
    case multipleChoice(selectedOption: Int)
    case fillInTheBlank(textAnswer: String)
    case calculation(numericAnswer: Int)
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        
        switch self {
        case .multipleChoice(let option):
            try container.encode(QuestionType.multipleChoice.rawValue, forKey: .questionType)
            try container.encode(option, forKey: .selectedOption)
            
        case .fillInTheBlank(let text):
            try container.encode(QuestionType.fillInTheBlank.rawValue, forKey: .questionType)
            try container.encode(text, forKey: .textAnswer)

        case .calculation(let number):
            try container.encode(QuestionType.calculation.rawValue, forKey: .questionType)
            try container.encode(number, forKey: .numericAnswer)
                
        }
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let type = try container.decode(String.self, forKey: .questionType)
        
        switch type {
        case QuestionType.multipleChoice.rawValue:
            let option = try container.decode(Int.self, forKey: .selectedOption)
            self = .multipleChoice(selectedOption: option)
        
        case QuestionType.fillInTheBlank.rawValue:
            let text = try container.decode(String.self, forKey: .textAnswer)
            self = .fillInTheBlank(textAnswer: text)
        
        case QuestionType.calculation.rawValue:
            let number = try container.decode(Int.self, forKey: .numericAnswer)
            self = .calculation(numericAnswer: number)
        default:
            throw DecodingError.dataCorruptedError(
                forKey: .questionType,
                in: container,
                debugDescription: "Unknown Question Type"
            )
        }
    }
    
    enum CodingKeys: String, CodingKey {
        case questionType = "question_type"
        case selectedOption = "selected_option"
        case textAnswer = "text_answer"
        case numericAnswer = "numeric_answer"
    }
}






//struct FillInTheBlankDetails: Codable, Equatable {
//    // TODO: The backend not finish this part
//}



//struct FillInTheBlankQuestion: Codable, Equatable {
//    let id: UUID
//    let text: String
//    let difficulty: QuestionDifficulty
//    let knowledgePointId: String
//    let questionType: String // "fill_in_the_blank"
//    let details: FillInTheBlankDetails
//
//    enum CodingKeys: String, CodingKey {
//        case id, text, difficulty, details
//        case knowledgePointId = "knowledge_point_id"
//        case questionType = "question_type"
//    }
//}



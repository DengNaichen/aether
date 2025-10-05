//
//  QuestionModel.swift
//  Maxwell
//
//  Created by Daniel on 2025-09-28.
//
import Foundation

struct ProblemSet: Codable {
    let problems: [MultipleChoiceQuestion]
}

struct MultipleChoiceQuestion: Codable, Identifiable {
    let id = UUID()
    
    var text: String
    var options: [String]
    var correctAnswerIndex: Int
    
    enum CodingKeys: String, CodingKey {
        case text = "question"
        case options
        case correctAnswerIndex = "correct"
    }
}

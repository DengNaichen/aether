//
//  QuestionLoader.swift
//  Maxwell
//
//  Created by Daniel on 2025-10-01.
//
import Foundation

class QuestionLoader {
    func LoadQuestions(from filename: String) -> [MultipleChoiceQuestion] {
        guard let fileURL = Bundle.main.url(forResource: filename, withExtension: "json") else {
            fatalError("Couldnt find \(filename) in main bundle.")
        }
        
        do {
            let data = try Data(contentsOf: fileURL)
            let decoder = JSONDecoder()
            let problemSet = try decoder.decode(ProblemSet.self, from: data)
            return problemSet.problems
        } catch {
            fatalError("Could't parse \(filename) as \(ProblemSet.self): \n(error)")
        }
    }
}


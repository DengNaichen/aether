import Foundation

struct AlertItem: Identifiable {
    let id = UUID()
    let title: String
    let message: String
    
    init(title: String, message: String) {
        self.title = title
        self.message = message
    }
}
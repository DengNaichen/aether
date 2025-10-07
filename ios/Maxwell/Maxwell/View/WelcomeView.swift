import SwiftUI

struct WelcomeView: View {
    var body: some View {
        // 1. 使用 NavigationStack 作为导航容器
        NavigationStack {
            VStack(spacing: 30) {
                Text("😅😒🤯")
                    .font(.largeTitle)
                NavigationLink(destination:QuizView()) {
                    Text("Start a quiz")
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }
            .padding()
            .navigationTitle("Welcome")
        }
    }
}


#Preview {
    WelcomeView()
}



import SwiftUI

struct WelcomeView: View {
    var body: some View {
        // 1. 使用 NavigationStack 作为导航容器
        NavigationStack {
            VStack(spacing: 30) {
                Text("😅😒🤯")
                    .font(.largeTitle)
                
                // 2. 创建一个 NavigationLink
                // destination: 指定要跳转到的目标视图
                // label: 定义链接的外观，这里是一个带文字的按钮
                NavigationLink(destination:QuizView()) {
                    Text("Start a quiz")
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
//                NavigationLink(destination: RegistrationView()) {
//                    Text("注册账户")
//                        .padding()
//                        .frame(maxWidth: .infinity) // 让按钮宽度撑满
//                        .background(Color.green) // 可以用不同的颜色区分
//                        .foregroundColor(.white)
//                        .cornerRadius(10)
//                }
//                NavigationLink(destination: LoginView()) {
//                    Text("Login")
//                        .padding()
//                        .frame(maxWidth: .infinity) // 让按钮宽度撑满
//                        .background(Color.yellow) // 可以用不同的颜色区分
//                        .foregroundColor(.white)
//                        .cornerRadius(10)
//                }
            }
            .padding()
            .navigationTitle("Welcome") // 设置首页的导航栏标题
        }
    }
}


#Preview {
    WelcomeView()
}



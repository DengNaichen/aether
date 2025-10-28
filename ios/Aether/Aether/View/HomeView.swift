import SwiftUI
import SwiftData
import Combine

struct HomeView: View {
    @Environment(\.modelContext) private var modelContext
    @StateObject private var courseViewModel: CourseViewModel
    @StateObject private var quizViewModel: QuizViewModel
    @StateObject private var statisticsViewModel: LearningStatisticsViewModel
    private let network: NetworkServicing
    
    @State private var selectedCourseId: String?

    init(network: NetworkServicing, modelContext: ModelContext) {
        self.network = network
        self._courseViewModel = StateObject(wrappedValue: CourseViewModel(network: network, modelContext: modelContext))
        self._quizViewModel = StateObject(wrappedValue: QuizViewModel(network: network, modelContext: modelContext))
        self._statisticsViewModel = StateObject(wrappedValue: LearningStatisticsViewModel(modelContext: modelContext))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 20) {
                    // 欢迎标题
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Welcome to Quiz Dashboard")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                        
                        Text("Select a course to start a quiz")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.horizontal)
                    .padding(.top, 10)
                    
                    // 学习统计视图 - 类似 GitHub 贡献图
                    LearningActivityChart(statisticsViewModel: statisticsViewModel)
                        .padding(.horizontal)
                    
                    // 已注册课程列表
                    if courseViewModel.isLoading {
                        VStack {
                            ProgressView("Loading courses...")
                            Spacer()
                        }
                        .frame(maxWidth: .infinity)
                        .frame(minHeight: 200)
                    } else {
                        enrolledCoursesContent
                    }
                }
                .padding(.bottom, 20)
            }
            .navigationTitle("Dashboard")
            .navigationBarTitleDisplayMode(.inline)
            .navigationDestination(isPresented: .constant(selectedCourseId != nil)) {
                if let courseId = selectedCourseId {
                    QuizView(courseId: courseId, network: network, modelContext: modelContext)
                }
            }
            .onAppear {
                Task {
                    await courseViewModel.fetchAllCourses()
                    await statisticsViewModel.loadStatistics()
                }
            }
            .alert(item: $courseViewModel.alertItem) { alertItem in
                Alert(title: Text(alertItem.title), message: Text(alertItem.message), dismissButton: .default(Text("OK")))
            }
            .alert(item: $quizViewModel.alertItem) { alertItem in
                Alert(title: Text(alertItem.title), message: Text(alertItem.message), dismissButton: .default(Text("OK")))
            }
        }
    }
    
    @ViewBuilder
    private var enrolledCoursesContent: some View {
        let enrolledCourses = courseViewModel.courses.filter { $0.isEnrolled }
        
        if enrolledCourses.isEmpty {
            VStack(spacing: 16) {
                Image(systemName: "graduationcap")
                    .font(.system(size: 50))
                    .foregroundColor(.gray)
                
                Text("No Enrolled Courses")
                    .font(.title2)
                    .fontWeight(.medium)
                
                Text("Go to the Courses tab to enroll in a course and start taking quizzes.")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
            .frame(maxWidth: .infinity)
            .frame(minHeight: 200)
            .padding(.horizontal)
        } else {
            LazyVStack(spacing: 12) {
                ForEach(enrolledCourses) { course in
                    EnrolledCourseCard(
                        course: course,
                        onStartQuiz: {
                            startQuizFor(course: course)
                        },
                        isLoading: quizViewModel.isLoading
                    )
                }
            }
            .padding(.horizontal)
        }
    }
    
    private func startQuizFor(course: Course) {
        // 导航到QuizView，QuizView会自动启动quiz（默认10个问题）
        selectedCourseId = course.courseId
    }
}

struct EnrolledCourseCard: View {
    let course: Course
    let onStartQuiz: () -> Void
    let isLoading: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(course.courseName)
                        .font(.headline)
                        .fontWeight(.bold)
                    
                    Text("\(course.numOfKnowledgeNodes) knowledge nodes")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // Quiz开始按钮
                Button(action: onStartQuiz) {
                    HStack(spacing: 6) {
                        Image(systemName: "play.fill")
                        Text("Start Quiz")
                    }
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 8)
                    .background(
                        LinearGradient(
                            colors: [Color.blue, Color.purple],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(8)
                }
                .disabled(isLoading)
            }
        }
        .padding(16)
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.1), radius: 2, x: 0, y: 1)
    }
}

//#if DEBUG
//import SwiftData
//
//@MainActor
//struct HomeView_Previews: PreviewProvider {
//    
//    static func createMockData() -> (NetworkServicing, ModelContainer) {
//        let mockNetwork = MockNetworkService()
//        // 设置一些有enrolled课程的mock数据
//        mockNetwork.mockResponse = FetchAllCoursesResponse(courses: [
//            FetchCourseResponse(
//                courseId: "swift-101",
//                courseName: "Swift Programming 101",
//                courseDescription: "Learn Swift basics",
//                isEnrolled: true,
//                numOfKnowledgeNode: 25
//            ),
//            FetchCourseResponse(
//                courseId: "ios-dev",
//                courseName: "iOS Development",
//                courseDescription: "Build iOS apps",
//                isEnrolled: true,
//                numOfKnowledgeNode: 40
//            ),
//            FetchCourseResponse(
//                courseId: "advanced-swift",
//                courseName: "Advanced Swift",
//                courseDescription: "Advanced concepts",
//                isEnrolled: false,
//                numOfKnowledgeNode: 30
//            )
//        ])
//        
//        let container = try! ModelContainer(
//            for: CourseModel.self, QuizAttempt.self, StoredQuestion.self,
//            configurations: .init(isStoredInMemoryOnly: true)
//        )
//        
//        return (mockNetwork, container)
//    }
//    
//    static var previews: some View {
//        let (mockNetwork, container) = createMockData()
//        
//        HomeView(network: mockNetwork, modelContext: container.mainContext)
//            .modelContainer(container)
//            .previewDisplayName("Dashboard with Enrolled Courses")
//    }
//}

// MARK: - Learning Statistics Components

@MainActor
class LearningStatisticsViewModel: ObservableObject {
    private let modelContext: ModelContext
    
    @Published var weeklyStats: [LearningDay] = []
    @Published var totalQuizzesCompleted: Int = 0
    @Published var currentStreak: Int = 0
    @Published var longestStreak: Int = 0
    
    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }
    
    func loadStatistics() async {
        // 先尝试加载真实数据
        await loadRealStatistics()
        
        // 如果没有真实数据，使用mock数据
        if weeklyStats.allSatisfy({ $0.quizCount == 0 }) {
            loadMockStatistics()
        }
    }
    
    private func loadRealStatistics() async {
        // 加载过去3个月的统计数据
        let calendar = Calendar.current
        let endDate = Date()
        let startDate = calendar.date(byAdding: .month, value: -3, to: endDate) ?? endDate
        
        do {
            let descriptor = FetchDescriptor<QuizAttempt>(
                predicate: #Predicate<QuizAttempt> { attempt in
                    attempt.createdAt >= startDate && attempt.createdAt <= endDate && attempt.statusRawValue == "COMPLETED"
                },
                sortBy: [SortDescriptor(\.createdAt)]
            )
            
            let completedQuizzes = try modelContext.fetch(descriptor)
            
            // 计算每日统计
            var dailyStats: [String: Int] = [:]
            let dateFormatter = DateFormatter()
            dateFormatter.dateFormat = "yyyy-MM-dd"
            
            for quiz in completedQuizzes {
                let dateString = dateFormatter.string(from: quiz.createdAt)
                dailyStats[dateString, default: 0] += 1
            }
            
            // 计算从开始日期到今天的天数
            let daysDifference = calendar.dateComponents([.day], from: startDate, to: endDate).day ?? 90
            let totalDays = min(daysDifference + 1, 90) // 最多90天（3个月）
            
            // 生成每日数据
            var stats: [LearningDay] = []
            for i in 0..<totalDays {
                let date = calendar.date(byAdding: .day, value: -(totalDays - 1 - i), to: endDate) ?? endDate
                let dateString = dateFormatter.string(from: date)
                let count = dailyStats[dateString] ?? 0
                
                stats.append(LearningDay(
                    date: date,
                    quizCount: count,
                    level: LearningLevel.from(count: count)
                ))
            }
            
            self.weeklyStats = stats
            self.totalQuizzesCompleted = completedQuizzes.count
            self.calculateStreaks(from: stats)
            
        } catch {
            print("Error loading learning statistics: \(error)")
            // 如果出错，加载mock数据
            loadMockStatistics()
        }
    }
    
    private func loadMockStatistics() {
        let calendar = Calendar.current
        let endDate = Date()
        
        // 创建mock数据，模拟过去90天（3个月）的学习活动
        let totalDays = 90
        var stats: [LearningDay] = []
        var totalCompleted = 0
        
        // 调试：打印日期范围
        let startDate = calendar.date(byAdding: .day, value: -totalDays + 1, to: endDate) ?? endDate
        print("Mock data date range: \(startDate.formatted()) to \(endDate.formatted())")
        
        for i in 0..<totalDays {
            let date = calendar.date(byAdding: .day, value: -(totalDays - 1 - i), to: endDate) ?? endDate
            
            // 获取当前日期的月份和星期
            let currentMonth = calendar.component(.month, from: date)
            let dayOfWeek = calendar.component(.weekday, from: date)
            let currentMonthNow = calendar.component(.month, from: endDate)
            
            var quizCount = 0
            
            // 计算距离今天的天数
            let daysFromToday = totalDays - 1 - i
            
            // 模拟真实的学习模式
            if dayOfWeek == 1 || dayOfWeek == 7 { // 周末
                quizCount = Int.random(in: 0...2) // 周末较少学习
            } else { // 工作日
                let random = Int.random(in: 0...10)
                if random < 2 {
                    quizCount = 0 // 20% 的天数不学习
                } else if random < 6 {
                    quizCount = Int.random(in: 1...2) // 40% 的天数轻度学习
                } else if random < 9 {
                    quizCount = Int.random(in: 3...4) // 30% 的天数中度学习
                } else {
                    quizCount = Int.random(in: 5...7) // 10% 的天数高强度学习
                }
            }
            
            // 根据距离今天的天数调整强度（越近的日期活动越多）
            if daysFromToday <= 20 { // 最近20天（主要是10月）
                // 大幅增加10月的学习活动
                if quizCount == 0 && Int.random(in: 0...3) == 0 { // 25%的概率将0变成有学习
                    quizCount = Int.random(in: 1...3)
                } else if quizCount > 0 {
                    quizCount = min(quizCount + Int.random(in: 1...3), 8) // 增加强度，但限制最大值
                }
                // 确保最近一周有更多活动
                if daysFromToday <= 7 {
                    quizCount = max(quizCount, 1) // 至少有1个quiz
                    if quizCount > 0 {
                        quizCount = Int.random(in: 2...6) // 高强度学习
                    }
                }
            } else if daysFromToday <= 50 { // 中期（主要是9月）
                if quizCount > 0 {
                    quizCount = min(quizCount + Int.random(in: 0...1), 5)
                }
            } else { // 早期（主要是8月）
                if quizCount > 2 {
                    quizCount = max(quizCount - 1, 1)
                }
            }
            
            // 模拟一些连续学习的模式
            if daysFromToday >= 45 && daysFromToday <= 60 { // 8月底到9月初的连续学习期
                quizCount = max(1, quizCount)
            }
            
            if daysFromToday >= 20 && daysFromToday <= 35 { // 9月中下旬的学习冲刺期
                if dayOfWeek != 1 && dayOfWeek != 7 { // 工作日
                    quizCount = Int.random(in: 2...5)
                }
            }
            
            totalCompleted += quizCount
            
            // 调试：打印最近几天的数据
            if daysFromToday <= 10 {
                print("Day \(daysFromToday) days ago (\(date.formatted(.dateTime.month().day()))): \(quizCount) quizzes")
            }
            
            stats.append(LearningDay(
                date: date,
                quizCount: quizCount,
                level: LearningLevel.from(count: quizCount)
            ))
        }
        
        print("Total mock quizzes: \(totalCompleted)")
        print("Recent 7 days total: \(stats.suffix(7).map { $0.quizCount }.reduce(0, +))")
        
        self.weeklyStats = stats
        self.totalQuizzesCompleted = totalCompleted
        self.calculateStreaks(from: stats)
    }
    
    private func calculateStreaks(from stats: [LearningDay]) {
        let sortedStats = stats.sorted { $0.date < $1.date }
        
        var current = 0
        var longest = 0
        var currentStreak = 0
        
        // 从今天开始倒推计算当前连续天数
        for stat in sortedStats.reversed() {
            if stat.quizCount > 0 {
                current += 1
            } else {
                break
            }
        }
        
        // 计算最长连续天数
        for stat in sortedStats {
            if stat.quizCount > 0 {
                currentStreak += 1
                longest = max(longest, currentStreak)
            } else {
                currentStreak = 0
            }
        }
        
        self.currentStreak = current
        self.longestStreak = longest
    }
}

struct LearningDay: Equatable {
    let date: Date
    let quizCount: Int
    let level: LearningLevel
}

enum LearningLevel: Int, CaseIterable, Equatable {
    case none = 0
    case light = 1
    case medium = 2
    case high = 3
    case intense = 4
    
    static func from(count: Int) -> LearningLevel {
        switch count {
        case 0:
            return .none
        case 1:
            return .light
        case 2:
            return .medium
        case 3:
            return .high
        default:
            return .intense
        }
    }
    
    var color: Color {
        switch self {
        case .none:
            return Color(.systemGray6)
        case .light:
            return Color.green.opacity(0.3)
        case .medium:
            return Color.green.opacity(0.5)
        case .high:
            return Color.green.opacity(0.7)
        case .intense:
            return Color.green
        }
    }
}

struct LearningActivityChart: View {
    @ObservedObject var statisticsViewModel: LearningStatisticsViewModel
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Learning Activity")
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text("Past 3 months")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                // 统计信息
                HStack(spacing: 16) {
                    StatisticItem(title: "Total", value: "\(statisticsViewModel.totalQuizzesCompleted)")
                    StatisticItem(title: "Current Streak", value: "\(statisticsViewModel.currentStreak)")
                    StatisticItem(title: "Longest Streak", value: "\(statisticsViewModel.longestStreak)")
                }
            }
            
            // 周标签
            HStack(spacing: 0) {
                ForEach(weekLabels, id: \.self) { label in
                    Text(label)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, 2)
            
            // GitHub 风格的活动图表 - 每周一列，每天一行
            HStack(spacing: 3) {
                ForEach(groupedByWeeks.indices, id: \.self) { weekIndex in
                    VStack(spacing: 2) {
                        ForEach(groupedByWeeks[weekIndex].indices, id: \.self) { dayIndex in
                            let day = groupedByWeeks[weekIndex][dayIndex]
                            
                            Rectangle()
                                .fill(day?.level.color ?? Color.clear)
                                .frame(width: 12, height: 12)
                                .cornerRadius(2)
                                .help(day != nil ? "\(day!.quizCount) quizzes on \(day!.date.formatted(date: .abbreviated, time: .omitted))" : "")
                        }
                    }
                }
            }
            
            // 图例
            HStack {
                Text("Less")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                HStack(spacing: 2) {
                    ForEach(LearningLevel.allCases, id: \.self) { level in
                        Rectangle()
                            .fill(level.color)
                            .frame(width: 8, height: 8)
                            .cornerRadius(1)
                    }
                }
                
                Text("More")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                
                Spacer()
            }
        }
        .padding(16)
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    // 将数据按周分组，每周7天
    private var groupedByWeeks: [[LearningDay?]] {
        let stats = statisticsViewModel.weeklyStats
        guard !stats.isEmpty else { return [] }
        
        var weeks: [[LearningDay?]] = []
        let calendar = Calendar.current
        
        // 找到第一天是星期几
        let firstDate = stats.first!.date
        let firstWeekday = calendar.component(.weekday, from: firstDate)
        let adjustedFirstWeekday = (firstWeekday + 5) % 7 // 转换为周一=0, 周二=1, ..., 周日=6
        
        var currentWeek: [LearningDay?] = Array(repeating: nil, count: 7)
        var dayIndex = 0
        
        // 填充第一周的前面空白天数
        for i in 0..<adjustedFirstWeekday {
            currentWeek[i] = nil
        }
        
        for day in stats {
            let weekday = calendar.component(.weekday, from: day.date)
            let adjustedWeekday = (weekday + 5) % 7 // 转换为周一=0, 周二=1, ..., 周日=6
            
            currentWeek[adjustedWeekday] = day
            
            // 如果是周日或者是最后一天，完成当前周
            if adjustedWeekday == 6 || day == stats.last {
                weeks.append(currentWeek)
                currentWeek = Array(repeating: nil, count: 7)
            }
        }
        
        return weeks
    }
    
    private var weekLabels: [String] {
        let calendar = Calendar.current
        let now = Date()
        var labels: [String] = []
        var lastMonth = -1
        
        let monthFormatter = DateFormatter()
        monthFormatter.dateFormat = "MMM"
        
        // 生成最近13周的标签（3个月约13周）
        for i in 0..<13 {
            let weekStart = calendar.dateInterval(of: .weekOfYear, for: calendar.date(byAdding: .weekOfYear, value: -12 + i, to: now) ?? now)?.start ?? now
            let currentMonth = calendar.component(.month, from: weekStart)
            
            // 只在月份改变时显示月份标签
            if currentMonth != lastMonth {
                labels.append(monthFormatter.string(from: weekStart))
                lastMonth = currentMonth
            } else {
                labels.append("")
            }
        }
        
        return labels
    }
}

struct StatisticItem: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(alignment: .center, spacing: 2) {
            Text(value)
                .font(.headline)
                .fontWeight(.bold)
            
            Text(title)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}
//#endif

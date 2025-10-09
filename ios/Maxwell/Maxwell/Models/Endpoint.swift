struct LoginEndpoint: Endpoint {
    let loginData: [String: String]
    
    var path: String { "/auth/login" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .formUrlEncoded(loginData) }
    
    var requiredAuth: Bool { false }
}

struct EnrollCourseEndpoint: Endpoint {
    let courseId: String
    
    var path: String { "/enrollments/course" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? {
        .json(EnrollmentRequest(courseId: courseId))
    }
    
    var requiredAuth: Bool { true }
}

struct RegisterEndpoint: Endpoint {
    let registrationRequest: RegistrationRequest
    
    var path: String { "/auth/register" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(registrationRequest) }
    var requiredAuth: Bool { false }
}

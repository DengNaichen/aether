# Maxwell Learning System

An adaptive learning system for Ontario high school students. It leverages a knowledge graph to model subjects and provide personalized learning paths and exercises.

## Features

* **Knowledge Graph:** Structures academic subjects (e.g., Ontario G11 Physics, Chemistry) into nodes and relationships, forming the foundation for personalized recommendations.
* **Adaptive Learning:** Dynamically recommends learning content and practice problems tailored to a student's current proficiency level, based on their response history and knowledge state.
* **Student Modeling:** Models and predicts a student's mastery of concepts using algorithms like Bayesian Knowledge Tracing (BKT).

## Tech Stack

| Category              | Technology                                                     |
| --------------------- | -------------------------------------------------------------- |
| **Backend** | Python, FastAPI                                                |
| **Frontend** | Swift, SwiftUI (iOS App)                                       |
| **Database** | Neo4j (for the knowledge graph and problems), PostgreSQL (for user data, etc.) |
| **Development & Deployment** | Docker, Docker Compose                                         |
| **Testing** | Pytest                                                         |

## 🚀 Getting Started

Ensure you have Docker, Python 3.10+, and Xcode installed on your development machine.

### 1. Clone the Repository

    git clone <your-repository-url>
    cd maxwell-learning-system

### 2. Configure Backend and Database

1.  **Start Database Services:**
    This project uses Docker Compose to manage database services. Run the following command from the project root directory:

        docker-compose up -d

    This will start the Neo4j and PostgreSQL containers in the background.

2.  **Set Up the Backend Environment:**
    It's recommended to create a virtual environment for the Python backend.

        cd backend
        python -m venv venv
        source venv/bin/activate  # macOS/Linux
        # venv\Scripts\activate   # Windows

3.  **Install Dependencies:**

        pip install -r requirements.txt

4.  **Configure Environment Variables:**
    Copy the `.env.example` file to create a new `.env` file, then fill in your local database connection details and other required variables.

### 3. Configure the Frontend (iOS)

1.  Navigate to the iOS app directory:

        cd ../ios-app

2.  Open the `.xcodeproj` or `.xcworkspace` file with Xcode.
3.  Locate the `NetworkService` configuration and ensure the API `baseURL` points to your local backend service (e.g., `http://localhost:8000`).

## ▶️ How to Run

1.  **Run the Backend Service:**
    With your virtual environment activated, run the following command in the `backend` directory:

        uvicorn app.main:app --reload

    Your backend API will be available at `http://localhost:8000`.

2.  **Run the iOS App:**
    In Xcode, select a simulator or a connected device and click the "Run" button.

## 🗺️ Roadmap

-   [ ] **User Authentication:** Finalize the complete registration and login flow.
-   [ ] **Knowledge Graph Construction:** Expand the knowledge graph data for G11 Physics and Chemistry.
-   [ ] **BKT Algorithm Implementation:** Implement the Bayesian Knowledge Tracing algorithm on the backend to update student knowledge states.
-   [ ] **Problem Recommendation Engine:** Develop the logic for recommending problems based on the knowledge graph and student model.
-   [ ] **Learning Path Visualization:** Display the student's knowledge graph and recommended learning paths in the frontend app.
-   [ ] **Improve Test Coverage:** Write comprehensive unit and integration tests for the backend API.

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

## 📄 License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) License.
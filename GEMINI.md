# Gemini Project Overview: Aether

This document provides a summary of the Aether project to help guide development and maintenance.

## Project Overview

Aether is an intelligent knowledge management and adaptive learning platform. The backend is built with Python and FastAPI, designed to create and manage knowledge graphs. It allows users to interact with structured curricula, tracks their learning progress using a Bayesian Knowledge Tracing (BKT) model, and recommends questions for review using a Free Spaced Repetition Scheduler (FSRS) to enhance long-term memory. The platform also features AI-assisted content creation, leveraging LangChain and Google's Generative AI to generate questions and create knowledge graphs from PDF documents.

## Key Technologies

- **Backend:** Python 3.12, FastAPI
- **Database:** PostgreSQL
- **Containerization:** Docker, Docker Compose
- **AI & Machine Learning:**
  - LangChain
  - Google Generative AI (`google-genai`)
  - Free Spaced Repetition Scheduler (`fsrs`)
- **Package Management & Environment:** `uv`
- **Testing:** `pytest`

## Project Structure

The project is organized as a standard FastAPI application:

- `app/`: Contains the core application logic.
  - `main.py`: The FastAPI application entrypoint.
  - `core/`: Core settings, configuration, and database connections.
  - `models/`: SQLAlchemy database models.
  - `schemas/`: Pydantic schemas for data validation and serialization.
  - `crud/`: Functions for Create, Read, Update, Delete database operations.
  - `routes/`: API endpoint definitions.
  - `services/`: Business logic, including AI-powered services for content generation and grading.
- `scripts/`: Contains utility and administrative scripts for managing the application, such as database seeding and content ingestion.
- `tests/`: Contains the test suite for the application.
- `docker-compose.yml`: Defines the services, networks, and volumes for the development environment.
- `Dockerfile`: Defines the Docker image for the application.
- `pyproject.toml`: Defines project dependencies and metadata.

## How to Run the Application

1.  **Start the services:**
    ```bash
    docker-compose up
    ```
2.  **Seed the database (for first-time setup):**
    ```bash
    docker-compose exec web uv run python scripts/setup_dev_data_pg.py
    ```

## How to Run Tests

1.  **Start the test environment:**
    ```bash
    make test-up
    ```
2.  **Run the test suite:**
    ```bash
    uv run pytest
    ```

## Key Scripts

The `scripts/` directory contains several important scripts for managing the application:

- `scripts/setup_dev_data_pg.py`: Initializes the development database with sample data.
- `scripts/import_pdf_to_graph.py`: Processes a PDF file to create a new knowledge graph.
- `scripts/generate_questions_for_graph.py`: Uses AI to generate questions for an existing knowledge graph.

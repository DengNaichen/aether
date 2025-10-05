import json
import os

# JSON_FILE_PATH = "force_prob.json"
# PROBLEM_TYPES = {"multiple_choice", "fill_in_the_blank", "short_answer"}
#
#
# def get_required_fields(prompt):
#     """enture the prompt is not empty and is a string."""
#     while True:
#         user_input = input(prompt).strip()
#         if user_input:
#             return user_input
#         print("input cannot be empty. Please try again.")
#
# def get_common_details():
#     """get the common details for all problem types."""
#     problem = {}
#     problem["problemId"] = get_required_fields("Enter problem ID (e.g., FF_MCQ_001): ")
#
#     print("Select problem type:")
#     for idx, p_type in enumerate(PROBLEM_TYPES):
#         print(f"{idx + 1}: {p_type}")
#     while True:
#         try:
            
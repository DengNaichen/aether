import json
import os

JSON_FILE_PATH = "test_problem.json"
PROBLEM_TYPES = ["multiple_choice", "fill_in_the_blank"]


def get_required_fields(prompt):
    """enture the prompt is not empty and is a string."""
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("input cannot be empty. Please try again.")


def get_common_details():
    """get the common details for all problem types."""
    problem = {}
    problem["problemId"] = get_required_fields("Enter problem ID (e.g., FF_MCQ_001): ")

    print("Select problem type:")
    for idx, p_type in enumerate(PROBLEM_TYPES):
        print(f"{idx + 1}: {p_type}")
    while True:
        try:
            choice = int(
                input(f"Please input the number of choice (1-{len(PROBLEM_TYPES)}): ")
            )
            if 1 <= choice <= len(PROBLEM_TYPES):
                problem["problemType"] = PROBLEM_TYPES[choice - 1]
                break
            else:
                print(f"Please input a number between 1 and {len(PROBLEM_TYPES)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    problem["problemContent"] = get_required_fields("Enter problem text: ")

    # tags_str = input("Enter tags (comma-separated): ")
    # problem["tags"] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]  # Remove empty tags

    return problem


def get_multiple_choice_details():
    """get the details specific to multiple choice problems."""
    details = {}
    options = []
    OPTIONS_KEYS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    # obtain the number of options
    while True:
        num_options_str = input(
            f"How many options do you want to add? (1-{len(OPTIONS_KEYS)}): "
        ).strip()
        if num_options_str.isdigit() and 1 <= int(num_options_str) <= len(OPTIONS_KEYS):
            num_options = int(num_options_str)
            break
        else:
            print(f"Please input a number between 1 and {len(OPTIONS_KEYS)}.")

    # obtain the options one by one
    print("\n--- Input Options ---")
    for i in range(num_options):
        options_key = OPTIONS_KEYS[i]
        option_value = get_required_fields(
            f"Please input option {options_key} content: "
        )
        options.append({"key": options_key, "value": option_value})

    details["options"] = options

    print("\n--- input the correct answer ---")
    while True:
        answer_key = (
            get_required_fields("Please input the correct option key (A, B, C, ...): ")
            .strip()
            .upper()
        )

        if any(opt["key"] == answer_key for opt in options):
            details["answer"] = {"key": answer_key}
            break
        else:
            print(
                "error: The answer key must be one of the options provided. Please try again."
            )

    return details


def main():
    print("--- multiple choice create guide ---")

    new_problem = get_common_details()

    p_type = new_problem["problemType"]
    print(f"\n--- creating '{p_type}' typing problem ---")

    type_specific_details = {}
    if p_type == "multiple_choice":
        type_specific_details = get_multiple_choice_details()
    elif p_type == "fill_in_the_blank":
        pass
    elif p_type == "short_answer":
        pass

    new_problem.update(type_specific_details)

    print("\n--- preview the problem ---")
    print(json.dumps(new_problem, indent=2, ensure_ascii=False))

    if input("\ndo you want to save? (y/n): ").lower() != "y":
        print("operation cancelled. no changes made.")
        return

    # 4. write to the JSON file
    problems = []
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            try:
                problems = json.load(f)
                if not isinstance(problems, list):  #
                    print(
                        f"warning: {JSON_FILE_PATH} file content is not a list, creating a new list."
                    )
                    problems = []
            except json.JSONDecodeError:
                print(
                    f"warning: {JSON_FILE_PATH} file is empty or invalid, creating a new list."
                )

    problems.append(new_problem)

    with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)

    print(f"\n success: the problem is created in: {JSON_FILE_PATH}。")


if __name__ == "__main__":
    main()

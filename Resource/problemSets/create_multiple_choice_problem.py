import json
import os
import uuid
from datetime import datetime

# --- 配置 ---
JSON_FILE_PATH = "force_problems.json"  # 建议使用和导入脚本一致的文件名
PROBLEM_TYPES = ["multiple_choice", "fill_in_the_blank", "short_answer"]


def get_required_input(prompt):
    """ensure the user provides a non-empty input."""
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("error: this field is required. please try again.")


def get_common_details():
    """get common details for all problem types."""
    problem = {}

    # 让用户选择题型
    print("请选择题目类型:")
    for idx, p_type in enumerate(PROBLEM_TYPES):
        print(f"  {idx + 1}: {p_type}")
    while True:
        try:
            choice = int(input(f"请输入选项数字 (1-{len(PROBLEM_TYPES)}): "))
            if 1 <= choice <= len(PROBLEM_TYPES):
                problem["problemType"] = PROBLEM_TYPES[choice - 1]
                break
            else:
                print(f"错误：请输入一个 1 到 {len(PROBLEM_TYPES)} 之间的数字。")
        except ValueError:
            print("错误：无效输入，请输入一个数字。")

    # 获取其他通用信息
    problem["problemContent"] = get_required_input("请输入题干内容: ")
    problem["explanation"] = input("请输入题目解析 (选填): ").strip()

    return problem


def get_multiple_choice_details():
    """get the details specific to multiple choice questions."""
    details = {}
    options = []
    OPTIONS_KEYS = ["A", "B", "C", "D", "E", "F", "G"]

    while True:
        num_options_str = input(
            f"please select options number (2-{len(OPTIONS_KEYS)}): "
        ).strip()
        if num_options_str.isdigit() and 2 <= int(num_options_str) <= len(OPTIONS_KEYS):
            num_options = int(num_options_str)
            break
        else:
            print(f"error: please enter a number between 2 to {len(OPTIONS_KEYS)}.")

    print("\nplease enter the options:")
    for i in range(num_options):
        options_key = OPTIONS_KEYS[i]
        option_value = get_required_input(f"  选项 {options_key}: ")
        options.append({"key": options_key, "value": option_value})
    details["options"] = options

    print("\nplease enter the correct answer:")
    valid_keys = [opt["key"] for opt in options]
    while True:
        answer_key = (
            get_required_input(f"请输入正确答案的字母 ({', '.join(valid_keys)}): ")
            .strip()
            .upper()
        )
        if answer_key in valid_keys:
            details["answer"] = {"key": answer_key}
            break
        else:
            print(
                f"error: answer must be one of you options {valid_keys}, please try again."
            )
    return details


def main():
    print("--- 习题创建工具 ---")

    # 1. 获取通用信息
    new_problem = get_common_details()
    p_type = new_problem["problemType"]

    # 2. 使用字典映射来获取特定题型的信息，代码更优雅
    type_function_mapping = {
        "multiple_choice": get_multiple_choice_details,
        # "fill_in_the_blank": get_fill_in_the_blank_details,
        # "short_answer": get_short_answer_details
    }

    # 调用对应的函数
    details_function = type_function_mapping[p_type]
    type_specific_details = details_function()
    new_problem.update(type_specific_details)

    # 3. 自动生成ID和时间戳
    id_prefix = p_type.split("_")[0].upper()  # 例如 'multiple_choice' -> 'MULTIPLE'
    new_problem["problemId"] = f"{id_prefix}_{uuid.uuid4().hex[:8].upper()}"
    new_problem["createdAt"] = datetime.now().isoformat()

    # 4. 预览并确认保存
    print("\n--- 题目预览 ---")
    print(json.dumps(new_problem, indent=2, ensure_ascii=False))

    if input("\n是否确认保存? (y/n): ").lower() != "y":
        print("操作已取消，未做任何更改。")
        return

    # 5. 写入JSON文件 (重要：已修改为正确的结构)
    all_data = {"problems": [], "relationships": []}
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            try:
                content = f.read()
                if content:  # 确保文件不是空的
                    all_data = json.loads(content)
                    # 确保基本结构存在
                    if "problems" not in all_data:
                        all_data["problems"] = []
                    if "relationships" not in all_data:
                        all_data["relationships"] = []
            except json.JSONDecodeError:
                print(f"警告: 文件 '{JSON_FILE_PATH}' 格式无效，将创建新内容。")

    # 将新题目添加到 'problems' 列表中
    all_data["problems"].append(new_problem)

    with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 成功! 题目已保存至: {JSON_FILE_PATH}")


if __name__ == "__main__":
    main()

# test_app.py

from useless.app_logic import get_student_progress, update_node_mastery # 假设 add_student 也在里面

# 模拟流程
student_name = "Alice"
# student_id = add_student(student_name) # 假设 add_student 会返回新学生的ID, 我们先手动设为 1
student_id = 1 

# 1. 查看 Alice 最初的学习进度
print(f"--- Alice's Initial Progress ---")
initial_progress = get_student_progress(student_id)
for node in initial_progress:
    print(f"Topic: {node['topic']}, Status: {node['status']}")

# 2. 假设 Alice 学习并掌握了 "Matter" (node_id=1)
print("\n--- Alice is studying 'Matter' ---")
update_node_mastery(student_id=1, node_id=1, new_mastery_level='mastered')

# 3. 再次查看 Alice 的学习进度
print("\n--- Alice's Progress After Studying ---")
updated_progress = get_student_progress(student_id)
for node in updated_progress:
    print(f"Topic: {node['topic']}, Status: {node['status']}")
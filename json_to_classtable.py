import json

# 读取JSON文件
with open("wakeup课程表响应.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 提取课程表信息
courses = data["courses"]
schedule = data["schedule"]
time_table = data["timeTable"]

# 创建课程ID到课程名称的映射
course_id_to_name = {course["id"]: course["courseName"] for course in courses}

# 创建时间节点到时间段的映射
node_to_time = {
    node["node"]: (node["startTime"], node["endTime"]) for node in time_table
}

# 按周次和时间节点排序课程表
sorted_schedule = sorted(schedule, key=lambda x: (x["day"], x["startNode"]))

# 打印课程表
print("课程表:")
for entry in sorted_schedule:
    day = entry["day"]
    start_node = entry["startNode"]
    step = entry["step"]
    course_id = entry["id"]
    room = entry["room"]
    teacher = entry["teacher"]

    start_time, end_time = node_to_time[start_node]
    course_name = course_id_to_name[course_id]

    print(
        f"星期{day} {start_time}-{end_time} {course_name} ({room}) 授课教师: {teacher}"
    )

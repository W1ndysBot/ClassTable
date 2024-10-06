import json
from datetime import datetime


def parse_nested_json(data):
    # 提取嵌套的 JSON 字符串
    nested_json_str = data["data"]
    # 按换行符分割字符串
    parts = nested_json_str.split("\n")

    # 解析每个部分的 JSON 数据
    time_table = json.loads(parts[1])
    settings = json.loads(parts[2])
    courses = json.loads(parts[3])
    schedules = json.loads(parts[4])

    # 返回解析后的数据
    return {
        "timeTable": time_table,
        "settings": settings,
        "courses": courses,
        "schedule": schedules,
    }


def generate_course_schedule_from_data(data):
    data = parse_nested_json(data)
    courses = data["courses"]
    schedules = data["schedule"]
    time_table = data["timeTable"]
    settings = data["settings"]

    # 建立课程ID到课程信息的映射
    course_dict = {course["id"]: course for course in courses}

    # 建立节次到时间的映射
    node_time_dict = {item["node"]: item for item in time_table}

    # 获取开学日期和最大周数
    start_date_str = settings["startDate"]  # 开学日期，例如 "2024-8-26"
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    max_week = settings.get("maxWeek", 18)  # 默认18周

    # 生成完整的课程表数据
    course_schedule = []

    for schedule_item in schedules:
        course_id = schedule_item["id"]
        course_info = course_dict.get(course_id, {})
        start_node = schedule_item["startNode"]
        step = schedule_item["step"]
        day = schedule_item["day"]
        start_week = schedule_item["startWeek"]
        end_week = schedule_item["endWeek"]
        room = schedule_item["room"]
        teacher = schedule_item["teacher"]

        # 获取对应的课程名称
        course_name = course_info.get("courseName", "未知课程")

        # 获取上课的时间段
        class_times = []
        for i in range(step):
            node = start_node + i
            time_info = node_time_dict.get(
                node, {"startTime": "未知", "endTime": "未知"}
            )
            class_times.append(
                {
                    "node": node,
                    "startTime": time_info["startTime"],
                    "endTime": time_info["endTime"],
                }
            )

        # 将课程信息整合
        course_entry = {
            "courseId": course_id,
            "courseName": course_name,
            "day": day,
            "startWeek": start_week,
            "endWeek": end_week,
            "room": room,
            "teacher": teacher,
            "classTimes": class_times,
        }

        course_schedule.append(course_entry)

    # 按周次、星期和节次整理课程表
    weekly_schedule = {}

    for week in range(1, max_week + 1):
        weekly_schedule[week] = {}

    for entry in course_schedule:
        for week in range(entry["startWeek"], entry["endWeek"] + 1):
            if week > max_week:
                continue
            day = entry["day"]
            if day > 7:
                continue  # 忽略无效的星期
            if day not in weekly_schedule[week]:
                weekly_schedule[week][day] = {}
            for time in entry["classTimes"]:
                node = time["node"]
                if node not in weekly_schedule[week][day]:
                    weekly_schedule[week][day][node] = []
                weekly_schedule[week][day][node].append(
                    {
                        "courseId": entry["courseId"],
                        "courseName": entry["courseName"],
                        "room": entry["room"],
                        "teacher": entry["teacher"],
                        "startTime": time["startTime"],
                        "endTime": time["endTime"],
                    }
                )

    # 清理掉没有课程的周
    cleaned_weekly_schedule = {
        week: days for week, days in weekly_schedule.items() if days
    }

    return cleaned_weekly_schedule


# 示例调用
# with open("schedule.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# cleaned_schedule = generate_course_schedule_from_data(data)
# print(json.dumps(cleaned_schedule, ensure_ascii=False, indent=4))

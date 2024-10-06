import json
from datetime import datetime, timedelta


def print_schedule(schedule):
    for week, days in schedule.items():
        print(f"周次: {week}")
        for day, periods in days.items():
            print(f"  星期: {day}")
            for period, classes in periods.items():
                print(f"    节次: {period}")
                for course in classes:
                    print(f"      课程ID: {course['courseId']}")
                    print(f"      课程名称: {course['courseName']}")
                    print(f"      上课地点: {course['room']}")
                    print(f"      教师姓名: {course['teacher']}")
                    print(f"      开始时间: {course['startTime']}")
                    print(f"      结束时间: {course['endTime']}")
                    print()


def load_schedule_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_current_week(start_date, current_date):
    delta_days = (current_date - start_date).days
    current_week = delta_days // 7 + 1
    return str(current_week)


def check_for_reminders(schedule, start_date=datetime(2024, 8, 26), test_time=None):
    current_time = test_time or datetime.now()
    print(current_time)
    current_week = calculate_current_week(start_date, current_time)

    # 获取今天是星期几，Python的weekday()方法返回0-6，代表周一到周日
    current_day = str(current_time.weekday() + 1)  # 转换为1-7，代表周一到周日
    # print(f"当前星期: {current_day}")
    if current_week in schedule and current_day in schedule[current_week]:
        periods = schedule[current_week][current_day]
        for period, classes in periods.items():
            for course in classes:
                start_time_str = course["startTime"]
                start_time = datetime.strptime(start_time_str, "%H:%M")
                # 将日期设为今天，以便比较时间
                start_time = start_time.replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day,
                )
                # 计算时间差
                time_diff = start_time - current_time
                # 仅在时间差在29到30分钟之间时返回提醒
                if 29 * 60 <= time_diff.total_seconds() < 30 * 60:
                    return (
                        f"=========课程提醒=========\n"
                        + f"日期: {current_time.strftime('%Y-%m-%d')}\n"
                        + f"课程: {course['courseName']}\n"
                        + f"地点: {course['room']}\n"
                        + f"教师: {course['teacher']}\n"
                        + f"开始时间: {course['startTime']}\n"
                        + f"=========课程提醒=========\n"
                        + f"当前时间: {current_time.strftime('%H:%M')}\n"
                        + f"技术支持：W1ndys\n"
                    )
    return None  # 确保在没有符合条件的课程时返回None


# # 从文件加载课程表数据
# schedule_data = load_schedule_from_file("course_schedule.json")

# # 设置开学日期
# start_date = datetime(2024, 8, 26)

# # 打印课程表
# # print_schedule(schedule_data)

# # 设置测试时间（例如，设置为某个特定的时间）
# test_time = datetime.now().replace(hour=7, minute=30)

# # 使用测试时间进行提醒检查
# check_for_reminders(schedule_data, start_date, test_time)

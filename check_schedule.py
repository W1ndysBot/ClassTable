import json
from datetime import datetime
import logging


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


def check_for_reminders(user_id, group_id, schedule, start_date=datetime(2024, 8, 26)):

    # 当前时间
    current_time = datetime.now()

    current_week = calculate_current_week(start_date, current_time)

    # 获取今天是星期几，Python的weekday()方法返回0-6，代表周一到周日
    current_day = str(current_time.weekday() + 1)  # 转换为1-7，代表周一到周日

    if current_week in schedule and current_day in schedule[current_week]:
        periods = schedule[current_week][current_day]  # 获取当前星期的课程表
        for period, classes in periods.items():  # 遍历当前星期的所有课程
            for course in classes:

                # 检查当前课程是否在上课时间
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

                # 仅在29到30分钟之间时返回提醒
                if 29 * 60 <= time_diff.total_seconds() < 30 * 60:

                    # 检查当天上一节课是否与当前课程一样
                    previous_period = str(int(period) - 1)
                    if previous_period in periods:
                        previous_classes = periods[previous_period]
                        for previous_course in previous_classes:
                            if (
                                previous_course["courseName"] == course["courseName"]
                                and previous_course["room"] == course["room"]
                            ):
                                logging.info(
                                    f"[ClassTable]群{group_id}的{user_id}的上一节课：{previous_course}，与当前课程{course}相同，跳过提醒"
                                )
                                return None

                    logging.info(
                        f"[ClassTable]检测到群{group_id}的{user_id}即将开始{course['courseName']}"
                    )

                    return (
                        f"=========课程提醒=========\n"
                        + f"日期: {current_time.strftime('%Y-%m-%d')}\n"
                        + f"课程: {course['courseName']}\n"
                        + f"地点: {course['room']}\n"
                        + f"教师: {course['teacher']}\n"
                        + f"开始时间: {course['startTime']}\n"
                        + f"=========课程提醒=========\n"
                        + f"当前时间: {current_time.strftime('%H:%M')}"
                    )

    # logging.info(f"[ClassTable]群{group_id}的{user_id}没有符合条件的课程")
    return None  # 确保在没有符合条件的课程时返回None


def get_today_schedule(schedule, start_date=datetime(2024, 8, 26), test_time=None):
    current_time = test_time or datetime.now()
    current_week = calculate_current_week(start_date, current_time)
    current_day = str(current_time.weekday() + 1)

    result = ""

    if current_week in schedule and current_day in schedule[current_week]:
        periods = schedule[current_week][current_day]
        result += f"今日课表 (周次: {current_week}, 星期: {current_day}):\n"
        for period, classes in periods.items():
            # result += f"  节次: {period}\n"
            for course in classes:
                result += "====================\n"
                result += f"课程: {course['courseName']}\n"
                result += f"地点: {course['room']}\n"
                result += f"教师: {course['teacher']}\n"
                result += f"时间: {course['startTime']}-{course['endTime']}\n"
    else:
        result += "今日无课程安排。"

    return result


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

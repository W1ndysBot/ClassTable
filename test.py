import os
import json
from datetime import datetime
import logging

# 数据存储路径，实际开发时，请将ClassTable替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "ClassTable",
)


def load_schedule_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_current_week(start_date, current_date):
    delta_days = (current_date - start_date).days
    current_week = delta_days // 7 + 1
    return str(current_week)


def check_for_reminders(
    user_id,
    group_id,
    schedule,
    start_date=datetime(2024, 8, 26),
    test_time=datetime.now(),
):

    current_time = test_time

    current_week = calculate_current_week(start_date, current_time)

    # 获取今天是星期几，Python的weekday()方法返回0-6，代表周一到周日
    current_day = str(current_time.weekday() + 1)  # 转换为1-7，代表周一到周日

    # 调试信息
    print(f"当前周次: {current_week}")
    print(f"当前星期: {current_day}")
    print(f"当前时间: {current_time}")

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
                                print(
                                    f"[ClassTable]群{group_id}的{user_id}的上一节课：{previous_course}，与当前课程{course}相同，跳过提醒"
                                )
                                return None

                    print(
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
                        + f"当前时间: {current_time.strftime('%H:%M')}\n"
                        + f"技术支持：www.w1ndys.top"
                    )

    print(f"[ClassTable]群{group_id}的{user_id}没有符合条件的课程")
    return None  # 确保在没有符合条件的课程时返回None


def check_and_push_course_schedule():

    # 设置开学日期
    start_date = datetime(2024, 8, 26)
    user_id = "2769731875"
    group_id = "728077087"
    schedule_data = load_schedule_from_file(
        os.path.join(DATA_DIR, f"{group_id}_{user_id}.json")
    )
    test_time = datetime.now().replace(hour=13, minute=30)
    reminder_message = check_for_reminders(
        user_id, group_id, schedule_data, start_date, test_time
    )
    print(reminder_message)


check_and_push_course_schedule()

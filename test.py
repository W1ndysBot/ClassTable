import json
from datetime import datetime
import logging


def load_schedule_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def check_course_reminders(periods, current_time):
    for period, classes in periods.items():
        for course in classes:
            start_time_str = course["startTime"]
            start_time = datetime.strptime(start_time_str, "%H:%M")
            start_time = start_time.replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day,
            )
            time_diff = start_time - current_time

            if 29 * 60 <= time_diff.total_seconds() < 30 * 60:
                previous_period = str(int(period) - 1)
                if previous_period in periods:
                    previous_classes = periods[previous_period]
                    for previous_course in previous_classes:
                        logging.info(f"上一节课：{previous_course}")
                        logging.info(f"当前课程：{course}")
                        return None

                logging.info(f"检测到即将开始{course['courseName']}")
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
    return None


def main():
    # 自定义当前日期时间
    test_time = datetime(2024, 8, 26, 7, 30)  # 例如，2024年8月26日7:30

    # 从文件加载课程表数据
    schedule_data = load_schedule_from_file("temp.json")

    # 假设我们要测试某一周的某一天
    current_week = "1"  # 自定义周次
    current_day = "1"  # 自定义星期几，1代表周一

    if current_week in schedule_data and current_day in schedule_data[current_week]:
        periods = schedule_data[current_week][current_day]
        reminder = check_course_reminders(periods, test_time)
        if reminder:
            print(reminder)
        else:
            print("没有符合条件的课程提醒。")


if __name__ == "__main__":
    main()

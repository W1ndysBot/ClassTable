# script/ClassTable/main.py


import logging
import os
import sys

import re
import aiohttp
import json
import glob

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch
from app.scripts.ClassTable.json2weektable import *
from app.scripts.ClassTable.check_schedule import *

# 数据存储路径，实际开发时，请将ClassTable替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "ClassTable",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "function_status")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "function_status", status)


# 调用API返回json
async def get_course_schedule_from_api(share_code):

    url = f"https://i.wakeup.fun/share_schedule/get?key={share_code}"
    headers = {
        "User-Agent": "okhttp/3.14.9",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "version": "243",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            json_data = await response.json()
            return json_data


# 课程表菜单
async def classtable_menu(websocket, group_id, message_id):
    await send_group_msg(
        websocket,
        group_id,
        f"[CQ:reply,id={message_id}]本功能通过wakeup课程表APP的API抓包导入\n"
        + f"使用方法：\n"
        + f"1. 打开wakeup课程表APP，点击右上角第二个按钮，选择从分享口令导入\n"
        + f"2. 复制分享口令，发送在群里\n"
        + f"3. 卷卷会自动识别并导入课程表\n"
        + f"4. 导入成功后，卷卷会自动撤回分享口令\n"
        + f"取消订阅：发送“取消课程表订阅”或“classtableoff”\n"
        + f"查看今日课表：发送“今日课表”或“classtabletoday”\n",
    )


# 查看今日课表
async def check_today_course_schedule(websocket, user_id, group_id, message_id):
    try:
        # 正则匹配课表文件路径
        file_path_pattern = os.path.join(DATA_DIR, f"*{user_id}.json")

        # 读取第一个匹配的文件
        file_path = glob.glob(file_path_pattern)[0]

        # 加载课表数据
        schedule_data = load_schedule_from_file(file_path)

        # 设置开学日期
        start_date = datetime(2024, 8, 26)

        # 获取今日课表
        message = f"[CQ:reply,id={message_id}]"

        message += get_today_schedule(schedule_data, start_date, datetime.now())

        # 发送今日课表
        await send_group_msg(websocket, group_id, message)
    except IndexError:
        await send_group_msg(
            websocket, group_id, f"[CQ:reply,id={message_id}]未找到匹配的课表文件"
        )
    except FileNotFoundError:
        await send_group_msg(
            websocket, group_id, f"[CQ:reply,id={message_id}]课表文件不存在"
        )
    except Exception as e:
        await send_group_msg(
            websocket, group_id, f"[CQ:reply,id={message_id}]发生错误: {str(e)}"
        )


# 群消息处理函数
async def handle_ClassTable_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

        # 课程表菜单
        if raw_message == "classtable" or raw_message == "课程表":
            await classtable_menu(websocket, group_id, message_id)
            return

        # 查看今日课表
        if (
            raw_message == "查看今日课表"
            or raw_message == "今日课表"
            or raw_message == "classtabletoday"
        ):
            await check_today_course_schedule(websocket, user_id, group_id, message_id)
            return

        # 取消该群订阅
        if raw_message == "取消课程表订阅" or raw_message == "classtableoff":
            # 删除对应文件
            os.remove(os.path.join(DATA_DIR, f"{group_id}_{user_id}.json"))
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]已取消订阅课程表",
            )
            return

        # 添加课程表
        if raw_message.startswith(
            "这是来自「WakeUp课程表」的课表分享，30分钟内有效哦，如果失效请朋友再分享一遍叭。为了保护隐私我们选择不监听你的剪贴板，请复制这条消息后，打开App的主界面，右上角第二个按钮 -> 从分享口令导入，按操作提示即可完成导入~分享口令为「"
        ):
            # 撤回消息
            await delete_msg(websocket, message_id)

            # 发出检测到分享口令的提示
            await send_group_msg_with_reply(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}][+]检测到分享口令，正在请求API，为避免口令泄露，请确定自行撤回分享口令",
            )

            # 提取分享口令
            match = re.search(
                r"这是来自「WakeUp课程表」的课表分享，30分钟内有效哦，如果失效请朋友再分享一遍叭。为了保护隐私我们选择不监听你的剪贴板，请复制这条消息后，打开App的主界面，右上角第二个按钮 -> 从分享口令导入，按操作提示即可完成导入~分享口令为「(.*)」",
                raw_message,
            )
            if match:

                logging.info(f"提取到{user_id}在{group_id}的分享口令: {match.group(1)}")

                share_code = match.group(1)

                # 异步调用API返回json
                json_data = await get_course_schedule_from_api(share_code)

                if (
                    json_data["status"] == "1"
                    and json_data["message"] == "success"
                    and json_data["data"] != ""
                ):

                    # 将json数据转换为课程表
                    course_schedule = generate_course_schedule_from_data(json_data)

                    # 保存课程表到文件
                    with open(
                        os.path.join(DATA_DIR, f"{group_id}_{user_id}.json"),
                        "w",
                        encoding="utf-8",
                    ) as file:
                        json.dump(course_schedule, file, ensure_ascii=False, indent=4)

                    logging.info(f"保存课程表到文件完成")

                    share_code = (
                        share_code[:2] + "*" * (len(share_code) - 4) + share_code[-2:]
                    )

                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]导入课程表成功，重复导入将会覆盖之前的数据，你的分享口令是{share_code}",
                    )

                else:
                    logging.warning(f"导入课程表失败: {json_data}")
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]导入课程表失败，请检查分享口令是否正确或是否已过期，如果确定分享口令正确，请稍后再试\n\n"
                        + f"错误返回值: {json_data}",
                    )

    except Exception as e:
        logging.error(f"处理ClassTable群消息失败: {e}")
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]课程表功能处理失败，请联系开发者处理，发送“owner”联系开发者QQ\n\n"
            + f"错误信息: {e}",
        )

        return


# 定时监控推送函数
async def check_and_push_course_schedule(websocket):

    # 设置开学日期
    start_date = datetime(2024, 8, 26)

    # 设置测试时间（例如，设置为某个特定的时间）
    # test_time = datetime.now().replace(hour=13, minute=45)

    # 遍历所有保存的文件
    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            # 解析文件名，提取群号和QQ号
            group_id = file.split("_")[0]
            user_id = file.split("_")[1].split(".")[0]

            file_path = os.path.join(DATA_DIR, file)
            schedule_data = load_schedule_from_file(file_path)

            logging.info(f"加载{user_id}在{group_id}的课程表完成")

            reminder_message = check_for_reminders(
                user_id, group_id, schedule_data, start_date
            )

            if reminder_message:
                reminder_message = f"[CQ:at,qq={user_id}]\n" + reminder_message
                await send_group_msg(websocket, group_id, reminder_message)

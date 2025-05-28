# script/ClassTable/main.py


import logging
import os
import sys

import re
import aiohttp
import json
from datetime import datetime, timedelta


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

# 设置开学日期为全局常量
SEMESTER_START_DATE = datetime(2025, 2, 17)


# 调用API返回json
async def get_course_schedule_from_api(share_code):

    url = f"https://i.wakeup.fun/share_schedule/get?key={share_code}"
    headers = {
        "User-Agent": "okhttp/3.14.9",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "version": "243",
    }
    timeout = aiohttp.ClientTimeout(total=5)  # 设置超时时间为5秒

    async with aiohttp.ClientSession(timeout=timeout) as session:
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
        + f"1. 打开wakeup课程表APP，点击右上角按钮\n"
        + f"2. 复制分享口令，全部内容直接发送在群里\n"
        + f"3. 卷卷会自动识别并导入课程表\n"
        + f"4. 导入成功后，卷卷会自动撤回分享口令\n"
        + f"取消订阅：发送【取消课程表订阅】或【classtableoff】\n"
        + f"查看今日课表：发送【今日课表】或【classtabletoday】\n",
    )


# 查看今日课表
async def check_today_course_schedule(websocket, user_id, group_id, message_id):
    try:
        # 正则匹配课表文件路径
        file_path = os.path.join(DATA_DIR, f"{group_id}_{user_id}.json")

        # 加载课表数据
        schedule_data = load_schedule_from_file(file_path)

        # 获取今日课表
        message = f"[CQ:reply,id={message_id}]"

        message += get_today_schedule(
            schedule_data, SEMESTER_START_DATE, datetime.now()
        )

        # 发送今日课表
        await send_group_msg(websocket, group_id, message)
    except IndexError:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]未找到群 {group_id} 的 {user_id} 的课表文件，发送【classtable】或【课程表】查看说明",
        )
    except FileNotFoundError:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]群 {group_id} 的 {user_id} 的课表文件不存在，发送【classtable】或【课程表】查看说明",
        )
    except Exception as e:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]读取群 {group_id} 的 {user_id} 的课表文件发生错误: {str(e)}\n\n发送【classtable】或【课程表】查看说明",
        )


# 查看指定日期课表
async def check_date_course_schedule(
    websocket, user_id, group_id, message_id, date_offset
):
    try:
        file_path = os.path.join(DATA_DIR, f"{group_id}_{user_id}.json")
        schedule_data = load_schedule_from_file(file_path)

        # 计算目标日期
        target_date = datetime.now() + timedelta(days=date_offset)

        # 获取日期描述
        date_desc = {-2: "前日", -1: "昨日", 0: "今日", 1: "明日", 2: "后日"}[
            date_offset
        ]

        message = f"[CQ:reply,id={message_id}]{date_desc}({target_date.strftime('%Y-%m-%d')})课表：\n"
        message += get_today_schedule(schedule_data, SEMESTER_START_DATE, target_date)

        await send_group_msg(websocket, group_id, message)
    except IndexError:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]未找到群 {group_id} 的 {user_id} 的课表文件，发送【classtable】或【课程表】查看说明",
        )
    except FileNotFoundError:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]群 {group_id} 的 {user_id} 的课表文件不存在，发送【classtable】或【课程表】查看说明",
        )
    except Exception as e:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]读取群 {group_id} 的 {user_id} 的课表文件发生错误: {str(e)}\n\n发送【classtable】或【课程表】查看说明",
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

        # 查看不同日期的课表
        date_commands = {
            "前日课表": -2,
            "昨日课表": -1,
            "今日课表": 0,
            "明日课表": 1,
            "后日课表": 2,
            "classtableyesterday": -1,
            "classtabletoday": 0,
            "classtabletomorrow": 1,
        }

        if raw_message in date_commands:
            await check_date_course_schedule(
                websocket, user_id, group_id, message_id, date_commands[raw_message]
            )
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

            # 提取分享口令
            match = re.search(
                r"这是来自「WakeUp课程表」的课表分享，30分钟内有效哦，如果失效请朋友再分享一遍叭。为了保护隐私我们选择不监听你的剪贴板，请复制这条消息后，打开App的主界面，右上角第二个按钮 -> 从分享口令导入，按操作提示即可完成导入~分享口令为「(.*)」",
                raw_message,
            )
            if match:

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

                    share_code = (
                        share_code[:2] + "*" * (len(share_code) - 4) + share_code[-2:]
                    )

                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]导入课程表成功，重复导入将会覆盖之前的数据，你的分享口令是{share_code}\n\n"
                        + f"支持的命令：\n"
                        + f"取消订阅：发送【取消课程表订阅】或【classtableoff】\n"
                        + f"查看今日课表：发送【今日课表】或【classtabletoday】\n"
                        + f"查看指定日期课表：发送【前日课表】或【昨日课表】或【今日课表】或【明日课表】或【后日课表】\n",
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
            f"[CQ:reply,id={message_id}]课程表功能处理失败，可能是wakeup课程表APP的服务器问题，请联系开发者处理，发送【owner】联系开发者QQ\n\n"
            + f"错误信息: {e}",
        )

        return


# 定时监控推送函数
async def check_and_push_course_schedule(websocket):
    # 整十分钟执行
    if datetime.now().minute % 10 != 0:
        return

    # 遍历所有保存的文件
    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            file_path = os.path.join(DATA_DIR, file)

            # 解析文件名
            if "_" in file:  # 群聊格式：group_id_user_id.json
                group_id = file.split("_")[0]
                user_id = file.split("_")[1].split(".")[0]

                schedule_data = load_schedule_from_file(file_path)
                reminder_message = check_for_reminders(
                    user_id, group_id, schedule_data, SEMESTER_START_DATE
                )

                if reminder_message:
                    reminder_message = f"[CQ:at,qq={user_id}]({user_id})\n" + reminder_message
                    await send_group_msg(websocket, group_id, reminder_message)

            else:  # 私聊格式：user_id.json
                user_id = file.split(".")[0]

                schedule_data = load_schedule_from_file(file_path)
                reminder_message = check_for_reminders(
                    user_id, None, schedule_data, SEMESTER_START_DATE
                )

                if reminder_message:
                    await send_private_msg(websocket, user_id, reminder_message)


# 处理私聊消息函数
async def handle_ClassTable_private_message(websocket, msg):
    try:
        user_id = str(msg.get("user_id"))
        raw_message = str(msg.get("raw_message"))
        message_id = str(msg.get("message_id"))

        # 通知owner的函数
        async def notify_owner(action):
            if user_id == owner_id[0]:
                return
            await send_private_msg(
                websocket,
                owner_id[0],
                f"用户 {user_id} 在私聊中{action}",
            )

        # 课程表菜单
        if raw_message == "classtable" or raw_message == "课程表":
            await send_private_msg(
                websocket,
                user_id,
                f"[CQ:reply,id={message_id}]本功能通过wakeup课程表APP的API抓包导入\n"
                + f"使用方法：\n"
                + f"1. 打开wakeup课程表APP，点击右上角按钮\n"
                + f"2. 复制分享口令，全部内容直接发送给我\n"
                + f"3. 我会自动识别并导入课程表\n"
                + f"4. 导入成功后，我会自动撤回分享口令\n"
                + f"取消订阅：发送【取消课程表订阅】或【classtableoff】\n"
                + f"查看今日课表：发送【今日课表】或【classtabletoday】\n",
            )
            await notify_owner("查看了课程表菜单")
            return

        # 查看不同日期的课表
        date_commands = {
            "前日课表": -2,
            "昨日课表": -1,
            "今日课表": 0,
            "明日课表": 1,
            "后日课表": 2,
            "classtableyesterday": -1,
            "classtabletoday": 0,
            "classtabletomorrow": 1,
        }

        if raw_message in date_commands:
            try:
                file_path = os.path.join(DATA_DIR, f"{user_id}.json")
                schedule_data = load_schedule_from_file(file_path)

                target_date = datetime.now() + timedelta(
                    days=date_commands[raw_message]
                )
                date_desc = {-2: "前日", -1: "昨日", 0: "今日", 1: "明日", 2: "后日"}[
                    date_commands[raw_message]
                ]

                message = f"[CQ:reply,id={message_id}]{date_desc}({target_date.strftime('%Y-%m-%d')})课表：\n"
                message += get_today_schedule(
                    schedule_data, SEMESTER_START_DATE, target_date
                )

                await send_private_msg(websocket, user_id, message)
                await notify_owner(f"查看了{date_desc}课表")
            except (IndexError, FileNotFoundError):
                await send_private_msg(
                    websocket,
                    user_id,
                    f"[CQ:reply,id={message_id}]未找到你的课表文件，发送【classtable】或【课程表】查看说明",
                )
                await notify_owner("尝试查看课表失败：未找到课表文件")
            return

        # 取消订阅
        if raw_message == "取消课程表订阅" or raw_message == "classtableoff":
            try:
                os.remove(os.path.join(DATA_DIR, f"{user_id}.json"))
                await send_private_msg(
                    websocket,
                    user_id,
                    f"[CQ:reply,id={message_id}]已取消订阅课程表",
                )
                await notify_owner("取消了课程表订阅")
            except FileNotFoundError:
                await send_private_msg(
                    websocket,
                    user_id,
                    f"[CQ:reply,id={message_id}]你还没有订阅课程表",
                )
                await notify_owner("尝试取消订阅失败：未找到课表文件")
            return

        # 添加课程表
        if raw_message.startswith("这是来自「WakeUp课程表」的课表分享，30分钟内有效哦"):
            # 提取分享口令
            match = re.search(r"分享口令为「(.*)」", raw_message)
            if match:
                share_code = match.group(1)
                json_data = await get_course_schedule_from_api(share_code)

                if (
                    json_data["status"] == "1"
                    and json_data["message"] == "success"
                    and json_data["data"] != ""
                ):
                    course_schedule = generate_course_schedule_from_data(json_data)

                    with open(
                        os.path.join(DATA_DIR, f"{user_id}.json"),
                        "w",
                        encoding="utf-8",
                    ) as file:
                        json.dump(course_schedule, file, ensure_ascii=False, indent=4)

                    masked_share_code = (
                        share_code[:2] + "*" * (len(share_code) - 4) + share_code[-2:]
                    )

                    await send_private_msg(
                        websocket,
                        user_id,
                        f"[CQ:reply,id={message_id}]导入课程表成功，重复导入将会覆盖之前的数据，你的分享口令是{masked_share_code}\n\n"
                        + f"支持的命令：\n"
                        + f"取消订阅：发送【取消课程表订阅】或【classtableoff】\n"
                        + f"查看今日课表：发送【今日课表】或【classtabletoday】\n"
                        + f"查看指定日期课表：发送【前日课表】或【昨日课表】或【今日课表】或【明日课表】或【后日课表】\n",
                    )
                    await notify_owner(f"导入了新的课程表，分享码：{masked_share_code}")
                else:
                    logging.warning(f"导入课程表失败: {json_data}")
                    await send_private_msg(
                        websocket,
                        user_id,
                        f"[CQ:reply,id={message_id}]导入课程表失败，请检查分享口令是否正确或是否已过期\n\n"
                        + f"错误返回值: {json_data}",
                    )
                    await notify_owner("尝试导入课表失败：API返回错误")

    except Exception as e:
        error_msg = f"处理ClassTable私聊消息失败: {e}"
        logging.error(error_msg)
        await send_private_msg(
            websocket,
            user_id,
            f"课程表功能处理失败，请联系开发者处理，发送【owner】联系开发者QQ\n\n"
            + f"错误信息: {e}",
        )
        await send_private_msg(
            websocket,
            owner_id,
            f"用户 {user_id} 使用课程表功能时发生错误：\n{error_msg}",
        )


# 统一事件处理入口
async def handle_events(websocket, msg):
    """统一事件处理入口"""
    post_type = msg.get("post_type", "response")
    try:
        if msg.get("status") == "ok":
            return

        post_type = msg.get("post_type")

        if post_type == "meta_event":
            await check_and_push_course_schedule(websocket)
            return
        elif post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await handle_ClassTable_group_message(websocket, msg)
            elif message_type == "private":
                await handle_ClassTable_private_message(websocket, msg)
        elif post_type == "notice":
            return

    except Exception as e:
        error_type = {
            "message": "消息",
            "notice": "通知",
            "request": "请求",
            "meta_event": "元事件",
        }.get(post_type, "未知")

        logging.error(f"处理ClassTable{error_type}事件失败: {e}")

        # 发送错误提示
        if post_type == "message":
            message_type = msg.get("message_type")
            if message_type == "group":
                await send_group_msg(
                    websocket,
                    msg.get("group_id"),
                    f"处理ClassTable{error_type}事件失败，错误信息：{str(e)}",
                )
            elif message_type == "private":
                await send_private_msg(
                    websocket,
                    msg.get("user_id"),
                    f"处理ClassTable{error_type}事件失败，错误信息：{str(e)}",
                )

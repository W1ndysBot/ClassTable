# ClassTable

本功能通过 wakeup 课程表 APP 的 API 抓包导入，如需订阅提醒请把你的 wakeup 课程表分享链接发到群里，卷卷会自动识别并调用导入，如需取消订阅，请发送“取消课程表订阅”或“classtableoff”

## 更新日志

### 2024-11-05

- feat: 新增测试文件，便于调试
- fix: 修复上一节课与当前课程相同时，判断出错的问题——fix by @Giant_GKL and @W1ndys
- feat: 新增判断上下节课是否一致对于教室的判断
- feat: 删除全文件匹配课程表的设置，改为指定群内文件

### 2024-10-24

- feat: 新增查看今日课表功能
- fix: 修复加载课表文件失败时，未返回错误信息的问题
- fix: 增加异常捕获，返回错误信息

### 2024-10-23

- feat: 把课表文件名格式改为群号\_QQ 号.json
- feat: 删除多条提示信息

### 2024-10-18

- feat: 新增读取到课程表之后，删除分享口令消息，避免口令泄露
- feat: 新增课程表导入成功之后，多条提示消息
- feat: 优化 API 请求，异步请求，防止堵塞
- feat: 新增测试代码，便于调试

### 2024-10-15

- feat: 在时间差在 59 到 60 分钟和 25 到 26 分钟之间时返回提醒
- fix: 调整代码逻辑顺序，修复部分课程提醒失败的问题

### 2024-10-8

- feat: 由于 wakeup 课程表以小节次为单位，增加对上一节课的检查，避免大课节次重复提醒

### 2024-10-7

- feat: 历时三个小时，完成课程提醒功能

# 培训网自动学习辅助工具

> 内部使用工具，请勿公开传播

## 适用网站
- www.chinapeixun.org.cn（培训网）

## v2.0 新功能
- ✅ 三种Cookie粘贴方式都支持（纯值/完整格式/整段字符串）
- ✅ 网络请求自动重试3次，波动不中断
- ✅ JSON解析容错，服务器异常不崩溃
- ✅ 整体进度统计，显示总章节数
- ✅ 支持 HH:MM:SS 时间格式
- ✅ Ctrl+C 优雅退出
- ✅ 依赖自动检查，缺少库友好提示

## 功能
- 自动获取账号下所有课程
- 自动遍历每门课程的所有章节
- 按顺序完成视频学习进度上报
- 自动解锁下一章
- 实时显示学习进度

## 使用前提
1. 已在网站购买并开通课程
2. 已完成人脸验证，能正常登录
3. Python 3.6+ 环境

## 快速开始

### 1. 安装依赖
```bash
pip install requests
```

### 2. 获取Cookie
1. 浏览器登录 https://www.chinapeixun.org.cn
2. 按 F12 → Application → Cookies → 点击域名
3. 找到 PHPSESSID，复制它的 Value 值

**三种粘贴方式都支持：**
- 只粘贴值：`bfs7okhp1i31kvfcnom5f2f22t`
- 完整格式：`PHPSESSID=bfs7okhp1i31kvfcnom5f2f22t`
- 整段Cookie：`PHPSESSID=xxx; play_token=yyy; ...`

### 3. 运行脚本
```bash
python3 training_course_auto_complete.py
```

### 4. 粘贴Cookie
按提示粘贴Cookie，回车即可开始自动学习。

## 文件说明
| 文件 | 说明 |
|------|------|
| `training_course_auto_complete.py` | 主程序脚本 |
| `使用说明.md` | 详细使用文档 |

## 常见问题

**Q: 提示"未找到课程"怎么办？**
A: 说明Cookie已过期或无效。请重新登录网站，再复制新的PHPSESSID。

**Q: 运行中途中断了怎么办？**
A: 直接重新运行即可，服务器端已记录的进度会自动跳过。

**Q: 提示"被锁定"怎么办？**
A: 说明章节顺序错乱了，脚本会自动按顺序解锁，不需要手动处理。

## 注意事项
- Cookie有时效性，过期后需要重新获取
- 脚本内置0.5秒延时，避免请求过快
- 请遵守网站相关规定，合理使用

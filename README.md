# 培训网自动学习辅助工具

> 内部使用工具，请勿公开传播

## 适用网站
- www.chinapeixun.org.cn（培训网）

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
2. 按 F12 打开开发者工具
3. Console 输入 `document.cookie`，复制输出内容

### 3. 运行脚本
```bash
python3 training_course_auto_complete.py
```

### 4. 粘贴Cookie
按提示粘贴刚才复制的Cookie字符串，回车即可开始自动学习。

## 文件说明
| 文件 | 说明 |
|------|------|
| `training_course_auto_complete.py` | 主程序脚本 |
| `使用说明.md` | 详细使用文档 |

## 注意事项
- Cookie有时效性，过期后需要重新获取
- 脚本内置延时，避免请求过快
- 请遵守网站相关规定，合理使用

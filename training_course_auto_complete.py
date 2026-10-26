#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
培训网自动刷课脚本
适用网站：www.chinapeixun.org.cn
"""

import sys
import time

# 检查依赖
try:
    import requests
except ImportError:
    print("❌ 缺少依赖库 requests")
    print("请先运行：pip install requests")
    input("按回车退出...")
    sys.exit(1)

import re


class TrainingCourseAutoComplete:
    def __init__(self, cookies_str):
        self.base_url = "https://www.chinapeixun.org.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self._parse_cookies(cookies_str)

    def _parse_cookies(self, cookies_str):
        """解析Cookie字符串，支持三种输入格式"""
        cookies_str = cookies_str.strip()

        # 智能识别：纯字符串自动当作PHPSESSID
        if '=' not in cookies_str and len(cookies_str) > 10:
            print(f"  ℹ️  检测到纯Cookie值，自动识别为PHPSESSID")
            self.session.cookies.set('PHPSESSID', cookies_str)
            return

        # 解析 key=value; key2=value2 格式
        for item in cookies_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                self.session.cookies.set(key.strip(), value.strip())

    def _request(self, method, url, **kwargs):
        """带重试的请求封装"""
        kwargs.setdefault('timeout', 15)
        kwargs.setdefault('allow_redirects', True)

        for retry in range(3):
            try:
                if method == 'GET':
                    resp = self.session.get(url, **kwargs)
                else:
                    resp = self.session.post(url, **kwargs)
                resp.encoding = 'utf-8'
                return resp
            except requests.exceptions.RequestException as e:
                if retry < 2:
                    wait = (retry + 1) * 2
                    print(f"  ⚠️  请求失败，{wait}秒后重试 ({retry+1}/3)...")
                    time.sleep(wait)
                else:
                    raise

    def _parse_time_to_seconds(self, time_str):
        """把时间字符串转成秒，支持 MM:SS 和 HH:MM:SS"""
        parts = time_str.split(':')
        parts = [int(p) for p in parts]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return 0

    def get_my_courses(self):
        """获取我的课程列表"""
        try:
            resp = self._request('GET', f"{self.base_url}/member/home.html")
        except Exception as e:
            print(f"  ❌ 网络错误：{e}")
            return []

        # 检查登录状态
        if 'login.html' in resp.url or '用户登录' in resp.text:
            print("  ⚠️  未检测到登录状态，Cookie可能已过期")
            return []

        courses = []
        # 匹配课程链接和名称
        pattern = r'href="/course/show/ids/(\d+)\.html"[^>]*>.*?<p><a href="/course/show/ids/\d+\.html">(.*?)</a></p>'
        matches = re.findall(pattern, resp.text, re.DOTALL)

        for match in matches:
            course_id = match[0]
            course_name = match[1].strip()
            courses.append({'id': course_id, 'name': course_name})

        return courses

    def get_course_sections(self, course_id):
        """获取课程的所有章节"""
        try:
            resp = self._request('GET', f"{self.base_url}/course/play/model_cid/{course_id}.html")
        except Exception as e:
            print(f"  ❌ 网络错误：{e}")
            return []

        sections = []
        pattern = r'id="ts-(\d+)">([0-9:]+)</i>/([0-9:]+)'
        matches = re.findall(pattern, resp.text)

        for match in matches:
            section_id = match[0]
            total_time = match[2]
            total_seconds = self._parse_time_to_seconds(total_time)

            sections.append({
                'id': section_id,
                'total_time': total_time,
                'total_seconds': total_seconds
            })

        return sections

    def complete_section(self, course_id, section_id, total_seconds):
        """完成单个章节的学习"""
        try:
            # 1. 访问播放页面，获取新Cookie
            play_url = f"{self.base_url}/course/play/model_cid/{course_id}/term_id/{section_id}.html"
            resp = self._request('GET', play_url)

            # 检查是否被锁定
            if "请先完成上一章节" in resp.text:
                return False, "被锁定（需按顺序学习）"

            # 2. 上报学习进度
            data = {'ts': total_seconds}
            resp = self._request('POST', f"{self.base_url}/course/synchronous.html", data=data)

            try:
                result = resp.json()
            except ValueError:
                return False, f"服务器返回异常（非JSON）"

            if result.get('code') != 200:
                return False, f"进度上报失败: {result.get('msg', result)}"

            # 3. 解锁下一章
            resp = self._request('POST', f"{self.base_url}/course/get_next_course.html", data=data)

            try:
                next_result = resp.json()
            except ValueError:
                return True, "进度已上报（解锁接口异常）"

            if next_result.get('code') == 201:
                return True, "🎉 课程全部完成！"
            elif next_result.get('code') == 200:
                return True, "成功"
            else:
                return True, f"完成（解锁返回: {next_result.get('msg', '未知')}）"

        except Exception as e:
            return False, f"异常: {e}"

    def run(self):
        """主运行函数"""
        print("=" * 60)
        print("培训网自动刷课工具")
        print("=" * 60)

        # 1. 获取课程列表
        print("\n[1/3] 正在获取我的课程列表...")
        courses = self.get_my_courses()

        if not courses:
            print("❌ 未找到任何课程，请检查：")
            print("   1. Cookie是否正确、是否已过期")
            print("   2. 是否在浏览器能正常看到\"我的课程\"")
            print("   3. 账号下是否已购买课程")
            return

        print(f"✅ 找到 {len(courses)} 门课程：")
        for i, course in enumerate(courses, 1):
            print(f"   {i}. {course['name']}")

        # 统计总章节数
        total_sections = 0
        for course in courses:
            sections = self.get_course_sections(course['id'])
            course['sections'] = sections
            total_sections += len(sections)

        print(f"\n📚 共 {total_sections} 个章节需要完成")

        completed = 0

        # 2. 遍历每门课程
        for course_idx, course in enumerate(courses, 1):
            course_id = course['id']
            course_name = course['name']
            sections = course['sections']

            print(f"\n{'─' * 60}")
            print(f"[{course_idx}/{len(courses)}] 课程：{course_name}")
            print(f"   共 {len(sections)} 个章节")
            print(f"{'─' * 60}")

            if not sections:
                print("   ⚠️  未找到章节，跳过")
                continue

            # 3. 遍历每个章节
            for sec_idx, section in enumerate(sections, 1):
                section_id = section['id']
                total_seconds = section['total_seconds']
                total_time = section['total_time']

                completed += 1
                progress = completed * 100 // total_sections

                print(f"   [{sec_idx}/{len(sections)}] 章节 {section_id} ({total_time})...", end=" ")

                success, msg = self.complete_section(course_id, section_id, total_seconds)

                if success:
                    print(f"✓ {msg}")
                else:
                    print(f"✗ {msg}")

                # 间隔，避免请求过快
                time.sleep(0.5)

                if "全部完成" in msg:
                    break

        print(f"\n{'=' * 60}")
        print(f"✅ 全部处理完成！共处理 {completed} 个章节")
        print(f"{'=' * 60}")


def main():
    print("=" * 50)
    print("培训网自动刷课工具")
    print("=" * 50)
    print()
    print("【获取Cookie方法】")
    print("1. 浏览器登录 www.chinapeixun.org.cn")
    print("2. 按 F12 → Application → Cookies → 点击域名")
    print("3. 找到 PHPSESSID，复制它的 Value 值")
    print()
    print("【三种粘贴方式都支持】")
    print("  ✓ 只粘贴值：bfs7okhp1i31kvfcnom5f2f22t")
    print("  ✓ 完整格式：PHPSESSID=bfs7okhp1i31kvfcnom5f2f22t")
    print("  ✓ 整段Cookie：PHPSESSID=xxx; play_token=yyy; ...")
    print("-" * 50)

    cookies = input("请粘贴Cookie: ").strip()

    if not cookies:
        print("❌ Cookie不能为空")
        input("按回车退出...")
        return

    print()
    try:
        bot = TrainingCourseAutoComplete(cookies)
        bot.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户手动中断")
    except Exception as e:
        print(f"\n❌ 运行出错：{e}")
        import traceback
        traceback.print_exc()

    input("\n按回车退出...")


if __name__ == "__main__":
    main()

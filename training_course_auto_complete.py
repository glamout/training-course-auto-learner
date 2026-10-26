#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
培训网自动刷课脚本
适用网站：www.chinapeixun.org.cn
使用方法：
1. 登录网站后，从浏览器复制PHPSESSID等Cookie
2. 运行脚本，输入Cookie
3. 脚本自动完成所有课程的学习
"""

import requests
import re
import time
import sys

class TrainingCourseAutoComplete:
    def __init__(self, cookies_str):
        self.base_url = "https://www.chinapeixun.org.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        # 解析Cookie字符串
        self._parse_cookies(cookies_str)
        
    def _parse_cookies(self, cookies_str):
        """解析Cookie字符串并设置到session中"""
        cookies_str = cookies_str.strip()
        
        # 智能识别：如果输入不包含=号，说明用户只复制了PHPSESSID的值
        if '=' not in cookies_str and len(cookies_str) > 10:
            print(f"  ℹ️  检测到只粘贴了Cookie值，自动识别为PHPSESSID")
            self.session.cookies.set('PHPSESSID', cookies_str)
            return
        
        # 正常解析 key=value; key2=value2 格式
        for item in cookies_str.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                self.session.cookies.set(key.strip(), value.strip())
    
    def get_my_courses(self):
        """获取我的课程列表"""
        url = f"{self.base_url}/member/home.html"
        resp = self.session.get(url, allow_redirects=True)
        resp.encoding = 'utf-8'
        
        # 调试：检查是否被重定向到登录页
        if 'login.html' in resp.url or '用户登录' in resp.text:
            print("  ⚠️  检测到未登录状态，Cookie可能已过期或无效")
            return []
        
        # 提取课程链接和名称
        courses = []
        # 匹配课程链接
        pattern = r'href="/course/show/ids/(\d+)\.html"[^>]*>.*?<p><a href="/course/show/ids/\d+\.html">(.*?)</a></p>'
        matches = re.findall(pattern, resp.text, re.DOTALL)
        
        for match in matches:
            course_id = match[0]
            course_name = match[1].strip()
            courses.append({
                'id': course_id,
                'name': course_name
            })
        
        return courses
    
    def get_course_sections(self, course_id):
        """获取课程的所有章节"""
        # 先访问课程播放页面，获取章节列表
        url = f"{self.base_url}/course/play/model_cid/{course_id}.html"
        resp = self.session.get(url)
        resp.encoding = 'utf-8'
        
        # 提取章节ID和时长
        sections = []
        # 匹配 ts-章节ID > 时长
        pattern = r'id="ts-(\d+)">([0-9:]+)</i>/([0-9:]+)'
        matches = re.findall(pattern, resp.text)
        
        for match in matches:
            section_id = match[0]
            current_time = match[1]
            total_time = match[2]
            
            # 转换时长为秒
            minutes, seconds = total_time.split(':')
            total_seconds = int(minutes) * 60 + int(seconds)
            
            sections.append({
                'id': section_id,
                'total_time': total_time,
                'total_seconds': total_seconds
            })
        
        return sections
    
    def complete_section(self, course_id, section_id, total_seconds):
        """完成单个章节的学习"""
        # 1. 访问播放页面，获取新的Cookie（section_id和play_token）
        play_url = f"{self.base_url}/course/play/model_cid/{course_id}/term_id/{section_id}.html"
        resp = self.session.get(play_url)
        
        # 检查是否被锁定
        if "请先完成上一章节" in resp.text:
            return False, "被锁定"
        
        # 2. 上报学习进度
        sync_url = f"{self.base_url}/course/synchronous.html"
        data = {'ts': total_seconds}
        resp = self.session.post(sync_url, data=data)
        result = resp.json()
        
        if result.get('code') != 200:
            return False, f"进度上报失败: {result}"
        
        # 3. 解锁下一章
        next_url = f"{self.base_url}/course/get_next_course.html"
        resp = self.session.post(next_url, data=data)
        next_result = resp.json()
        
        if next_result.get('code') == 201:
            return True, "课程全部完成"
        elif next_result.get('code') == 200:
            return True, "成功"
        else:
            return True, f"完成（解锁结果: {next_result}）"
    
    def run(self):
        """主运行函数"""
        print("=" * 60)
        print("培训网自动刷课脚本")
        print("=" * 60)
        
        # 1. 获取课程列表
        print("\n[1/3] 正在获取我的课程列表...")
        courses = self.get_my_courses()
        
        if not courses:
            print("未找到课程，请检查Cookie是否有效")
            return
        
        print(f"找到 {len(courses)} 门课程：")
        for i, course in enumerate(courses, 1):
            print(f"  {i}. {course['name']} (ID: {course['id']})")
        
        # 2. 遍历每门课程
        for course_idx, course in enumerate(courses, 1):
            course_id = course['id']
            course_name = course['name']
            
            print(f"\n{'='*60}")
            print(f"[{course_idx}/{len(courses)}] 正在处理课程：{course_name}")
            print(f"{'='*60}")
            
            # 获取章节列表
            print("正在获取章节列表...")
            sections = self.get_course_sections(course_id)
            
            if not sections:
                print("  未找到章节")
                continue
            
            print(f"共 {len(sections)} 个章节")
            
            # 3. 遍历每个章节
            for sec_idx, section in enumerate(sections, 1):
                section_id = section['id']
                total_seconds = section['total_seconds']
                total_time = section['total_time']
                
                print(f"  [{sec_idx}/{len(sections)}] 章节 {section_id} ({total_time})...", end=" ")
                
                success, msg = self.complete_section(course_id, section_id, total_seconds)
                
                if success:
                    print(f"✓ {msg}")
                else:
                    print(f"✗ {msg}")
                
                # 间隔一下，避免请求太快
                time.sleep(0.5)
                
                if "课程全部完成" in msg:
                    break
        
        print(f"\n{'='*60}")
        print("全部课程处理完成！")
        print(f"{'='*60}")

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
    print("【两种粘贴方式都可以】")
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
    bot = TrainingCourseAutoComplete(cookies)
    bot.run()
    
    input("\n按回车退出...")

if __name__ == "__main__":
    main()

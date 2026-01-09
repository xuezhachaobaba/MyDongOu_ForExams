#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试时间安排系统
功能：根据用户选择的天数和科目，自动生成考试时间安排表
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import sys

class ExamScheduler:
    def __init__(self):
        # 考试时长配置（分钟）
        self.EXAM_DURATION = {
            '语文': 150,
            '数学': 120,
            '外语': 120,
            '物理': 90,
            '化学': 90,
            '生物': 90,
            '历史': 90,
            '地理': 90,
            '政治': 90,
            '技术': 90
        }

        # 时间段配置 (开始时间, 结束时间)
        self.TIME_SLOTS = {
            '上午': ('07:30', '12:00'),
            '下午': ('13:30', '17:25'),
            '晚上': ('19:30', '21:00')
        }

        # 考试间隔时间（分钟）
        self.EXAM_INTERVAL = 20

    def calculate_slot_duration(self, slot_name: str) -> int:
        """计算时间段可用总时长（分钟）"""
        start_str, end_str = self.TIME_SLOTS[slot_name]
        start = datetime.strptime(start_str, '%H:%M')
        end = datetime.strptime(end_str, '%H:%M')
        return int((end - start).total_seconds() / 60)

    def time_str_to_datetime(self, time_str: str) -> datetime:
        """将时间字符串转换为datetime对象"""
        return datetime.strptime(time_str, '%H:%M')

    def datetime_to_time_str(self, dt: datetime) -> str:
        """将datetime对象转换为时间字符串"""
        return dt.strftime('%H:%M')

    def arrange_exams_in_slot(self, subjects: List[str], slot_name: str, date_str: str) -> List[Dict]:
        """在指定时间段内安排考试"""
        arrangements = []

        if not subjects:
            return arrangements

        start_str, end_str = self.TIME_SLOTS[slot_name]
        current_time = self.time_str_to_datetime(start_str)
        end_time = self.time_str_to_datetime(end_str)

        for subject in subjects:
            duration = self.EXAM_DURATION[subject]
            exam_end_time = current_time + timedelta(minutes=duration)

            # 检查是否超出时间段
            if exam_end_time > end_time:
                print(f"警告：科目 {subject} 无法在 {date_str} {slot_name} 完成安排，时间不足")
                break

            arrangements.append({
                'date': date_str,
                'time_slot': slot_name,
                'subject': subject,
                'start_time': self.datetime_to_time_str(current_time),
                'end_time': self.datetime_to_time_str(exam_end_time),
                'duration': duration
            })

            # 更新当前时间（加上考试时长和间隔）
            current_time = exam_end_time + timedelta(minutes=self.EXAM_INTERVAL)

        return arrangements

    def get_available_subjects(self) -> List[str]:
        """获取所有可选科目"""
        return list(self.EXAM_DURATION.keys())

    def generate_schedule(self, days: int, daily_subjects: Dict[str, Dict[str, List[str]]]) -> List[Dict]:
        """生成完整考试安排"""
        full_schedule = []

        for day_idx in range(days):
            date_str = f"第{day_idx + 1}天"
            if date_str not in daily_subjects:
                continue

            day_schedule = []
            for slot_name in ['上午', '下午', '晚上']:
                if slot_name in daily_subjects[date_str]:
                    subjects = daily_subjects[date_str][slot_name]
                    slot_arrangements = self.arrange_exams_in_slot(subjects, slot_name, date_str)
                    day_schedule.extend(slot_arrangements)

            full_schedule.extend(day_schedule)

        return full_schedule

    def display_schedule(self, schedule: List[Dict]):
        """显示考试安排表"""
        print("\n" + "="*80)
        print("考试时间安排表".center(80))
        print("="*80)
        print(f"{'日期':<8} {'时间段':<8} {'科目':<8} {'开始时间':<10} {'结束时间':<10} {'时长(分钟)':<10}")
        print("-"*80)

        for exam in schedule:
            print(f"{exam['date']:<8} {exam['time_slot']:<8} {exam['subject']:<8} "
                  f"{exam['start_time']:<10} {exam['end_time']:<10} {exam['duration']:<10}")

        print("="*80)

    def interactive_mode(self):
        """交互式模式"""
        print("欢迎使用考试时间安排系统")
        print("="*50)

        # 选择考试天数
        while True:
            try:
                days = int(input("请输入考试天数（1-7天）："))
                if 1 <= days <= 7:
                    break
                else:
                    print("请输入1-7之间的数字")
            except ValueError:
                print("请输入有效的数字")

        print(f"\n可选择的科目：{', '.join(self.get_available_subjects())}")
        print("时间段：上午(7:30-12:00)、下午(13:30-17:25)、晚上(19:30-21:00)")

        daily_subjects = {}

        # 为每天安排科目
        for day_idx in range(days):
            date_str = f"第{day_idx + 1}天"
            daily_subjects[date_str] = {}

            print(f"\n=== {date_str} ===")

            for slot_name in ['上午', '下午', '晚上']:
                print(f"\n{slot_name}时间段（可用时长：{self.calculate_slot_duration(slot_name)}分钟）")

                while True:
                    subject_input = input(f"请输入{slot_name}要考试的科目（用逗号分隔，输入'无'表示不安排）：").strip()

                    if subject_input.lower() == '无':
                        daily_subjects[date_str][slot_name] = []
                        break

                    subjects = [s.strip() for s in subject_input.split(',') if s.strip()]

                    # 验证科目
                    invalid_subjects = [s for s in subjects if s not in self.EXAM_DURATION]
                    if invalid_subjects:
                        print(f"无效科目：{', '.join(invalid_subjects)}，请重新输入")
                        continue

                    # 检查时间是否足够
                    total_duration = sum(self.EXAM_DURATION[s] for s in subjects)
                    total_time = total_duration + (len(subjects) - 1) * self.EXAM_INTERVAL
                    available_time = self.calculate_slot_duration(slot_name)

                    if total_time > available_time:
                        print(f"时间不足！需要{total_time}分钟，但只有{available_time}分钟可用")
                        continue

                    daily_subjects[date_str][slot_name] = subjects
                    break

        # 生成并显示安排
        schedule = self.generate_schedule(days, daily_subjects)
        self.display_schedule(schedule)

        # 询问是否保存
        save_choice = input("\n是否保存到文件？(y/n): ").strip().lower()
        if save_choice == 'y':
            self.save_to_file(schedule)

    def save_to_file(self, schedule: List[Dict], filename: str = None):
        """保存安排到文件"""
        import os
        if filename is None:
            os.makedirs("process_data", exist_ok=True)
            filename = os.path.join("process_data", "考试安排表.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("考试时间安排表\n".center(80))
                f.write("="*80 + "\n")
                f.write(f"{'日期':<8} {'时间段':<8} {'科目':<8} {'开始时间':<10} {'结束时间':<10} {'时长(分钟)':<10}\n")
                f.write("-"*80 + "\n")

                for exam in schedule:
                    f.write(f"{exam['date']:<8} {exam['time_slot']:<8} {exam['subject']:<8} "
                           f"{exam['start_time']:<10} {exam['end_time']:<10} {exam['duration']:<10}\n")

                f.write("="*80 + "\n")

            print(f"安排表已保存到 {filename}")
        except Exception as e:
            print(f"保存失败：{e}")

def main():
    scheduler = ExamScheduler()

    while True:
        print("\n" + "="*40)
        print("考试时间安排系统")
        print("="*40)
        print("1. 开始安排考试")
        print("2. 查看科目时长配置")
        print("3. 退出")

        choice = input("请选择操作（1-3）：").strip()

        if choice == '1':
            scheduler.interactive_mode()
        elif choice == '2':
            print("\n科目考试时长配置：")
            for subject, duration in scheduler.EXAM_DURATION.items():
                print(f"  {subject}：{duration}分钟")
        elif choice == '3':
            print("谢谢使用！")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
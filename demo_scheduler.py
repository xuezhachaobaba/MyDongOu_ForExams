#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考试时间安排系统演示脚本
展示如何使用ExamScheduler类
"""

from exam_scheduler import ExamScheduler

def demo():
    """演示考试安排系统的使用"""
    print("="*80)
    print("考试时间安排系统演示")
    print("="*80)

    scheduler = ExamScheduler()

    # 示例：3天考试安排
    days = 3
    print(f"\n演示：安排{days}天考试")
    print("\n科目考试时长：")
    for subject, duration in scheduler.EXAM_DURATION.items():
        print(f"  {subject}：{duration}分钟")

    print("\n时间段配置：")
    for slot, (start, end) in scheduler.TIME_SLOTS.items():
        duration = scheduler.calculate_slot_duration(slot)
        print(f"  {slot}：{start}-{end}（可用{duration}分钟）")

    # 模拟用户输入的考试安排
    daily_subjects = {
        "第1天": {
            "上午": ["语文"],
            "下午": ["数学"],
            "晚上": []
        },
        "第2天": {
            "上午": ["外语"],
            "下午": ["物理", "化学"],
            "晚上": ["技术"]
        },
        "第3天": {
            "上午": ["历史", "地理"],
            "下午": ["生物", "政治"],
            "晚上": []
        }
    }

    print("\n模拟的考试安排：")
    for day, slots in daily_subjects.items():
        print(f"\n{day}:")
        for slot, subjects in slots.items():
            if subjects:
                total_time = sum(scheduler.EXAM_DURATION[s] for s in subjects) + (len(subjects) - 1) * scheduler.EXAM_INTERVAL
                print(f"  {slot}：{', '.join(subjects)}（总计{total_time}分钟）")

    # 生成考试安排
    schedule = scheduler.generate_schedule(days, daily_subjects)

    # 显示结果
    scheduler.display_schedule(schedule)

    # 保存到文件
    scheduler.save_to_file(schedule, "演示考试安排表.txt")

    print("\n" + "="*80)
    print("演示完成！")
    print("使用方法：")
    print("1. 运行 python3 exam_scheduler.py")
    print("2. 按照提示输入考试天数")
    print("3. 为每天的时间段输入要考试的科目")
    print("4. 查看生成的考试安排表")
    print("5. 可选择保存到文件")
    print("="*80)

if __name__ == "__main__":
    demo()
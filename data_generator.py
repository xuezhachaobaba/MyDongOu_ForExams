"""
数据生成器
用于生成测试用的排考数据
"""
import random
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

from models import (
    Teacher, Room, TimeSlot, Exam, SubjectType, ExamMode,
    Assignment, ConstraintConfig, ExamSchedule
)


class DataGenerator:
    """测试数据生成器"""

    def __init__(self, seed: int = 42):
        random.seed(seed)

    def generate_teachers(self, count: int = 400) -> List[Teacher]:
        """生成教师列表"""
        subjects = list(SubjectType)
        grades = ["高一", "高二", "高三"]
        teachers = []

        for i in range(count):
            teacher = Teacher(
                id=i + 1,
                name=f"老师{i+1:03d}",
                subject=random.choice(subjects),
                grade=random.choice(grades),
                historical_load=random.uniform(100, 500)  # 历史负荷随机生成
            )

            # 生成授课时间表 (简化版本)
            self._generate_teaching_schedule(teacher)

            # 随机生成请假时间
            if random.random() < 0.1:  # 10%的教师有请假
                self._generate_leave_time(teacher)

            # 随机生成固定坐班
            if random.random() < 0.15:  # 15%的教师有固定坐班
                self._generate_fixed_duty(teacher)

            teachers.append(teacher)

        return teachers

    def _generate_teaching_schedule(self, teacher: Teacher):
        """生成教师授课时间表"""
        # 简化版本：每天可能有1-3节课
        days = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]
        time_slots = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节", "第8节", "第9节"]

        for day in days:
            daily_slots = random.sample(time_slots, random.randint(1, 3))
            teacher.teaching_schedule[day] = daily_slots

    def _generate_leave_time(self, teacher: Teacher):
        """生成请假时间"""
        days = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]
        time_slots = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节", "第8节", "第9节"]

        day = random.choice(days)
        slot = random.choice(time_slots)
        teacher.leave_times.append((day, slot))

    def _generate_fixed_duty(self, teacher: Teacher):
        """生成固定坐班"""
        days = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]

        day = random.choice(days)
        slot = "第9节"  # 通常固定坐班在第9节
        room_id = random.randint(1, 100)
        teacher.fixed_duties.append((day, slot, f"房间{room_id:03d}"))

    def generate_rooms(self, count: int = 100) -> List[Room]:
        """生成考场列表"""
        rooms = []
        buildings = ["教学楼A", "教学楼B", "教学楼C", "实验楼", "综合楼"]

        for i in range(count):
            building = random.choice(buildings)
            floor = str(random.randint(1, 6))

            room = Room(
                id=i + 1,
                name=f"{building}{floor}0{i % 10 + 1:02d}",
                capacity=random.choice([30, 40, 50]),
                building=building,
                floor=floor
            )
            rooms.append(room)

        return rooms

    def generate_time_slots(self, days: int = 5) -> List[TimeSlot]:
        """生成时间段列表"""
        time_slots = []
        start_date = datetime(2024, 1, 15)

        # 上午时段
        morning_slots = [
            ("第1场", "08:00", "09:30"),
            ("第2场", "10:00", "11:30")
        ]

        # 下午时段
        afternoon_slots = [
            ("第3场", "14:00", "15:30"),
            ("第4场", "16:00", "17:30")
        ]

        slot_counter = 1

        for day in range(days):
            current_date = start_date + timedelta(days=day)
            date_str = current_date.strftime("%Y-%m-%d")

            # 上午时段
            for i, (name, start, end) in enumerate(morning_slots):
                duration = self._calculate_duration(start, end)

                time_slot = TimeSlot(
                    id=f"{date_str}_上午_{name}",
                    name=f"{date_str} {name}",
                    date=date_str,
                    start_time=start,
                    end_time=end,
                    duration_minutes=duration,
                    is_morning=True,
                    is_afternoon=False
                )
                time_slots.append(time_slot)
                slot_counter += 1

            # 下午时段
            for i, (name, start, end) in enumerate(afternoon_slots):
                duration = self._calculate_duration(start, end)

                time_slot = TimeSlot(
                    id=f"{date_str}_下午_{name}",
                    name=f"{date_str} {name}",
                    date=date_str,
                    start_time=start,
                    end_time=end,
                    duration_minutes=duration,
                    is_morning=False,
                    is_afternoon=True
                )
                time_slots.append(time_slot)
                slot_counter += 1

        # 设置午休配对
        self._set_lunch_pairs(time_slots)

        return time_slots

    def _calculate_duration(self, start: str, end: str) -> int:
        """计算时间段时长（分钟）"""
        start_hour, start_min = map(int, start.split(":"))
        end_hour, end_min = map(int, end.split(":"))

        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min

        return end_minutes - start_minutes

    def _set_lunch_pairs(self, time_slots: List[TimeSlot]):
        """设置午休配对关系"""
        # 按日期分组
        slots_by_date = {}
        for slot in time_slots:
            if slot.date not in slots_by_date:
                slots_by_date[slot.date] = []
            slots_by_date[slot.date].append(slot)

        # 为每一天的上午最后一场和下午第一场设置配对
        for date, daily_slots in slots_by_date.items():
            morning_slots = [s for s in daily_slots if s.is_morning]
            afternoon_slots = [s for s in daily_slots if s.is_afternoon]

            if morning_slots and afternoon_slots:
                # 上午最后一场配对下午第一场
                last_morning = max(morning_slots, key=lambda x: x.start_time)
                first_afternoon = min(afternoon_slots, key=lambda x: x.start_time)
                last_morning.is_lunch_pair_with = first_afternoon.id
                first_afternoon.is_lunch_pair_with = last_morning.id

    def generate_exams(self, subjects: List[SubjectType], time_slots: List[TimeSlot],
                      rooms: List[Room], rooms_per_exam: int = 20,
                      exam_mode: ExamMode = ExamMode.SHUFFLED) -> List[Exam]:
        """生成考试列表"""
        exams = []

        # 长时科目定义
        long_subjects = {SubjectType.CHINESE, SubjectType.MATH, SubjectType.ENGLISH}

        for i, subject in enumerate(subjects):
            # 每个科目分配一个时间段
            if i >= len(time_slots):
                break

            time_slot = time_slots[i]

            # 选择考场
            selected_rooms = random.sample(rooms, min(rooms_per_exam, len(rooms)))

            exam = Exam(
                subject=subject,
                time_slot=time_slot,
                rooms=selected_rooms,
                is_long_subject=(subject in long_subjects)
            )
            exams.append(exam)

        return exams

    def generate_schedule(self, teacher_count: int = 400, exam_subjects: List[SubjectType] = None,
                         rooms_per_exam: int = 20) -> ExamSchedule:
        """生成完整的考试安排数据"""
        if exam_subjects is None:
            exam_subjects = list(SubjectType)[:10]  # 默认10个科目

        # 生成基础数据
        teachers = self.generate_teachers(teacher_count)
        rooms = self.generate_rooms(100)  # 生成100个考场
        time_slots = self.generate_time_slots(5)  # 5天考试

        # 生成考试安排
        exams = self.generate_exams(exam_subjects, time_slots, rooms, rooms_per_exam)

        # 创建考试安排对象
        schedule = ExamSchedule(
            teachers=teachers,
            rooms=rooms,
            time_slots=time_slots,
            exams=exams,
            config=ConstraintConfig()  # 使用默认配置
        )

        return schedule

    def create_small_test_case(self) -> ExamSchedule:
        """创建小型测试用例"""
        subjects = [SubjectType.CHINESE, SubjectType.MATH, SubjectType.PHYSICS]
        return self.generate_schedule(
            teacher_count=50,
            exam_subjects=subjects,
            rooms_per_exam=5
        )

    def create_medium_test_case(self) -> ExamSchedule:
        """创建中型测试用例"""
        subjects = list(SubjectType)[:5]
        return self.generate_schedule(
            teacher_count=200,
            exam_subjects=subjects,
            rooms_per_exam=10
        )

    def create_large_test_case(self) -> ExamSchedule:
        """创建大型测试用例（接近实际规模）"""
        subjects = list(SubjectType)
        return self.generate_schedule(
            teacher_count=400,
            exam_subjects=subjects,
            rooms_per_exam=20
        )


def main():
    """测试数据生成器"""
    generator = DataGenerator()

    # 生成大型测试用例
    schedule = generator.create_large_test_case()

    print(f"生成了大型测试用例:")
    print(f"教师数量: {len(schedule.teachers)}")
    print(f"考场数量: {len(schedule.rooms)}")
    print(f"时间段数量: {len(schedule.time_slots)}")
    print(f"考试数量: {len(schedule.exams)}")

    # 显示每个考试的信息
    for exam in schedule.exams:
        print(f"考试: {exam.subject.value}, 时间: {exam.time_slot.id}, "
              f"考场数: {exam.get_total_rooms()}, 长时科目: {exam.is_long_subject}")


if __name__ == "__main__":
    main()
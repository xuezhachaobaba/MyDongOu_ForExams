"""
基础数据生成器
生成400个教师和20个考场的基础信息，供系统使用
"""
import random
import json
from typing import List, Dict
from models import Teacher, Room, SubjectType


class BasicDataGenerator:
    """基础数据生成器"""

    def __init__(self, seed=42):
        random.seed(seed)
        self.subjects = list(SubjectType)
        self.grades = ["高一", "高二", "高三"]
        self.buildings = ["教学楼A", "教学楼B", "教学楼C", "实验楼", "综合楼"]

    def generate_teachers(self, count: int = 400) -> List[Teacher]:
        """生成教师数据"""
        teachers = []

        # 按科目平均分配教师
        teachers_per_subject = count // len(self.subjects)
        remaining = count % len(self.subjects)

        teacher_id = 1
        for i, subject in enumerate(self.subjects):
            # 每个科目的教师数量
            subject_count = teachers_per_subject + (1 if i < remaining else 0)

            for j in range(subject_count):
                grade = self.grades[j % len(self.grades)]

                # 生成历史负荷（基于经验）
                experience_years = random.randint(1, 30)
                historical_load = 100 + experience_years * 10 + random.uniform(-50, 50)

                teacher = Teacher(
                    id=teacher_id,
                    name=f"{subject.value[:2]}老师{teacher_id:03d}",
                    subject=subject,
                    grade=grade,
                    historical_load=historical_load
                )

                # 生成授课时间表
                self._generate_teaching_schedule(teacher)

                # 随机生成请假和固定任务
                self._generate_teacher_constraints(teacher)

                teachers.append(teacher)
                teacher_id += 1

        return teachers

    def _generate_teaching_schedule(self, teacher: Teacher):
        """生成授课时间表"""
        days = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]
        time_slots = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节", "第8节", "第9节"]

        for day in days:
            # 每天安排1-3节课
            daily_slots = random.sample(time_slots, random.randint(1, 3))
            teacher.teaching_schedule[day] = daily_slots

    def _generate_teacher_constraints(self, teacher: Teacher):
        """生成教师约束条件"""
        # 10%的教师有请假
        if random.random() < 0.1:
            days = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]
            time_slots = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节", "第8节", "第9节"]

            leave_day = random.choice(days)
            leave_slot = random.choice(time_slots)
            teacher.leave_times.append((leave_day, leave_slot))

        # 15%的教师有固定坐班
        if random.random() < 0.15:
            days = ["2024-01-15", "2024-01-16", "2024-01-17", "2024-01-18", "2024-01-19"]

            duty_day = random.choice(days)
            duty_slot = "第9节"  # 通常晚上
            teacher.fixed_duties.append((duty_day, duty_slot, f"房间{random.randint(1, 100):03d}"))

    def generate_rooms(self, count: int = 20) -> List[Room]:
        """生成考场数据"""
        rooms = []

        for i in range(1, count + 1):
            building = self.buildings[(i-1) % len(self.buildings)]
            floor = str(((i-1) % 15) // 3 + 1)  # 每栋楼5层

            # 根据楼层和建筑确定容量
            if building == "实验楼":
                capacity = random.choice([25, 30])  # 实验室容量较小
            elif floor in ["1", "2"]:
                capacity = random.choice([50, 55])  # 低层大教室
            else:
                capacity = random.choice([35, 40, 45])  # 普通教室

            room = Room(
                id=i,
                name=f"{building}{floor}0{i % 10 + 1:02d}",
                capacity=capacity,
                building=building,
                floor=floor
            )
            rooms.append(room)

        return rooms

    def save_to_files(self, teachers: List[Teacher], rooms: List[Room],
                    teacher_file: str = "teachers.json",
                    room_file: str = "rooms.json"):
        """保存数据到文件"""
        # 保存教师数据
        teacher_data = []
        for teacher in teachers:
            teacher_dict = {
                'id': teacher.id,
                'name': teacher.name,
                'subject': teacher.subject.value,
                'grade': teacher.grade,
                'historical_load': teacher.historical_load,
                'teaching_schedule': teacher.teaching_schedule,
                'leave_times': teacher.leave_times,
                'fixed_duties': teacher.fixed_duties
            }
            teacher_data.append(teacher_dict)

        with open(teacher_file, 'w', encoding='utf-8') as f:
            json.dump(teacher_data, f, ensure_ascii=False, indent=2)

        # 保存考场数据
        room_data = []
        for room in rooms:
            room_dict = {
                'id': room.id,
                'name': room.name,
                'capacity': room.capacity,
                'building': room.building,
                'floor': room.floor
            }
            room_data.append(room_dict)

        with open(room_file, 'w', encoding='utf-8') as f:
            json.dump(room_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 已生成 {len(teachers)} 名教师数据 → {teacher_file}")
        print(f"✅ 已生成 {len(rooms)} 个考场数据 → {room_file}")


def main():
    """生成基础数据"""
    generator = BasicDataGenerator(seed=42)

    # 生成400个教师
    teachers = generator.generate_teachers(400)
    print(f"生成教师数据完成，共 {len(teachers)} 名教师")

    # 生成20个考场
    rooms = generator.generate_rooms(20)
    print(f"生成考场数据完成，共 {len(rooms)} 个考场")

    # 保存到文件
    generator.save_to_files(teachers, rooms, "basic_teachers.json", "basic_rooms.json")

    # 显示示例数据
    print("\n📊 教师数据示例：")
    print(json.dumps(teachers[0].__dict__, default=str, ensure_ascii=False, indent=2))

    print("\n🏢 考场数据示例：")
    print(json.dumps(rooms[0].__dict__, default=str, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
"""
数据格式转换器
将exam_scheduler.py的考试安排结果转换为智能排考系统所需的完整数据格式
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

from models import (
    Teacher, Room, TimeSlot, Exam, SubjectType,
    Assignment, ConstraintConfig, ExamSchedule, ExamMode
)


@dataclass
class ConversionConfig:
    """转换配置"""
    # 基础参数
    student_count_per_class: int = 40        # 每班学生数
    classes_per_grade: int = 10              # 每个年级班数
    teachers_per_subject: int = 8            # 每科教师数

    # 时间参数
    exam_interval_minutes: int = 20          # 考试间隔
    lunch_start_time: str = "12:00"        # 午休开始
    lunch_end_time: str = "14:00"           # 午休结束

    # 考场配置
    room_capacity_small: int = 30            # 小考场容量
    room_capacity_medium: int = 40           # 中考场容量
    room_capacity_large: int = 50           # 大考场容量

    # 教师配置
    historical_load_min: float = 100.0       # 最低历史负荷
    historical_load_max: float = 500.0       # 最高历史负荷
    teaching_load_ratio: float = 0.3          # 授课负荷比例

    # 分配策略
    room_allocation_strategy: str = "grade_based"  # grade_based, random, capacity_based
    teacher_distribution_strategy: str = "balanced"  # balanced, random, experienced


class ScheduleConverter:
    """考试安排到排考系统的数据转换器"""

    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()
        random.seed(42)  # 确保可重现性

        # 内部数据
        self.exam_schedule = []
        self.teachers = []
        self.rooms = []
        self.time_slots = []
        self.exams = []

        # 映射表
        self.subject_name_mapping = {
            "语文": SubjectType.CHINESE,
            "数学": SubjectType.MATH,
            "英语": SubjectType.ENGLISH,
            "外语": SubjectType.ENGLISH,
            "物理": SubjectType.PHYSICS,
            "化学": SubjectType.CHEMISTRY,
            "生物": SubjectType.BIOLOGY,
            "历史": SubjectType.HISTORY,
            "地理": SubjectType.GEOGRAPHY,
            "政治": SubjectType.POLITICS,
            "技术": SubjectType.SCIENCE
        }

        self.long_subjects = {
            SubjectType.CHINESE, SubjectType.MATH, SubjectType.ENGLISH
        }

        # 时间段配置模板
        self.time_slot_templates = {
            "上午": {
                "start": "07:30",
                "end": "09:40",   # 第一场
                "alt_start": "10:00",
                "alt_end": "11:30"   # 第二场
            },
            "下午": {
                "start": "14:00",
                "end": "15:30",   # 第一场
                "alt_start": "15:50",
                "alt_end": "17:20"    # 第二场
            },
            "晚上": {
                "start": "19:30",
                "end": "21:00"    # 只有一场
            }
        }

    def convert(self, exam_schedule: List[Dict[str, Any]],
               base_date: str = "2024-01-15",
               pre_generated_teachers=None,
               pre_generated_rooms=None) -> ExamSchedule:
        """
        将考试安排转换为完整的ExamSchedule

        Args:
            exam_schedule: exam_scheduler.py生成的考试安排列表
            base_date: 基础日期，用于计算具体日期
            pre_generated_teachers: 预生成的教师数据
            pre_generated_rooms: 预生成的考场数据

        Returns:
            完整的ExamSchedule对象
        """
        print("开始转换考试安排数据...")
        self.exam_schedule = exam_schedule

        # Step 1: 分析考试安排，提取基本信息
        exam_info = self._analyze_exam_schedule()
        print(f"发现 {exam_info['total_exams']} 场考试，涉及 {exam_info['total_days']} 天")

        # Step 2: 生成时间段
        self._generate_time_slots(base_date)
        print(f"生成 {len(self.time_slots)} 个时间段")

        # Step 3: 使用预生成考场或生成考场
        if pre_generated_rooms:
            print("使用预生成的考场数据...")
            self.rooms = pre_generated_rooms
        else:
            print("生成考场数据...")
            self._generate_rooms(exam_info)
        print(f"考场数量: {len(self.rooms)}")

        # Step 4: 使用预生成教师或生成教师
        if pre_generated_teachers:
            print("使用预生成的教师数据...")
            self.teachers = pre_generated_teachers
        else:
            print("生成教师数据...")
            self._generate_teachers(exam_info)
        print(f"教师数量: {len(self.teachers)}")

        # Step 5: 转换考试对象
        self._convert_exams()
        print(f"转换 {len(self.exams)} 个考试对象")

        # Step 6: 创建ExamSchedule
        schedule = ExamSchedule(
            teachers=self.teachers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            exams=self.exams,
            assignments=[],
            config=ConstraintConfig()
        )

        # Step 7: 验证转换结果
        self._validate_conversion(schedule)

        print("数据转换完成！")
        return schedule

    def _analyze_exam_schedule(self) -> Dict[str, Any]:
        """分析考试安排，提取统计信息"""
        subjects = set()
        days = set()
        time_slots_count = {}

        for exam in self.exam_schedule:
            subjects.add(exam['subject'])
            days.add(exam['date'])
            key = (exam['date'], exam['time_slot'])
            time_slots_count[key] = time_slots_count.get(key, 0) + 1

        return {
            'total_exams': len(self.exam_schedule),
            'unique_subjects': list(subjects),
            'total_days': len(days),
            'time_slots_count': time_slots_count,
            'max_exams_per_slot': max(time_slots_count.values()) if time_slots_count else 1
        }

    def _generate_time_slots(self, base_date: str):
        """根据考试安排生成精确的时间段"""
        self.time_slots = []
        base_dt = datetime.strptime(base_date, "%Y-%m-%d")

        # 🔧 修复：直接为每个考试创建独立时间段
        slot_id = 1
        used_time_slots = {}  # 避免重复时间段

        for exam in self.exam_schedule:
            # 计算实际日期
            date_str = exam['date']
            day_num = int(date_str.replace('第', '').replace('天', ''))
            actual_date = (base_dt + timedelta(days=day_num-1)).strftime("%Y-%m-%d")

            # 使用真实的考试时间
            start_time = exam['start_time']
            end_time = exam['end_time']

            # 🔧 修复：生成唯一的时间段名称
            period = exam['time_slot']

            # 创建基于实际时间的唯一标识
            exam_key = f"{actual_date}_{period}_{start_time.replace(':', '')}-{end_time.replace(':', '')}"

            if exam_key not in used_time_slots:
                # 🔧 修复：使用真实的考试时间，不是模板时间
                time_slot = self._create_time_slot(
                    slot_id=slot_id,
                    date=actual_date,
                    name=f"{period}_{start_time}-{end_time}",  # 使用时间范围作为唯一标识
                    start_time=start_time,  # 使用真实的开始时间
                    end_time=end_time,       # 使用真实的结束时间
                    is_morning=(period == "上午"),
                    is_afternoon=(period == "下午")
                )
                self.time_slots.append(time_slot)
                used_time_slots[exam_key] = True
                slot_id += 1
                print(f"  创建时间段: {actual_date} {period} {start_time}-{end_time}")
            else:
                print(f"  跳过重复时间段: {exam_key}")

        # 设置午休配对
        self._setup_lunch_pairs()

    def _create_time_slot(self, slot_id: int, date: str, name: str,
                        start_time: str, end_time: str,
                        is_morning: bool, is_afternoon: bool) -> TimeSlot:
        """创建时间段对象"""
        duration = self._calculate_duration(start_time, end_time)

        return TimeSlot(
            id=f"{date}_{name}",
            name=f"{date} {name}",
            date=date,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration,
            is_morning=is_morning,
            is_afternoon=is_afternoon
        )

    def _calculate_duration(self, start: str, end: str) -> int:
        """计算时间差（分钟）"""
        start_hour, start_min = map(int, start.split(":"))
        end_hour, end_min = map(int, end.split(":"))

        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min

        return end_minutes - start_minutes

    def _setup_lunch_pairs(self):
        """设置午休配对关系"""
        # 按日期查找上午最后一场和下午第一场
        date_slots = {}
        for slot in self.time_slots:
            if slot.date not in date_slots:
                date_slots[slot.date] = {"morning": [], "afternoon": []}

            if slot.is_morning:
                date_slots[slot.date]["morning"].append(slot)
            elif slot.is_afternoon:
                date_slots[slot.date]["afternoon"].append(slot)

        # 配对上午最后一场和下午第一场
        for date, slots in date_slots.items():
            if slots["morning"] and slots["afternoon"]:
                last_morning = max(slots["morning"], key=lambda x: x.start_time)
                first_afternoon = min(slots["afternoon"], key=lambda x: x.start_time)

                last_morning.is_lunch_pair_with = first_afternoon.id
                first_afternoon.is_lunch_pair_with = last_morning.id

    def _generate_rooms(self, exam_info: Dict[str, Any]):
        """生成考场"""
        self.rooms = []
        room_id = 1

        # 根据考试规模确定考场数量
        total_classes = len(exam_info['unique_subjects']) * exam_info['total_days'] * 2
        total_students = total_classes * self.config.student_count_per_class
        estimated_rooms_needed = max(20, total_students // self.config.room_capacity_medium)

        # 按建筑物分布考场
        buildings = ["教学楼A", "教学楼B", "教学楼C", "实验楼", "综合楼"]

        for building in buildings:
            for floor in range(1, 6):  # 1-5层
                for room_num in range(1, 5):  # 每层4个考场
                    if room_id > estimated_rooms_needed:
                        break

                    # 根据楼层和建筑确定容量
                    if building == "实验楼":
                        capacity = self.config.room_capacity_small
                    elif floor <= 2:
                        capacity = self.config.room_capacity_large
                    else:
                        capacity = self.config.room_capacity_medium

                    room = Room(
                        id=room_id,
                        name=f"{building}{floor}0{room_num:02d}",
                        capacity=capacity,
                        building=building,
                        floor=str(floor)
                    )
                    self.rooms.append(room)
                    room_id += 1

                if room_id > estimated_rooms_needed:
                    break

    def _generate_teachers(self, exam_info: Dict[str, Any]):
        """生成教师"""
        self.teachers = []
        teacher_id = 1

        grades = ["高一", "高二", "高三"]

        for subject in exam_info['unique_subjects']:
            # 转换科目名称
            subject_type = self._convert_subject_name(subject)

            # 为每个科目生成教师
            for i in range(self.config.teachers_per_subject):
                # 分配年级（尽量平均分配）
                grade = grades[i % len(grades)]

                # 生成历史负荷（基于教龄的估算）
                experience_years = random.randint(1, 30)
                historical_load = self.config.historical_load_min + \
                               (self.config.historical_load_max - self.config.historical_load_min) * \
                               (experience_years / 30) + random.uniform(-50, 50)

                teacher = Teacher(
                    id=teacher_id,
                    name=f"{subject[:2]}老师{teacher_id:03d}",
                    subject=subject_type,
                    grade=grade,
                    historical_load=historical_load
                )

                # 生成授课时间表
                self._generate_teaching_schedule(teacher)

                # 随机生成请假和固定任务
                self._generate_teacher_constraints(teacher)

                self.teachers.append(teacher)
                teacher_id += 1

        # 确保有足够的教师（补充通用教师）
        needed_teachers = max(len(self.teachers), 100)
        while len(self.teachers) < needed_teachers:
            subject = random.choice(list(SubjectType))
            grade = random.choice(grades)

            teacher = Teacher(
                id=teacher_id,
                name=f"通用老师{teacher_id:03d}",
                subject=subject,
                grade=grade,
                historical_load=random.uniform(self.config.historical_load_min,
                                          self.config.historical_load_max)
            )

            self._generate_teaching_schedule(teacher)
            self._generate_teacher_constraints(teacher)

            self.teachers.append(teacher)
            teacher_id += 1

    def _convert_subject_name(self, subject_name: str) -> SubjectType:
        """转换科目名称为枚举类型"""
        return self.subject_name_mapping.get(subject_name, SubjectType.CHINESE)

    def _generate_teaching_schedule(self, teacher: Teacher):
        """生成教师授课时间表"""
        days = []
        for slot in self.time_slots:
            if slot.date not in days:
                days.append(slot.date)

        teacher.teaching_schedule = {}

        # 根据教师的工作量生成授课安排
        teaching_days = random.sample(days, random.randint(1, max(1, len(days)//2)))

        for day in teaching_days:
            # 每天安排1-3节课
            daily_slots = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节", "第8节", "第9节"]
            selected_slots = random.sample(daily_slots, random.randint(1, 3))
            teacher.teaching_schedule[day] = selected_slots

    def _generate_teacher_constraints(self, teacher: Teacher):
        """生成教师约束条件"""
        # 10%概率有请假
        if random.random() < 0.1:
            days = [slot.date for slot in self.time_slots]
            leave_day = random.choice(days)
            leave_slot = random.choice(["第1节", "第2节", "第3节", "第4节", "第5节"])
            teacher.leave_times.append((leave_day, leave_slot))

        # 15%概率有固定坐班
        if random.random() < 0.15:
            days = [slot.date for slot in self.time_slots]
            duty_day = random.choice(days)
            duty_slot = "第9节"  # 通常在晚上
            duty_room = random.choice(self.rooms[:10]) if self.rooms else None
            if duty_room:
                teacher.fixed_duties.append((duty_day, duty_slot, duty_room.name))

    def _convert_exams(self):
        """转换考试安排为Exam对象"""
        self.exams = []

        # 创建时间段查找表
        time_slot_map = {}
        for slot in self.time_slots:
            key = (slot.date, slot.name.split()[1] if len(slot.name.split()) > 1 else slot.name)
            time_slot_map[key] = slot

        # 为每个考试安排创建Exam对象
        for exam_schedule in self.exam_schedule:
            subject_type = self._convert_subject_name(exam_schedule['subject'])

            # 查找对应的时间段
            day_num = int(exam_schedule['date'].replace('第', '').replace('天', ''))
            base_date = datetime.strptime("2024-01-15", "%Y-%m-%d")
            actual_date = (base_date + timedelta(days=day_num-1)).strftime("%Y-%m-%d")

            # 查找时间段
            time_slot = None
            for slot in self.time_slots:
                if (slot.date == actual_date and
                    exam_schedule['time_slot'] in slot.name and
                    abs(self._calculate_duration(slot.start_time, slot.end_time) -
                        exam_schedule['duration']) < 30):
                    time_slot = slot
                    break

            if not time_slot:
                # 如果找不到精确匹配，使用该日期的第一个时间段
                for slot in self.time_slots:
                    if slot.date == actual_date:
                        time_slot = slot
                        break

            if time_slot:
                # 分配考场
                allocated_rooms = self._allocate_rooms_for_exam(
                    exam_schedule['subject'],
                    len(self.time_slots) * 5  # 估算考场数量
                )

                exam = Exam(
                    subject=subject_type,
                    time_slot=time_slot,
                    rooms=allocated_rooms,
                    is_long_subject=subject_type in self.long_subjects
                )
                self.exams.append(exam)

    def _allocate_rooms_for_exam(self, subject: str, total_rooms_available: int) -> List[Room]:
        """为考试分配考场"""
        if self.config.room_allocation_strategy == "grade_based":
            # 基于年级的分配策略
            return self._allocate_rooms_by_grade(subject)
        elif self.config.room_allocation_strategy == "capacity_based":
            # 基于容量的分配策略
            return self._allocate_rooms_by_capacity()
        else:
            # 随机分配
            return random.sample(self.rooms, min(20, len(self.rooms)))

    def _allocate_rooms_by_grade(self, subject: str) -> List[Room]:
        """基于年级分配考场"""
        # 根据科目确定主要年级
        grade_mapping = {
            "语文": "高三", "数学": "高三", "英语": "高三",
            "物理": "高二", "化学": "高二", "生物": "高二",
            "历史": "高一", "地理": "高一", "政治": "高一"
        }

        target_grade = grade_mapping.get(subject, "高二")

        # 优先选择对应年级教学楼
        preferred_rooms = [room for room in self.rooms
                          if target_grade in room.building or "教学楼" in room.building]

        if len(preferred_rooms) >= 20:
            return preferred_rooms[:20]
        else:
            # 如果不够，补充其他考场
            additional_rooms = [room for room in self.rooms if room not in preferred_rooms]
            return preferred_rooms + additional_rooms[:20-len(preferred_rooms)]

    def _allocate_rooms_by_capacity(self) -> List[Room]:
        """基于容量分配考场"""
        # 优先使用中等容量考场
        medium_rooms = [room for room in self.rooms
                       if room.capacity == self.config.room_capacity_medium]
        large_rooms = [room for room in self.rooms
                      if room.capacity == self.config.room_capacity_large]
        small_rooms = [room for room in self.rooms
                      if room.capacity == self.config.room_capacity_small]

        selected_rooms = medium_rooms[:10] + large_rooms[:7] + small_rooms[:3]
        return selected_rooms[:20]

    def _validate_conversion(self, schedule: ExamSchedule):
        """验证转换结果"""
        print("验证转换结果...")

        # 基础检查
        assert len(schedule.teachers) > 0, "教师列表不能为空"
        assert len(schedule.rooms) > 0, "考场列表不能为空"
        assert len(schedule.time_slots) > 0, "时间段列表不能为空"
        assert len(schedule.exams) > 0, "考试列表不能为空"

        # 一致性检查
        exam_count = len(self.exam_schedule)
        converted_count = len(schedule.exams)
        if converted_count != exam_count:
            print(f"警告：原考试安排有{exam_count}场，转换后为{converted_count}场")

        # 时间段检查
        dates = set(exam['date'] for exam in self.exam_schedule)
        converted_dates = set(slot.date for slot in schedule.time_slots)
        if not dates.issubset(converted_dates):
            print("警告：部分日期未正确转换")

        print("转换验证完成")

    def get_conversion_summary(self) -> Dict[str, Any]:
        """获取转换结果摘要"""
        return {
            'original_exams': len(self.exam_schedule),
            'generated_teachers': len(self.teachers),
            'generated_rooms': len(self.rooms),
            'generated_time_slots': len(self.time_slots),
            'converted_exams': len(self.exams),
            'subjects': list(set(exam.subject.value for exam in self.exams)),  # 修复：转换为字符串
            'config': self.config.__dict__
        }


def main():
    """测试转换器"""
    # 模拟exam_scheduler.py的输出
    mock_exam_schedule = [
        {'date': '第1天', 'time_slot': '上午', 'subject': '语文',
         'start_time': '07:30', 'end_time': '09:40', 'duration': 150},
        {'date': '第1天', 'time_slot': '下午', 'subject': '数学',
         'start_time': '14:00', 'end_time': '15:30', 'duration': 120},
        {'date': '第2天', 'time_slot': '上午', 'subject': '英语',
         'start_time': '07:30', 'end_time': '09:30', 'duration': 120},
        {'date': '第2天', 'time_slot': '下午', 'subject': '物理',
         'start_time': '14:00', 'end_time': '15:30', 'duration': 90}
    ]

    # 创建转换器
    config = ConversionConfig(
        student_count_per_class=40,
        teachers_per_subject=6,
        room_allocation_strategy="grade_based"
    )

    converter = ScheduleConverter(config)

    # 执行转换
    schedule = converter.convert(mock_exam_schedule)

    # 显示结果
    summary = converter.get_conversion_summary()
    print("\n=== 转换结果摘要 ===")
    for key, value in summary.items():
        print(f"{key}: {value}")

    # 验证生成的数据
    print(f"\n生成的教师示例：{schedule.teachers[0].name} - {schedule.teachers[0].subject.value}")
    print(f"生成的考场示例：{schedule.rooms[0].name} - 容量{schedule.rooms[0].capacity}")
    print(f"生成的考试示例：{schedule.exams[0].subject.value} - {schedule.exams[0].time_slot.name}")


if __name__ == "__main__":
    main()
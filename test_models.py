"""
数据模型单元测试
全面测试所有数据模型类的功能和方法
"""
import unittest
from datetime import datetime
from models import (
    Teacher, Room, TimeSlot, Exam, Assignment,
    ExamSchedule, ConstraintConfig, SubjectType, ExamMode
)


class TestTeacher(unittest.TestCase):
    """教师类测试"""

    def setUp(self):
        """设置测试数据"""
        self.teacher = Teacher(
            id=1,
            name="张老师",
            subject=SubjectType.MATH,
            grade="高二",
            historical_load=50.0,
            teaching_schedule={
                "2024-01-01": ["上午第1-2节", "下午第1-2节"],
                "2024-01-02": ["上午第3-4节"]
            },
            leave_times=[("2024-01-03", "上午第1-2节")],
            fixed_duties=[("2024-01-04", "下午第1-2节", "A101")]
        )

    def test_teacher_creation(self):
        """测试教师对象创建"""
        self.assertEqual(self.teacher.id, 1)
        self.assertEqual(self.teacher.name, "张老师")
        self.assertEqual(self.teacher.subject, SubjectType.MATH)
        self.assertEqual(self.teacher.grade, "高二")
        self.assertEqual(self.teacher.historical_load, 50.0)

    def test_teacher_hash(self):
        """测试教师哈希方法"""
        self.assertEqual(hash(self.teacher), hash(1))

    def test_teacher_equality(self):
        """测试教师相等性比较"""
        teacher2 = Teacher(id=1, name="李老师", subject=SubjectType.CHINESE, grade="高一")
        self.assertEqual(self.teacher, teacher2)

        teacher3 = Teacher(id=2, name="张老师", subject=SubjectType.MATH, grade="高二")
        self.assertNotEqual(self.teacher, teacher3)


class TestRoom(unittest.TestCase):
    """考场类测试"""

    def setUp(self):
        """设置测试数据"""
        self.room = Room(
            id=101,
            name="A101",
            capacity=50,
            building="A栋",
            floor="1楼"
        )

    def test_room_creation(self):
        """测试考场对象创建"""
        self.assertEqual(self.room.id, 101)
        self.assertEqual(self.room.name, "A101")
        self.assertEqual(self.room.capacity, 50)
        self.assertEqual(self.room.building, "A栋")
        self.assertEqual(self.room.floor, "1楼")


class TestTimeSlot(unittest.TestCase):
    """时间段类测试"""

    def setUp(self):
        """设置测试数据"""
        self.time_slot = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100,
            is_morning=True,
            is_afternoon=False,
            is_lunch_pair_with="2024-01-01-下午"
        )

    def test_time_slot_creation(self):
        """测试时间段对象创建"""
        self.assertEqual(self.time_slot.id, "2024-01-01-上午")
        self.assertEqual(self.time_slot.name, "上午第1-2节")
        self.assertEqual(self.time_slot.date, "2024-01-01")
        self.assertEqual(self.time_slot.start_time, "08:00")
        self.assertEqual(self.time_slot.end_time, "09:40")
        self.assertEqual(self.time_slot.duration_minutes, 100)
        self.assertTrue(self.time_slot.is_morning)
        self.assertFalse(self.time_slot.is_afternoon)
        self.assertEqual(self.time_slot.is_lunch_pair_with, "2024-01-01-下午")

    def test_time_slot_hash(self):
        """测试时间段哈希方法"""
        self.assertEqual(hash(self.time_slot), hash("2024-01-01-上午"))


class TestExam(unittest.TestCase):
    """考试类测试"""

    def setUp(self):
        """设置测试数据"""
        self.time_slot = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100
        )
        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)

        self.exam = Exam(
            subject=SubjectType.MATH,
            time_slot=self.time_slot,
            rooms=[self.room1, self.room2],
            is_long_subject=True
        )

    def test_exam_creation(self):
        """测试考试对象创建"""
        self.assertEqual(self.exam.subject, SubjectType.MATH)
        self.assertEqual(self.exam.time_slot, self.time_slot)
        self.assertEqual(len(self.exam.rooms), 2)
        self.assertTrue(self.exam.is_long_subject)

    def test_get_total_rooms(self):
        """测试获取考场总数方法"""
        self.assertEqual(self.exam.get_total_rooms(), 2)

        exam_single_room = Exam(
            subject=SubjectType.ENGLISH,
            time_slot=self.time_slot,
            rooms=[self.room1],
            is_long_subject=False
        )
        self.assertEqual(exam_single_room.get_total_rooms(), 1)


class TestAssignment(unittest.TestCase):
    """监考安排类测试"""

    def setUp(self):
        """设置测试数据"""
        self.teacher = Teacher(id=1, name="张老师", subject=SubjectType.MATH, grade="高二")
        self.room = Room(id=101, name="A101", capacity=50)
        self.time_slot = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100
        )

        self.assignment = Assignment(
            teacher=self.teacher,
            room=self.room,
            time_slot=self.time_slot,
            subject=SubjectType.PHYSICS,
            is_invigilation=True
        )

    def test_assignment_creation(self):
        """测试监考安排对象创建"""
        self.assertEqual(self.assignment.teacher, self.teacher)
        self.assertEqual(self.assignment.room, self.room)
        self.assertEqual(self.assignment.time_slot, self.time_slot)
        self.assertEqual(self.assignment.subject, SubjectType.PHYSICS)
        self.assertTrue(self.assignment.is_invigilation)

    def test_assignment_hash(self):
        """测试监考安排哈希方法"""
        expected_hash = hash((1, 101, "2024-01-01-上午"))
        self.assertEqual(hash(self.assignment), expected_hash)


class TestConstraintConfig(unittest.TestCase):
    """约束配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ConstraintConfig()

        # 负荷系数
        self.assertEqual(config.invigilation_coefficient, 1.0)
        self.assertEqual(config.study_coefficient, 0.5)

        # 历史权重
        self.assertEqual(config.current_weight, 0.5)
        self.assertEqual(config.historical_weight, 0.5)

        # 软约束权重
        self.assertEqual(config.fairness_weight, 1000.0)
        self.assertEqual(config.long_exam_weight, 100.0)
        self.assertEqual(config.lunch_weight, 200.0)
        self.assertEqual(config.daily_limit_weight, 50.0)
        self.assertEqual(config.concentration_weight, 30.0)

        # 其他参数
        self.assertEqual(config.daily_comfort_limit, 2)
        self.assertEqual(config.lunch_break_duration, 90)

    def test_custom_config(self):
        """测试自定义配置"""
        config = ConstraintConfig(
            invigilation_coefficient=1.5,
            study_coefficient=0.8,
            fairness_weight=2000.0
        )

        self.assertEqual(config.invigilation_coefficient, 1.5)
        self.assertEqual(config.study_coefficient, 0.8)
        self.assertEqual(config.fairness_weight, 2000.0)


class TestExamSchedule(unittest.TestCase):
    """考试安排总表类测试"""

    def setUp(self):
        """设置测试数据"""
        self.config = ConstraintConfig()

        # 创建教师
        self.teacher1 = Teacher(id=1, name="张老师", subject=SubjectType.MATH, grade="高二", historical_load=30.0)
        self.teacher2 = Teacher(id=2, name="李老师", subject=SubjectType.CHINESE, grade="高二", historical_load=40.0)

        # 创建考场
        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)

        # 创建时间段
        self.time_slot1 = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100
        )
        self.time_slot2 = TimeSlot(
            id="2024-01-01-下午",
            name="下午第1-2节",
            date="2024-01-01",
            start_time="14:00",
            end_time="15:40",
            duration_minutes=100
        )

        # 创建考试
        self.exam1 = Exam(
            subject=SubjectType.MATH,
            time_slot=self.time_slot1,
            rooms=[self.room1],
            is_long_subject=True
        )
        self.exam2 = Exam(
            subject=SubjectType.CHINESE,
            time_slot=self.time_slot2,
            rooms=[self.room2],
            is_long_subject=False
        )

        # 创建监考安排
        self.assignment1 = Assignment(
            teacher=self.teacher1,
            room=self.room1,
            time_slot=self.time_slot1,
            subject=SubjectType.MATH,
            is_invigilation=True
        )
        self.assignment2 = Assignment(
            teacher=self.teacher2,
            room=self.room2,
            time_slot=self.time_slot2,
            subject=SubjectType.CHINESE,
            is_invigilation=True
        )

        # 创建考试安排表
        self.schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot1, self.time_slot2],
            exams=[self.exam1, self.exam2],
            assignments=[self.assignment1, self.assignment2],
            config=self.config
        )

    def test_schedule_creation_and_maps(self):
        """测试考试安排表创建和索引映射"""
        self.assertEqual(len(self.schedule.teachers), 2)
        self.assertEqual(len(self.schedule.rooms), 2)
        self.assertEqual(len(self.schedule.time_slots), 2)
        self.assertEqual(len(self.schedule.exams), 2)
        self.assertEqual(len(self.schedule.assignments), 2)

        # 检查索引映射
        self.assertEqual(len(self.schedule.teacher_map), 2)
        self.assertEqual(len(self.schedule.room_map), 2)
        self.assertEqual(len(self.schedule.time_slot_map), 2)

        self.assertIn(1, self.schedule.teacher_map)
        self.assertIn(101, self.schedule.room_map)
        self.assertIn("2024-01-01-上午", self.schedule.time_slot_map)

    def test_get_teacher_assignments(self):
        """测试获取教师的监考安排"""
        assignments = self.schedule.get_teacher_assignments(1)
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0].teacher.id, 1)
        self.assertEqual(assignments[0].room.id, 101)

        empty_assignments = self.schedule.get_teacher_assignments(999)
        self.assertEqual(len(empty_assignments), 0)

    def test_get_room_assignments(self):
        """测试获取考场的监考安排"""
        assignments = self.schedule.get_room_assignments(101)
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0].room.id, 101)
        self.assertEqual(assignments[0].teacher.id, 1)

        empty_assignments = self.schedule.get_room_assignments(999)
        self.assertEqual(len(empty_assignments), 0)

    def test_get_time_slot_assignments(self):
        """测试获取时间段的监考安排"""
        assignments = self.schedule.get_time_slot_assignments("2024-01-01-上午")
        self.assertEqual(len(assignments), 1)
        self.assertEqual(assignments[0].time_slot.id, "2024-01-01-上午")
        self.assertEqual(assignments[0].teacher.id, 1)

        empty_assignments = self.schedule.get_time_slot_assignments("invalid-time")
        self.assertEqual(len(empty_assignments), 0)

    def test_check_conflicts_no_conflicts(self):
        """测试冲突检查 - 无冲突情况"""
        conflicts = self.schedule.check_conflicts()
        self.assertEqual(len(conflicts), 0)

    def test_check_conflicts_teacher_conflict(self):
        """测试冲突检查 - 教师时间冲突"""
        # 添加冲突安排：同一教师在同一时间段有两个监考任务
        conflict_assignment = Assignment(
            teacher=self.teacher1,
            room=self.room2,
            time_slot=self.time_slot1,
            subject=SubjectType.ENGLISH,
            is_invigilation=True
        )
        self.schedule.assignments.append(conflict_assignment)

        conflicts = self.schedule.check_conflicts()
        self.assertGreater(len(conflicts), 0)
        self.assertTrue(any("张老师" in conflict and "2024-01-01-上午" in conflict for conflict in conflicts))

    def test_check_conflicts_room_conflict(self):
        """测试冲突检查 - 考场时间冲突"""
        # 添加冲突安排：同一考场在同一时间段有两场考试
        conflict_assignment = Assignment(
            teacher=self.teacher2,
            room=self.room1,
            time_slot=self.time_slot1,
            subject=SubjectType.ENGLISH,
            is_invigilation=True
        )
        self.schedule.assignments.append(conflict_assignment)

        conflicts = self.schedule.check_conflicts()
        self.assertGreater(len(conflicts), 0)
        self.assertTrue(any("A101" in conflict and "2024-01-01-上午" in conflict for conflict in conflicts))

    def test_calculate_teacher_load(self):
        """测试教师负荷计算"""
        # 为教师1添加更多安排以测试负荷计算
        study_assignment = Assignment(
            teacher=self.teacher1,
            room=self.room2,
            time_slot=self.time_slot2,
            subject=SubjectType.STUDY,
            is_invigilation=False
        )
        self.schedule.assignments.append(study_assignment)

        current_load, historical_load, total_load = self.schedule.calculate_teacher_load(1)

        # 验证计算结果
        expected_current = (100 * 1.0) + (100 * 0.5)  # 监考100分钟 + 自习100分钟*0.5
        self.assertAlmostEqual(current_load, expected_current, places=2)
        self.assertEqual(historical_load, 30.0)

        expected_total = (0.5 * expected_current) + (0.5 * 30.0)
        self.assertAlmostEqual(total_load, expected_total, places=2)

    def test_generate_statistics(self):
        """测试统计报表生成"""
        stats = self.schedule.generate_statistics()

        # 检查报表结构
        self.assertIn('teacher_stats', stats)
        self.assertIn('constraint_stats', stats)
        self.assertIn('fairness_metrics', stats)

        # 检查教师统计
        self.assertEqual(len(stats['teacher_stats']), 2)

        # 检查约束统计
        self.assertEqual(stats['constraint_stats']['conflict_count'], 0)
        self.assertEqual(len(stats['constraint_stats']['conflicts']), 0)

        # 检查公平性指标
        self.assertIn('max_total_load', stats['fairness_metrics'])
        self.assertIn('min_total_load', stats['fairness_metrics'])
        self.assertIn('avg_total_load', stats['fairness_metrics'])
        self.assertIn('load_range', stats['fairness_metrics'])
        self.assertIn('load_std', stats['fairness_metrics'])

    def test_count_long_exams(self):
        """测试长时科目统计"""
        count = self.schedule._count_long_exams(1)
        self.assertEqual(count, 1)  # 教师1监考了一科长时科目（数学）

        count2 = self.schedule._count_long_exams(2)
        self.assertEqual(count2, 0)  # 教师2监考的不是长时科目

    def test_calculate_std(self):
        """测试标准差计算"""
        values = [1, 2, 3, 4, 5]
        std = self.schedule._calculate_std(values)
        expected_std = ((4/5) ** 0.5)  # 方差=2，标准差=√2
        self.assertAlmostEqual(std, expected_std, places=6)

        # 单个值的标准差
        single_std = self.schedule._calculate_std([42])
        self.assertEqual(single_std, 0.0)

        # 空列表的标准差
        empty_std = self.schedule._calculate_std([])
        self.assertEqual(empty_std, 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
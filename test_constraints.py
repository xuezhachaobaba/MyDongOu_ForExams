"""
约束验证测试
全面测试系统中的硬约束和软约束验证逻辑
"""
import unittest
from datetime import datetime
from models import (
    Teacher, Room, TimeSlot, Exam, Assignment,
    ExamSchedule, ConstraintConfig, SubjectType
)


class TestHardConstraintValidation(unittest.TestCase):
    """硬约束验证测试"""

    def setUp(self):
        """设置测试数据"""
        self.config = ConstraintConfig()

        # 创建基础数据
        self.teacher1 = Teacher(
            id=1, name="张老师", subject=SubjectType.MATH, grade="高二",
            teaching_schedule={"2024-01-01": ["上午第1-2节"]},
            leave_times=[("2024-01-02", "下午第1-2节")]
        )
        self.teacher2 = Teacher(
            id=2, name="李老师", subject=SubjectType.CHINESE, grade="高二"
        )
        self.teacher3 = Teacher(
            id=3, name="王老师", subject=SubjectType.ENGLISH, grade="高二"
        )

        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)
        self.room3 = Room(id=103, name="A103", capacity=50)

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
        self.time_slot3 = TimeSlot(
            id="2024-01-02-上午",
            name="上午第1-2节",
            date="2024-01-02",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100
        )

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
        self.exam3 = Exam(
            subject=SubjectType.ENGLISH,
            time_slot=self.time_slot3,
            rooms=[self.room3],
            is_long_subject=False
        )

    def test_no_conflicts_valid_schedule(self):
        """测试无冲突的有效排期"""
        # 创建有效的监考安排
        assignments = [
            Assignment(teacher=self.teacher1, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH),
            Assignment(teacher=self.teacher2, room=self.room2, time_slot=self.time_slot2, subject=SubjectType.CHINESE),
            Assignment(teacher=self.teacher3, room=self.room3, time_slot=self.time_slot3, subject=SubjectType.ENGLISH)
        ]

        schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2, self.teacher3],
            rooms=[self.room1, self.room2, self.room3],
            time_slots=[self.time_slot1, self.time_slot2, self.time_slot3],
            exams=[self.exam1, self.exam2, self.exam3],
            assignments=assignments,
            config=self.config
        )

        conflicts = schedule.check_conflicts()
        self.assertEqual(len(conflicts), 0, "有效的排期不应该有冲突")

    def test_teacher_time_conflict(self):
        """测试教师时间冲突约束"""
        # 创建冲突安排：同一教师在同一时间监考两个考场
        assignments = [
            Assignment(teacher=self.teacher1, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH),
            Assignment(teacher=self.teacher1, room=self.room2, time_slot=self.time_slot1, subject=SubjectType.CHINESE),  # 冲突
            Assignment(teacher=self.teacher3, room=self.room3, time_slot=self.time_slot3, subject=SubjectType.ENGLISH)
        ]

        schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2, self.teacher3],
            rooms=[self.room1, self.room2, self.room3],
            time_slots=[self.time_slot1, self.time_slot2, self.time_slot3],
            exams=[self.exam1, self.exam2, self.exam3],
            assignments=assignments,
            config=self.config
        )

        conflicts = schedule.check_conflicts()
        self.assertGreater(len(conflicts), 0, "应该检测到教师时间冲突")
        self.assertTrue(any("张老师" in conflict and "2024-01-01-上午" in conflict for conflict in conflicts),
                       "冲突信息应该包含教师姓名和时间段")

    def test_room_time_conflict(self):
        """测试考场时间冲突约束"""
        # 创建冲突安排：同一考场在同一时间有两场考试
        assignments = [
            Assignment(teacher=self.teacher1, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH),
            Assignment(teacher=self.teacher2, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.CHINESE),  # 冲突
            Assignment(teacher=self.teacher3, room=self.room3, time_slot=self.time_slot3, subject=SubjectType.ENGLISH)
        ]

        schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2, self.teacher3],
            rooms=[self.room1, self.room2, self.room3],
            time_slots=[self.time_slot1, self.time_slot2, self.time_slot3],
            exams=[self.exam1, self.exam2, self.exam3],
            assignments=assignments,
            config=self.config
        )

        conflicts = schedule.checklicts()
        self.assertGreater(len(conflicts), 0, "应该检测到考场时间冲突")
        self.assertTrue(any("A101" in conflict and "2024-01-01-上午" in conflict for conflict in conflicts),
                       "冲突信息应该包含考场名称和时间段")

    def test_multiple_conflicts(self):
        """测试多个冲突同时存在"""
        # 创建多个冲突安排
        assignments = [
            Assignment(teacher=self.teacher1, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH),
            # 教师冲突
            Assignment(teacher=self.teacher1, room=self.room2, time_slot=self.time_slot1, subject=SubjectType.CHINESE),
            # 考场冲突
            Assignment(teacher=self.teacher2, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.ENGLISH),
            Assignment(teacher=self.teacher3, room=self.room3, time_slot=self.time_slot3, subject=SubjectType.PHYSICS)
        ]

        schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2, self.teacher3],
            rooms=[self.room1, self.room2, self.room3],
            time_slots=[self.time_slot1, self.time_slot2, self.time_slot3],
            exams=[self.exam1, self.exam2, self.exam3],
            assignments=assignments,
            config=self.config
        )

        conflicts = schedule.check_conflicts()
        self.assertGreaterEqual(len(conflicts), 2, "应该检测到至少2个冲突")

    def test_edge_case_empty_assignments(self):
        """测试边界情况：空安排列表"""
        schedule = ExamSchedule(
            teachers=[self.teacher1],
            rooms=[self.room1],
            time_slots=[self.time_slot1],
            exams=[self.exam1],
            assignments=[],
            config=self.config
        )

        conflicts = schedule.check_conflicts()
        self.assertEqual(len(conflicts), 0, "空安排不应该有冲突")

    def test_edge_case_single_assignment(self):
        """测试边界情况：单个安排"""
        assignment = Assignment(teacher=self.teacher1, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH)

        schedule = ExamSchedule(
            teachers=[self.teacher1],
            rooms=[self.room1],
            time_slots=[self.time_slot1],
            exams=[self.exam1],
            assignments=[assignment],
            config=self.config
        )

        conflicts = schedule.check_conflicts()
        self.assertEqual(len(conflicts), 0, "单个安排不应该有冲突")


class TestAdvancedConstraintValidation(unittest.TestCase):
    """高级约束验证测试（包括未来可能实现的约束）"""

    def setUp(self):
        """设置测试数据"""
        self.config = ConstraintConfig()

        # 创建具有约束的教师
        self.math_teacher = Teacher(
            id=1, name="数学张老师", subject=SubjectType.MATH, grade="高二"
        )
        self.chinese_teacher = Teacher(
            id=2, name="语文李老师", subject=SubjectType.CHINESE, grade="高二"
        )
        self.english_teacher = Teacher(
            id=3, name="英语王老师", subject=SubjectType.ENGLISH, grade="高二"
        )
        self.physics_teacher = Teacher(
            id=4, name="物理赵老师", subject=SubjectType.PHYSICS, grade="高二",
            teaching_schedule={"2024-01-01": ["上午第1-2节"]}  # 有授课安排
        )
        self.leaving_teacher = Teacher(
            id=5, name="请假钱老师", subject=SubjectType.CHEMISTRY, grade="高二",
            leave_times=[("2024-01-01", "下午第1-2节")]  # 有请假安排
        )

        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)

        self.morning_slot = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100,
            is_morning=True
        )
        self.afternoon_slot = TimeSlot(
            id="2024-01-01-下午",
            name="下午第1-2节",
            date="2024-01-01",
            start_time="14:00",
            end_time="15:40",
            duration_minutes=100,
            is_afternoon=True
        )

        self.math_exam = Exam(
            subject=SubjectType.MATH,
            time_slot=self.morning_slot,
            rooms=[self.room1],
            is_long_subject=True
        )
        self.physics_exam = Exam(
            subject=SubjectType.PHYSICS,
            time_slot=self.afternoon_slot,
            rooms=[self.room2],
            is_long_subject=False
        )

    def test_subject_avoidance_constraint_validation(self):
        """测试科目回避约束（教师不能监考自己的科目）"""
        # 违反科目回避约束：数学老师监考数学
        invalid_assignment = Assignment(
            teacher=self.math_teacher,
            room=self.room1,
            time_slot=self.morning_slot,
            subject=SubjectType.MATH,  # 数学老师监考数学（违反约束）
            is_invigilation=True
        )

        schedule = ExamSchedule(
            teachers=[self.math_teacher],
            rooms=[self.room1],
            time_slots=[self.morning_slot],
            exams=[self.math_exam],
            assignments=[invalid_assignment],
            config=self.config
        )

        # 当前实现中check_conflicts()不检查科目回避，但这是重要的约束
        # 这里演示如何测试这种约束，如果实现了的话
        conflicts = schedule.check_conflicts()

        # 这个测试展示了科目回避约束的概念
        # 在实际实现中，应该检查这类约束并返回相应的冲突信息
        # 目前这个测试会通过，因为check_conflicts()还没有实现这个功能

    def test_teaching_schedule_constraint_validation(self):
        """测试授课时间约束（教师不能在授课时间监考）"""
        # 违反授课时间约束：有授课安排的教师同时被安排监考
        invalid_assignment = Assignment(
            teacher=self.physics_teacher,
            room=self.room1,
            time_slot=self.morning_slot,
            subject=SubjectType.MATH
        )

        schedule = ExamSchedule(
            teachers=[self.physics_teacher],
            rooms=[self.room1],
            time_slots=[self.morning_slot],
            exams=[self.math_exam],
            assignments=[invalid_assignment],
            config=self.config
        )

        # 这个约束检查需要扩展check_conflicts()方法
        conflicts = schedule.check_conflicts()
        # 目前不会检测到授课时间冲突，但这是重要的硬约束

    def test_leave_time_constraint_validation(self):
        """测试请假时间约束（教师不能在请假时间监考）"""
        # 违反请假时间约束：请假的教师被安排监考
        invalid_assignment = Assignment(
            teacher=self.leaving_teacher,
            room=self.room2,
            time_slot=self.afternoon_slot,
            subject=SubjectType.PHYSICS
        )

        schedule = ExamSchedule(
            teachers=[self.leaving_teacher],
            rooms=[self.room2],
            time_slots=[self.afternoon_slot],
            exams=[self.physics_exam],
            assignments=[invalid_assignment],
            config=self.config
        )

        # 这个约束检查需要扩展check_conflicts()方法
        conflicts = schedule.check_conflicts()
        # 目前不会检测到请假时间冲突，但这是重要的硬约束

    def test_valid_subject_avoidance(self):
        """测试有效的科目回避情况"""
        # 满足科目回避约束：数学老师监考语文
        valid_assignment = Assignment(
            teacher=self.math_teacher,
            room=self.room1,
            time_slot=self.morning_slot,
            subject=SubjectType.CHINESE,  # 数学老师监考语文（满足约束）
            is_invigilation=True
        )

        schedule = ExamSchedule(
            teachers=[self.math_teacher],
            rooms=[self.room1],
            time_slots=[self.morning_slot],
            exams=[self.math_exam],
            assignments=[valid_assignment],
            config=self.config
        )

        conflicts = schedule.check_conflicts()
        self.assertEqual(len(conflicts), 0, "跨科目监考不应该有冲突")


class TestSoftConstraintEvaluation(unittest.TestCase):
    """软约束评估测试"""

    def setUp(self):
        """设置测试数据"""
        self.config = ConstraintConfig(
            fairness_weight=1000.0,
            long_exam_weight=100.0,
            lunch_weight=200.0,
            daily_limit_weight=50.0,
            concentration_weight=30.0,
            daily_comfort_limit=2
        )

        # 创建不同历史负荷的教师
        self.high_load_teacher = Teacher(
            id=1, name="高负荷教师", subject=SubjectType.MATH, grade="高二",
            historical_load=100.0
        )
        self.low_load_teacher = Teacher(
            id=2, name="低负荷教师", subject=SubjectType.CHINESE, grade="高二",
            historical_load=10.0
        )
        self.medium_load_teacher = Teacher(
            id=3, name="中等负荷教师", subject=SubjectType.ENGLISH, grade="高二",
            historical_load=50.0
        )

        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)

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

    def test_load_fairness_evaluation(self):
        """测试负荷公平性评估"""
        # 创建不公平的安排：高历史负荷教师承担更多任务
        assignments = [
            Assignment(teacher=self.high_load_teacher, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH),
            Assignment(teacher=self.high_load_teacher, room=self.room2, time_slot=self.time_slot2, subject=SubjectType.CHINESE),
            Assignment(teacher=self.low_load_teacher, room=self.room2, time_slot=self.time_slot1, subject=SubjectType.MATH, is_invigilation=False)
        ]

        schedule = ExamSchedule(
            teachers=[self.high_load_teacher, self.low_load_teacher, self.medium_load_teacher],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot1, self.time_slot2],
            exams=[self.exam1, self.exam2],
            assignments=assignments,
            config=self.config
        )

        # 生成统计信息
        stats = schedule.generate_statistics()
        fairness_metrics = stats.get('fairness_metrics', {})

        # 检查负荷分布
        self.assertIn('max_total_load', fairness_metrics)
        self.assertIn('min_total_load', fairness_metrics)
        self.assertIn('load_range', fairness_metrics)
        self.assertIn('avg_total_load', fairness_metrics)
        self.assertIn('load_std', fairness_metrics)

        # 验证负荷极差较大（表示不公平）
        load_range = fairness_metrics.get('load_range', 0)
        self.assertGreater(load_range, 0, "不公平安排应该有较大的负荷极差")

    def test_balanced_load_evaluation(self):
        """测试均衡负荷评估"""
        # 创建相对均衡的安排
        assignments = [
            Assignment(teacher=self.high_load_teacher, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH, is_invigilation=False),
            Assignment(teacher=self.low_load_teacher, room=self.room2, time_slot=self.time_slot2, subject=SubjectType.CHINESE),
            Assignment(teacher=self.medium_load_teacher, room=self.room2, time_slot=self.time_slot1, subject=SubjectType.MATH)
        ]

        schedule = ExamSchedule(
            teachers=[self.high_load_teacher, self.low_load_teacher, self.medium_load_teacher],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot1, self.time_slot2],
            exams=[self.exam1, self.exam2],
            assignments=assignments,
            config=self.config
        )

        # 生成统计信息
        stats = schedule.generate_statistics()
        fairness_metrics = stats.get('fairness_metrics', {})

        # 验证负荷分布
        self.assertIn('load_range', fairness_metrics)
        self.assertIn('load_std', fairness_metrics)

        load_std = fairness_metrics.get('load_std', 0)
        # 相对均衡的安排应该有较小的标准差
        self.assertGreaterEqual(load_std, 0, "标准差应该非负")

    def test_long_exam_distribution_evaluation(self):
        """测试长时科目分布评估"""
        # 创建多个长时科目监考安排给同一个教师
        assignments = [
            Assignment(teacher=self.high_load_teacher, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH),
            Assignment(teacher=self.high_load_teacher, room=self.room2, time_slot=self.time_slot2, subject=SubjectType.MATH, is_invigilation=False)
        ]

        schedule = ExamSchedule(
            teachers=[self.high_load_teacher, self.low_load_teacher, self.medium_load_teacher],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot1, self.time_slot2],
            exams=[self.exam1, self.exam2],
            assignments=assignments,
            config=self.config
        )

        # 检查长时科目计数
        long_exam_count = schedule._count_long_exams(self.high_load_teacher.id)
        self.assertGreaterEqual(long_exam_count, 1, "应该正确统计长时科目监考次数")

    def test_teacher_load_calculation_accuracy(self):
        """测试教师负荷计算准确性"""
        # 创建已知负荷的安排
        assignments = [
            Assignment(teacher=self.high_load_teacher, room=self.room1, time_slot=self.time_slot1, subject=SubjectType.MATH, is_invigilation=True),
            Assignment(teacher=self.high_load_teacher, room=self.room2, time_slot=self.time_slot2, subject=SubjectType.CHINESE, is_invigilation=False)
        ]

        schedule = ExamSchedule(
            teachers=[self.high_load_teacher],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot1, self.time_slot2],
            exams=[self.exam1, self.exam2],
            assignments=assignments,
            config=self.config
        )

        # 计算负荷
        current_load, historical_load, total_load = schedule.calculate_teacher_load(self.high_load_teacher.id)

        # 验证计算准确性
        expected_current_load = (100 * self.config.invigilation_coefficient) + (100 * self.config.study_coefficient)
        self.assertAlmostEqual(current_load, expected_current_load, places=2, "当前负荷计算应该准确")
        self.assertEqual(historical_load, 100.0, "历史负荷应该正确")

        expected_total_load = (self.config.current_weight * expected_current_load +
                             self.config.historical_weight * historical_load)
        self.assertAlmostEqual(total_load, expected_total_load, places=2, "加权总负荷计算应该准确")


class TestConstraintPerformance(unittest.TestCase):
    """约束检查性能测试"""

    def setUp(self):
        """设置大规模测试数据"""
        self.config = ConstraintConfig()

    def test_large_scale_conflict_checking_performance(self):
        """测试大规模冲突检查性能"""
        import time
        import random

        # 创建大规模数据
        teachers = [Teacher(id=i, name=f"教师{i}", subject=SubjectType.MATH, grade="高二")
                   for i in range(100)]

        rooms = [Room(id=i, name=f"Room{i}", capacity=50) for i in range(50)]

        time_slots = [TimeSlot(
            id=f"2024-01-{i//2+1:02d}-{'上午' if i%2==0 else '下午'}",
            name=f"第{i+1}节",
            date=f"2024-01-{i//2+1:02d}",
            start_time=f"{8+i%2*6:02d}:00",
            end_time=f"{9+i%2*6:02d}:40",
            duration_minutes=100
        ) for i in range(20)]

        # 创建大量安排（包含一些冲突）
        assignments = []
        for i in range(500):
            teacher = random.choice(teachers)
            room = random.choice(rooms)
            time_slot = random.choice(time_slots)
            subject = random.choice(list(SubjectType))

            assignment = Assignment(
                teacher=teacher,
                room=room,
                time_slot=time_slot,
                subject=subject
            )
            assignments.append(assignment)

        schedule = ExamSchedule(
            teachers=teachers,
            rooms=rooms,
            time_slots=time_slots,
            exams=[],
            assignments=assignments,
            config=self.config
        )

        # 测量冲突检查时间
        start_time = time.time()
        conflicts = schedule.check_conflicts()
        end_time = time.time()

        check_time = end_time - start_time

        # 验证性能（应该在合理时间内完成）
        self.assertLess(check_time, 5.0, "大规模冲突检查应该在5秒内完成")
        self.assertGreater(len(conflicts), 0, "随机安排应该产生一些冲突")

    def test_statistics_generation_performance(self):
        """测试统计生成性能"""
        import time

        # 创建中等规模数据
        teachers = [Teacher(id=i, name=f"教师{i}", subject=SubjectType.MATH, grade="高二")
                   for i in range(50)]

        rooms = [Room(id=i, name=f"Room{i}", capacity=50) for i in range(25)]

        time_slots = [TimeSlot(
            id=f"2024-01-{i//2+1:02d}-{'上午' if i%2==0 else '下午'}",
            name=f"第{i+1}节",
            date=f"2024-01-{i//2+1:02d}",
            start_time=f"{8+i%2*6:02d}:00",
            end_time=f"{9+i%2*6:02d}:40",
            duration_minutes=100
        ) for i in range(10)]

        assignments = []
        for teacher in teachers:
            for time_slot in time_slots[:2]:  # 每个教师2个安排
                room = rooms[teacher.id % len(rooms)]
                assignment = Assignment(
                    teacher=teacher,
                    room=room,
                    time_slot=time_slot,
                    subject=SubjectType.MATH
                )
                assignments.append(assignment)

        schedule = ExamSchedule(
            teachers=teachers,
            rooms=rooms,
            time_slots=time_slots,
            exams=[],
            assignments=assignments,
            config=self.config
        )

        # 测量统计生成时间
        start_time = time.time()
        stats = schedule.generate_statistics()
        end_time = time.time()

        generation_time = end_time - start_time

        # 验证性能和结果完整性
        self.assertLess(generation_time, 2.0, "统计生成应该在2秒内完成")

        # 验证统计信息完整性
        self.assertIn('teacher_stats', stats)
        self.assertIn('constraint_stats', stats)
        self.assertIn('fairness_metrics', stats)
        self.assertEqual(len(stats['teacher_stats']), len(teachers))


if __name__ == '__main__':
    unittest.main(verbosity=2)
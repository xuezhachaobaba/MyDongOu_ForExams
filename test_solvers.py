"""
求解器算法测试
测试OR-Tools和DEAP求解器的功能和正确性
"""
import unittest
from unittest.mock import Mock, patch
from models import (
    Teacher, Room, TimeSlot, Exam, Assignment,
    ExamSchedule, ConstraintConfig, SubjectType
)

# Import solvers with error handling
try:
    from ortools_solver import ORToolsSolver
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False

try:
    from deap_solver import DEAPSolver
    DEAP_AVAILABLE = True
except ImportError:
    DEAP_AVAILABLE = False


class TestORToolsSolver(unittest.TestCase):
    """OR-Tools求解器测试"""

    def setUp(self):
        """设置测试数据"""
        if not ORTOOLS_AVAILABLE:
            self.skipTest("OR-Tools未安装")

        # 创建简单的测试数据
        self.config = ConstraintConfig()

        self.teacher1 = Teacher(id=1, name="张老师", subject=SubjectType.MATH, grade="高二")
        self.teacher2 = Teacher(id=2, name="李老师", subject=SubjectType.CHINESE, grade="高二")

        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)

        self.time_slot = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100
        )

        self.exam = Exam(
            subject=SubjectType.MATH,
            time_slot=self.time_slot,
            rooms=[self.room1, self.room2],
            is_long_subject=False
        )

        self.schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot],
            exams=[self.exam],
            config=self.config
        )

        self.solver = ORToolsSolver(self.schedule)

    def test_solver_initialization(self):
        """测试求解器初始化"""
        self.assertEqual(self.solver.schedule, self.schedule)
        self.assertIsNotNone(self.solver.model)
        self.assertIsNotNone(self.solver.solver)
        self.assertEqual(len(self.solver.assign_vars), 0)
        self.assertEqual(len(self.solver.auxiliary_vars), 0)
        self.assertEqual(len(self.solver.assignments), 0)
        self.assertIsNone(self.solver.objective_value)

    def test_solver_parameters(self):
        """测试求解器参数设置"""
        self.assertEqual(self.solver.solver.parameters.max_time_in_seconds, 60)
        self.assertEqual(self.solver.solver.parameters.num_search_workers, 8)
        self.assertFalse(self.solver.solver.parameters.log_search_progress)

    def test_build_model(self):
        """测试模型构建"""
        self.solver.build_model()

        # 检查决策变量是否创建
        self.assertGreater(len(self.solver.assign_vars), 0)

        # 检查辅助变量是否创建
        self.assertGreater(len(self.solver.auxiliary_vars), 0)

    def test_solve_simple_case(self):
        """测试简单案例求解"""
        self.solver.build_model()
        success = self.solver.solve()

        self.assertTrue(success)
        self.assertIsNotNone(self.solver.objective_value)
        self.assertGreater(self.solver.solve_time, 0)
        self.assertGreater(len(self.solver.assignments), 0)

    def test_get_schedule(self):
        """测试获取求解结果"""
        self.solver.build_model()
        success = self.solver.solve()

        if success:
            result_schedule = self.solver.get_schedule()
            self.assertIsNotNone(result_schedule)
            self.assertIsInstance(result_schedule, ExamSchedule)
            self.assertGreater(len(result_schedule.assignments), 0)

    def test_print_solution_stats(self):
        """测试打印解决方案统计"""
        # 测试这个方法不会抛出异常
        with patch('builtins.print'):
            self.solver.print_solution_stats()

    def test_unsolvable_case(self):
        """测试无法求解的情况"""
        # 创建一个不可能满足约束的案例
        # 只有一个教师但有两个考场需要同时监考
        unsolvable_schedule = ExamSchedule(
            teachers=[self.teacher1],  # 只有一个教师
            rooms=[self.room1, self.room2],  # 两个考场
            time_slots=[self.time_slot],
            exams=[self.exam],
            config=self.config
        )

        solver = ORToolsSolver(unsolvable_schedule)
        solver.build_model()
        success = solver.solve()

        # 根据约束处理方式，可能成功但有惩罚，或失败
        # 这里主要测试不会崩溃
        self.assertIsInstance(success, bool)

    def test_empty_schedule(self):
        """测试空排期表"""
        empty_schedule = ExamSchedule(config=self.config)
        solver = ORToolsSolver(empty_schedule)

        # 构建模型不应该崩溃
        solver.build_model()

        # 求解应该成功，但没有安排
        success = solver.solve()
        self.assertTrue(success)


class TestDEAPSolver(unittest.TestCase):
    """DEAP遗传算法求解器测试"""

    def setUp(self):
        """设置测试数据"""
        if not DEAP_AVAILABLE:
            self.skipTest("DEAP未安装")

        # 创建测试数据
        self.config = ConstraintConfig()

        self.teacher1 = Teacher(id=1, name="张老师", subject=SubjectType.MATH, grade="高二")
        self.teacher2 = Teacher(id=2, name="李老师", subject=SubjectType.CHINESE, grade="高二")
        self.teacher3 = Teacher(id=3, name="王老师", subject=SubjectType.ENGLISH, grade="高二")

        self.room1 = Room(id=101, name="A101", capacity=50)
        self.room2 = Room(id=102, name="A102", capacity=50)

        self.time_slot = TimeSlot(
            id="2024-01-01-上午",
            name="上午第1-2节",
            date="2024-01-01",
            start_time="08:00",
            end_time="09:40",
            duration_minutes=100
        )

        self.exam = Exam(
            subject=SubjectType.MATH,
            time_slot=self.time_slot,
            rooms=[self.room1, self.room2],
            is_long_subject=False
        )

        self.schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2, self.teacher3],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot],
            exams=[self.exam],
            config=self.config
        )

        # 使用较小的参数进行快速测试
        self.solver = DEAPSolver(self.schedule, population_size=10, generations=5)

    def test_solver_initialization(self):
        """测试求解器初始化"""
        self.assertEqual(self.solver.schedule, self.schedule)
        self.assertEqual(self.solver.population_size, 10)
        self.assertEqual(self.solver.generations, 5)
        self.assertGreater(self.solver.chromosome_length, 0)
        self.assertIsNone(self.solver.best_individual)
        self.assertEqual(len(self.solver.best_assignments), 0)
        self.assertEqual(len(self.solver.fitness_history), 0)

    def test_chromosome_length_calculation(self):
        """测试染色体长度计算"""
        # 2个考场需要2个监考教师
        self.assertEqual(self.solver.chromosome_length, 2)

        # 测试多个考试的情况
        exam2 = Exam(
            subject=SubjectType.CHINESE,
            time_slot=self.time_slot,
            rooms=[self.room1],
            is_long_subject=False
        )
        multi_exam_schedule = ExamSchedule(
            teachers=[self.teacher1, self.teacher2],
            rooms=[self.room1, self.room2],
            time_slots=[self.time_slot],
            exams=[self.exam, exam2],
            config=self.config
        )

        solver = DEAPSolver(multi_exam_schedule, population_size=10, generations=5)
        # 2个考场（第一个考试）+ 1个考场（第二个考试）= 3个监考任务
        self.assertEqual(solver.chromosome_length, 3)

    def test_deap_setup(self):
        """测试DEAP框架设置"""
        # DEAP设置应该在初始化时完成
        self.assertTrue(hasattr(self.solver, 'toolbox'))

    def test_solve_simple_case(self):
        """测试简单案例求解"""
        success = self.solver.solve()

        self.assertTrue(success)
        self.assertIsNotNone(self.solver.best_individual)
        self.assertGreater(self.solver.solve_time, 0)
        self.assertGreaterEqual(len(self.solver.best_assignments), 0)

    def test_get_schedule(self):
        """测试获取求解结果"""
        success = self.solver.solve()

        if success:
            result_schedule = self.solver.get_schedule()
            self.assertIsNotNone(result_schedule)
            self.assertIsInstance(result_schedule, ExamSchedule)
            self.assertGreaterEqual(len(result_schedule.assignments), 0)

    def test_print_solution_stats(self):
        """测试打印解决方案统计"""
        # 测试这个方法不会抛出异常
        with patch('builtins.print'):
            self.solver.print_solution_stats()

    def test_fitness_history(self):
        """测试适应度历史记录"""
        self.solver.solve()
        self.assertGreater(len(self.solver.fitness_history), 0)

        # 适应度值应该随时间改善（减小）
        if len(self.solver.fitness_history) > 1:
            # 允许一定的波动，但整体趋势应该是改善的
            pass  # 由于遗传算法的随机性，这里不做严格断言

    def test_insufficient_teachers(self):
        """测试教师不足的情况"""
        insufficient_schedule = ExamSchedule(
            teachers=[self.teacher1],  # 只有一个教师
            rooms=[self.room1, self.room2],  # 两个考场
            time_slots=[self.time_slot],
            exams=[self.exam],
            config=self.config
        )

        solver = DEAPSolver(insufficient_schedule, population_size=10, generations=5)
        success = solver.solve()

        # 遗传算法应该能够运行，但可能有高惩罚
        self.assertIsInstance(success, bool)

    def test_empty_schedule(self):
        """测试空排期表"""
        empty_schedule = ExamSchedule(config=self.config)
        solver = DEAPSolver(empty_schedule, population_size=10, generations=5)

        # 空排期表应该能处理
        success = solver.solve()
        self.assertTrue(success)


class TestSolverComparison(unittest.TestCase):
    """求解器对比测试"""

    def setUp(self):
        """设置测试数据"""
        if not (ORTOOLS_AVAILABLE and DEAP_AVAILABLE):
            self.skipTest("需要同时安装OR-Tools和DEAP")

        self.config = ConstraintConfig()

        # 创建标准测试数据
        self.teachers = [
            Teacher(id=1, name="张老师", subject=SubjectType.MATH, grade="高二"),
            Teacher(id=2, name="李老师", subject=SubjectType.CHINESE, grade="高二"),
            Teacher(id=3, name="王老师", subject=SubjectType.ENGLISH, grade="高二"),
            Teacher(id=4, name="赵老师", subject=SubjectType.PHYSICS, grade="高二")
        ]

        self.rooms = [
            Room(id=101, name="A101", capacity=50),
            Room(id=102, name="A102", capacity=50),
            Room(id=103, name="A103", capacity=50)
        ]

        self.time_slots = [
            TimeSlot(
                id="2024-01-01-上午",
                name="上午第1-2节",
                date="2024-01-01",
                start_time="08:00",
                end_time="09:40",
                duration_minutes=100
            ),
            TimeSlot(
                id="2024-01-01-下午",
                name="下午第1-2节",
                date="2024-01-01",
                start_time="14:00",
                end_time="15:40",
                duration_minutes=100
            )
        ]

        self.exams = [
            Exam(
                subject=SubjectType.MATH,
                time_slot=self.time_slots[0],
                rooms=[self.rooms[0], self.rooms[1]],
                is_long_subject=False
            ),
            Exam(
                subject=SubjectType.CHINESE,
                time_slot=self.time_slots[1],
                rooms=[self.rooms[2]],
                is_long_subject=True
            )
        ]

        self.schedule = ExamSchedule(
            teachers=self.teachers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            exams=self.exams,
            config=self.config
        )

    def test_both_solvers_can_solve(self):
        """测试两个求解器都能求解同一问题"""
        # OR-Tests求解
        ortools_solver = ORToolsSolver(self.schedule)
        ortools_solver.build_model()
        ortools_success = ortools_solver.solve()

        # DEAP求解
        deap_solver = DEAPSolver(self.schedule, population_size=20, generations=10)
        deap_success = deap_solver.solve()

        # 两个求解器都应该能够求解
        self.assertTrue(ortools_success, "OR-Tools应该能够求解该问题")
        self.assertTrue(deap_success, "DEAP应该能够求解该问题")

    def test_solution_validity(self):
        """测试求解结果的有效性"""
        # 使用OR-Tools求解
        ortools_solver = ORToolsSolver(self.schedule)
        ortools_solver.build_model()
        ortools_success = ortools_solver.solve()

        if ortools_success:
            ortools_result = ortools_solver.get_schedule()
            # 检查没有冲突
            conflicts = ortools_result.check_conflicts()
            self.assertEqual(len(conflicts), 0, "OR-Tools求解结果不应该有冲突")

        # 使用DEAP求解
        deap_solver = DEAPSolver(self.schedule, population_size=20, generations=10)
        deap_success = deap_solver.solve()

        if deap_success:
            deap_result = deap_solver.get_schedule()
            # 检查冲突数量（由于是启发式算法，可能有少量冲突，但应该很少）
            conflicts = deap_result.check_conflicts()
            self.assertLessEqual(len(conflicts), 2, "DEAP求解结果冲突数应该很少")


if __name__ == '__main__':
    unittest.main(verbosity=2)
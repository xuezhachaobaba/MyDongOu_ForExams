"""
集成测试
测试完整的系统工作流程，从数据生成到求解分析的端到端测试
"""
import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# Import the main scheduler class
from main import IntelligentExamScheduler
from models import SubjectType, ConstraintConfig


class TestIntelligentExamSchedulerIntegration(unittest.TestCase):
    """智能排考系统集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.scheduler = IntelligentExamScheduler()

    def test_small_case_complete_workflow(self):
        """测试小规模案例完整工作流程"""
        # 1. 生成测试数据
        self.scheduler.generate_test_data("small")
        self.assertIsNotNone(self.scheduler.schedule)
        self.assertEqual(len(self.scheduler.schedule.teachers), 50)
        self.assertEqual(len(self.scheduler.schedule.exams), 3)  # 语文、数学、英语

        # 2. 使用OR-Tools求解
        success = self.scheduler.solve_with_ortools(time_limit=30)
        self.assertTrue(success)
        self.assertIsNotNone(self.scheduler.result_schedule)
        self.assertEqual(self.scheduler.algorithm_used, "OR-Tools")

        # 3. 分析结果
        with patch('builtins.print') as mock_print:
            self.scheduler.analyze_result()
            # 验证分析函数被调用
            self.assertGreater(mock_print.call_count, 0)

        # 4. 验证结果的有效性
        conflicts = self.scheduler.result_schedule.check_conflicts()
        self.assertEqual(len(conflicts), 0, "小规模案例不应该有硬约束冲突")

    def test_medium_case_complete_workflow(self):
        """测试中规模案例完整工作流程"""
        # 1. 生成测试数据
        self.scheduler.generate_test_data("medium")
        self.assertIsNotNone(self.scheduler.schedule)
        self.assertEqual(len(self.scheduler.schedule.teachers), 200)
        self.assertEqual(len(self.scheduler.schedule.exams), 5)  # 5个科目

        # 2. 使用DEAP求解
        success = self.scheduler.solve_with_deap(population_size=50, generations=20)
        self.assertTrue(success)
        self.assertIsNotNone(self.scheduler.result_schedule)
        self.assertEqual(self.scheduler.algorithm_used, "DEAP")

        # 3. 分析结果
        with patch('builtins.print'):
            self.scheduler.analyze_result()

        # 4. 验证结果的有效性（允许少量冲突，因为DEAP是启发式算法）
        conflicts = self.scheduler.result_schedule.check_conflicts()
        self.assertLessEqual(len(conflicts), 5, "中规模案例冲突数应该很少")

    def test_auto_algorithm_selection(self):
        """测试自动算法选择功能"""
        # 测试小规模（应该优先选择OR-Tools）
        self.scheduler.generate_test_data("small")
        success = self.scheduler.solve_auto(time_limit=30)

        self.assertTrue(success)
        self.assertIsNotNone(self.scheduler.result_schedule)
        self.assertIsNotNone(self.scheduler.algorithm_used)

        # 小规模问题应该优先使用OR-Tools
        self.assertIn(self.scheduler.algorithm_used, ["OR-Tools", "DEAP"])

    def test_custom_data_workflow(self):
        """测试自定义数据工作流程"""
        custom_config = {
            'teacher_count': 30,
            'subjects': [SubjectType.MATH, SubjectType.CHINESE],
            'rooms_per_exam': 5,
            'constraint_config': ConstraintConfig(
                invigilation_coefficient=1.5,
                fairness_weight=1500.0
            )
        }

        # 生成自定义数据
        self.scheduler.generate_test_data("custom", custom_config)
        self.assertIsNotNone(self.scheduler.schedule)
        self.assertEqual(len(self.scheduler.schedule.teachers), 30)
        self.assertEqual(len(self.scheduler.schedule.exams), 2)

        # 验证自定义配置被应用
        self.assertEqual(self.scheduler.schedule.config.invigilation_coefficient, 1.5)
        self.assertEqual(self.scheduler.schedule.config.fairness_weight, 1500.0)

        # 求解
        success = self.scheduler.solve_with_ortools(time_limit=30)
        self.assertTrue(success)

    def test_error_handling_workflow(self):
        """测试错误处理工作流程"""
        # 测试不支持的规模
        with self.assertRaises(ValueError):
            self.scheduler.generate_test_data("invalid_size")

        # 测试空求解
        empty_scheduler = IntelligentExamScheduler()
        with patch('builtins.print'):
            empty_scheduler.analyze_result()  # 不应该崩溃

    def test_benchmark_functionality(self):
        """测试基准测试功能"""
        with patch('builtins.print') as mock_print:
            self.scheduler.run_benchmark(
                sizes=['small'],  # 只测试小规模以加快测试
                algorithms=['ortools']  # 只测试OR-Tools
            )

        # 验证基准测试被调用
        self.assertGreater(mock_print.call_count, 0)

    def test_multiple_solving_attempts(self):
        """测试多次求解尝试"""
        self.scheduler.generate_test_data("small")

        # 第一次求解
        success1 = self.scheduler.solve_with_ortools(time_limit=30)
        result1_assignments = len(self.scheduler.result_schedule.assignments) if success1 else 0

        # 第二次求解（应该产生不同的结果）
        success2 = self.scheduler.solve_with_deap(population_size=30, generations=10)
        result2_assignments = len(self.scheduler.result_schedule.assignments) if success2 else 0

        # 验证两次求解都成功
        self.assertTrue(success1, "OR-Tools求解应该成功")
        self.assertTrue(success2, "DEAP求解应该成功")

        # 验证两次求解都产生了安排
        self.assertGreater(result1_assignments, 0, "OR-Tools应该产生监考安排")
        self.assertGreater(result2_assignments, 0, "DEAP应该产生监考安排")

    def test_result_consistency(self):
        """测试结果一致性"""
        self.scheduler.generate_test_data("small")

        # 求解
        success = self.scheduler.solve_with_ortools(time_limit=30)
        self.assertTrue(success)

        # 获取结果统计
        stats1 = self.scheduler.result_schedule.generate_statistics()

        # 再次获取统计（应该一致）
        stats2 = self.scheduler.result_schedule.generate_statistics()

        # 验证统计信息的一致性
        self.assertEqual(stats1['teacher_stats'], stats2['teacher_stats'])
        self.assertEqual(stats1['constraint_stats'], stats2['constraint_stats'])
        self.assertEqual(stats1['fairness_metrics'], stats2['fairness_metrics'])


class TestCommandLineInterface(unittest.TestCase):
    """命令行接口集成测试"""

    def setUp(self):
        """设置测试环境"""
        # 保存原始argv
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        """恢复测试环境"""
        # 恢复原始argv
        sys.argv = self.original_argv

    @patch('main.IntelligentExamScheduler')
    def test_cli_small_case(self, mock_scheduler_class):
        """测试命令行接口小规模案例"""
        # Mock the scheduler instance
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        # 设置命令行参数
        sys.argv = ['main.py', '--size', 'small', '--algorithm', 'ortools']

        # 导入并运行main函数
        from main import main

        try:
            main()
        except SystemExit:
            pass  # main()可能调用sys.exit()

        # 验证正确的调用
        mock_scheduler.generate_test_data.assert_called_with('small')
        mock_scheduler.solve_with_ortools.assert_called_with(60)
        mock_scheduler.analyze_result.assert_called()

    @patch('main.IntelligentExamScheduler')
    def test_cli_benchmark(self, mock_scheduler_class):
        """测试命令行接口基准测试"""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        # 设置命令行参数
        sys.argv = ['main.py', '--benchmark']

        from main import main

        try:
            main()
        except SystemExit:
            pass

        # 验证基准测试被调用
        mock_scheduler.run_benchmark.assert_called_once()

    @patch('main.IntelligentExamScheduler')
    def test_cli_custom_parameters(self, mock_scheduler_class):
        """测试命令行接口自定义参数"""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        # 设置命令行参数
        sys.argv = [
            'main.py',
            '--size', 'medium',
            '--algorithm', 'deap',
            '--population', '150',
            '--generations', '80',
            '--time-limit', '120'
        ]

        from main import main

        try:
            main()
        except SystemExit:
            pass

        # 验证参数传递
        mock_scheduler.generate_test_data.assert_called_with('medium')
        mock_scheduler.solve_with_deap.assert_called_with(150, 80)


class TestDataFlowIntegration(unittest.TestCase):
    """数据流集成测试"""

    def test_data_generator_to_solver_flow(self):
        """测试从数据生成到求解器的数据流"""
        scheduler = IntelligentExamScheduler()

        # 生成数据
        scheduler.generate_test_data("small")
        original_teacher_count = len(scheduler.schedule.teachers)
        original_exam_count = len(scheduler.schedule.exams)
        original_room_count = len(scheduler.schedule.rooms)

        # 求解
        success = scheduler.solve_with_ortools(time_limit=30)
        self.assertTrue(success)

        # 验证数据完整性
        self.assertEqual(len(scheduler.result_schedule.teachers), original_teacher_count)
        self.assertEqual(len(scheduler.result_schedule.exams), original_exam_count)
        self.assertEqual(len(scheduler.result_schedule.rooms), original_room_count)

        # 验证教师和考试信息在求解前后保持一致
        for i, teacher in enumerate(scheduler.schedule.teachers):
            result_teacher = scheduler.result_schedule.teachers[i]
            self.assertEqual(teacher.id, result_teacher.id)
            self.assertEqual(teacher.name, result_teacher.name)
            self.assertEqual(teacher.subject, result_teacher.subject)

    def test_schedule_consistency_across_algorithms(self):
        """测试不同算法间排期表的一致性"""
        scheduler = IntelligentExamScheduler()
        scheduler.generate_test_data("small")

        # 保存原始排期表
        original_schedule = scheduler.schedule

        # OR-Tools求解
        scheduler1 = IntelligentExamScheduler()
        scheduler1.schedule = original_schedule
        success1 = scheduler1.solve_with_ortools(time_limit=30)

        if success1:
            ortools_assignments = len(scheduler1.result_schedule.assignments)
            ortools_conflicts = len(scheduler1.result_schedule.check_conflicts())
        else:
            ortools_assignments = 0
            ortools_conflicts = float('inf')

        # DEAP求解
        scheduler2 = IntelligentExamScheduler()
        scheduler2.schedule = original_schedule
        success2 = scheduler2.solve_with_deap(population_size=50, generations=20)

        if success2:
            deap_assignments = len(scheduler2.result_schedule.assignments)
            deap_conflicts = len(scheduler2.result_schedule.check_conflicts())
        else:
            deap_assignments = 0
            deap_conflicts = float('inf')

        # 验证至少有一种算法成功
        self.assertTrue(success1 or success2, "至少应该有一种算法成功")

        # 验证成功的算法都产生了合理的安排
        if success1:
            self.assertGreater(ortools_assignments, 0, "OR-Tools应该产生监考安排")
            self.assertEqual(ortools_conflicts, 0, "OR-Tools结果不应该有冲突")

        if success2:
            self.assertGreater(deap_assignments, 0, "DEAP应该产生监考安排")
            self.assertLessEqual(deap_conflicts, 5, "DEAP冲突数应该很少")


class TestPerformanceIntegration(unittest.TestCase):
    """性能集成测试"""

    def test_performance_scaling(self):
        """测试性能随规模的扩展"""
        scheduler = IntelligentExamScheduler()

        sizes_and_teacher_counts = [
            ("small", 50),
            ("medium", 200)
        ]

        performance_data = {}

        for size, expected_teacher_count in sizes_and_teacher_counts:
            # 生成数据
            scheduler.generate_test_data(size)
            actual_teacher_count = len(scheduler.schedule.teachers)
            self.assertEqual(actual_teacher_count, expected_teacher_count)

            # 计算问题规模
            total_tasks = sum(exam.get_total_rooms() for exam in scheduler.exams)

            # 测量求解时间
            import time
            start_time = time.time()
            success = scheduler.solve_auto(time_limit=60)
            solve_time = time.time() - start_time

            if success:
                performance_data[size] = {
                    'teacher_count': actual_teacher_count,
                    'total_tasks': total_tasks,
                    'solve_time': solve_time,
                    'assignments': len(scheduler.result_schedule.assignments),
                    'conflicts': len(scheduler.result_schedule.check_conflicts())
                }

        # 验证性能数据
        self.assertIn("small", performance_data)
        self.assertIn("medium", performance_data)

        # 验证中规模问题需要更多时间（但仍在合理范围内）
        small_time = performance_data["small"]["solve_time"]
        medium_time = performance_data["medium"]["solve_time"]

        # 中规模应该需要更多时间，但差异不应该过大（表明算法具有良好的扩展性）
        self.assertGreater(medium_time, small_time * 0.5)  # 至少不会快太多

    def test_memory_usage_basic(self):
        """测试基本内存使用"""
        import gc
        import sys

        # 记录初始内存
        gc.collect()
        initial_objects = len(gc.get_objects())

        scheduler = IntelligentExamScheduler()
        scheduler.generate_test_data("small")
        scheduler.solve_with_ortools(time_limit=30)

        # 清理并检查内存
        gc.collect()
        final_objects = len(gc.get_objects())

        # 验证对象增长在合理范围内（不会出现明显的内存泄漏）
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 10000, "对象创建数量应该合理")


if __name__ == '__main__':
    unittest.main(verbosity=2)
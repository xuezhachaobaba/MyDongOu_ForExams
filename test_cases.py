"""
测试用例定义
包含不同规模和复杂度的排考场景
"""
import unittest
from data_generator import DataGenerator
from models import SubjectType, ConstraintConfig


class TestExamScheduler(unittest.TestCase):
    """排考系统测试用例"""

    def setUp(self):
        """测试设置"""
        self.generator = DataGenerator(seed=42)

    def test_small_case(self):
        """测试小型用例（50名教师，3个科目）"""
        print("\n=== 测试小型用例 ===")
        schedule = self.generator.create_small_test_case()

        self.assertGreater(len(schedule.teachers), 0)
        self.assertGreater(len(schedule.rooms), 0)
        self.assertGreater(len(schedule.exams), 0)

        print(f"教师数量: {len(schedule.teachers)}")
        print(f"考场数量: {len(schedule.rooms)}")
        print(f"考试数量: {len(schedule.exams)}")

        # 验证每个考试都有足够的考场
        for exam in schedule.exams:
            self.assertEqual(exam.get_total_rooms(), 5)  # 小型用例每个科目5个考场

    def test_medium_case(self):
        """测试中型用例（200名教师，5个科目）"""
        print("\n=== 测试中型用例 ===")
        schedule = self.generator.create_medium_test_case()

        self.assertGreater(len(schedule.teachers), 0)
        self.assertGreater(len(schedule.rooms), 0)
        self.assertGreater(len(schedule.exams), 0)

        print(f"教师数量: {len(schedule.teachers)}")
        print(f"考场数量: {len(schedule.rooms)}")
        print(f"考试数量: {len(schedule.exams)}")

        # 验证每个考试都有足够的考场
        for exam in schedule.exams:
            self.assertEqual(exam.get_total_rooms(), 10)  # 中型用例每个科目10个考场

    def test_large_case(self):
        """测试大型用例（400名教师，10个科目）"""
        print("\n=== 测试大型用例 ===")
        schedule = self.generator.create_large_test_case()

        self.assertGreater(len(schedule.teachers), 0)
        self.assertGreater(len(schedule.rooms), 0)
        self.assertGreater(len(schedule.exams), 0)

        print(f"教师数量: {len(schedule.teachers)}")
        print(f"考场数量: {len(schedule.rooms)}")
        print(f"考试数量: {len(schedule.exams)}")

        # 验证每个考试都有足够的考场
        for exam in schedule.exams:
            self.assertEqual(exam.get_total_rooms(), 20)  # 大型用例每个科目20个考场

    def test_constraint_config(self):
        """测试约束配置"""
        print("\n=== 测试约束配置 ===")
        config = ConstraintConfig()

        # 验证默认配置
        self.assertEqual(config.invigilation_coefficient, 1.0)
        self.assertEqual(config.study_coefficient, 0.5)
        self.assertEqual(config.current_weight, 0.5)
        self.assertEqual(config.historical_weight, 0.5)

        print(f"监考负荷系数: {config.invigilation_coefficient}")
        print(f"自习负荷系数: {config.study_coefficient}")
        print(f"本次负荷权重: {config.current_weight}")
        print(f"历史负荷权重: {config.historical_weight}")


class TestAlgorithms(unittest.TestCase):
    """算法测试用例"""

    def setUp(self):
        """测试设置"""
        self.generator = DataGenerator(seed=42)

    def test_ortools_small(self):
        """测试OR-Tools在小型用例上的表现"""
        print("\n=== 测试OR-Tools小型用例 ===")
        schedule = self.generator.create_small_test_case()

        try:
            from ortools_solver import ORToolsSolver
            solver = ORToolsSolver(schedule)
            solver.build_model()

            success = solver.solve()
            self.assertTrue(success, "OR-Tools应该在小型用例上找到解")

            solver.print_solution_stats()

            # 验证结果
            result_schedule = solver.get_schedule()
            conflicts = result_schedule.check_conflicts()
            self.assertEqual(len(conflicts), 0, "解不应该有硬约束冲突")

        except ImportError:
            print("OR-Tools未安装，跳过测试")

    def test_deap_small(self):
        """测试DEAP在小型用例上的表现"""
        print("\n=== 测试DEAP小型用例 ===")
        schedule = self.generator.create_small_test_case()

        try:
            from deap_solver import DEAPSolver
            solver = DEAPSolver(schedule, population_size=20, generations=10)

            success = solver.solve()
            self.assertTrue(success, "DEAP应该在小型用例上找到解")

            solver.print_solution_stats()

        except ImportError:
            print("DEAP未安装，跳过测试")


def run_performance_benchmark():
    """性能基准测试"""
    print("\n" + "="*50)
    print("性能基准测试")
    print("="*50)

    generator = DataGenerator(seed=42)

    # 测试不同规模的数据生成时间
    test_sizes = [
        ("小型", "create_small_test_case"),
        ("中型", "create_medium_test_case"),
        ("大型", "create_large_test_case")
    ]

    import time

    for size_name, method_name in test_sizes:
        print(f"\n--- {size_name}测试 ---")

        start_time = time.time()
        schedule = getattr(generator, method_name)()
        generation_time = time.time() - start_time

        print(f"数据生成时间: {generation_time:.2f}秒")
        print(f"教师数量: {len(schedule.teachers)}")
        print(f"考场数量: {len(schedule.rooms)}")
        print(f"考试数量: {len(schedule.exams)}")
        print(f"总监考任务数: {sum(exam.get_total_rooms() for exam in schedule.exams)}")


def run_algorithm_comparison():
    """算法比较测试"""
    print("\n" + "="*50)
    print("算法比较测试")
    print("="*50)

    generator = DataGenerator(seed=42)
    schedule = generator.create_small_test_case()  # 使用小型用例进行快速比较

    results = {}

    # 测试OR-Tools
    try:
        print("\n--- OR-Tools求解 ---")
        from ortools_solver import ORToolsSolver

        import time
        start_time = time.time()
        solver = ORToolsSolver(schedule)
        solver.build_model()
        success = solver.solve()
        ortools_time = time.time() - start_time

        if success:
            result_schedule = solver.get_schedule()
            stats = result_schedule.generate_statistics()
            conflicts = result_schedule.check_conflicts()

            results['OR-Tools'] = {
                'success': True,
                'time': ortools_time,
                'objective': solver.objective_value,
                'conflicts': len(conflicts),
                'load_range': stats['fairness_metrics'].get('load_range', 0),
                'assignments': len(result_schedule.assignments)
            }

            print(f"求解成功，耗时: {ortools_time:.2f}秒")
            print(f"目标函数值: {solver.objective_value}")
            print(f"冲突数: {len(conflicts)}")
            print(f"负荷极差: {stats['fairness_metrics'].get('load_range', 0):.2f}")
        else:
            results['OR-Tools'] = {'success': False, 'time': ortools_time}
            print("OR-Tools求解失败")

    except ImportError:
        print("OR-Tools未安装")
        results['OR-Tools'] = {'success': False, 'error': 'Not installed'}

    # 测试DEAP
    try:
        print("\n--- DEAP求解 ---")
        from deap_solver import DEAPSolver

        import time
        start_time = time.time()
        solver = DEAPSolver(schedule, population_size=30, generations=15)
        success = solver.solve()
        deap_time = time.time() - start_time

        if success:
            result_schedule = solver.get_schedule()
            stats = result_schedule.generate_statistics()
            conflicts = result_schedule.check_conflicts()

            results['DEAP'] = {
                'success': True,
                'time': deap_time,
                'objective': solver.best_individual.fitness.values[0],
                'conflicts': len(conflicts),
                'load_range': stats['fairness_metrics'].get('load_range', 0),
                'assignments': len(result_schedule.assignments)
            }

            print(f"求解成功，耗时: {deap_time:.2f}秒")
            print(f"适应度值: {solver.best_individual.fitness.values[0]}")
            print(f"冲突数: {len(conflicts)}")
            print(f"负荷极差: {stats['fairness_metrics'].get('load_range', 0):.2f}")
        else:
            results['DEAP'] = {'success': False, 'time': deap_time}
            print("DEAP求解失败")

    except ImportError:
        print("DEAP未安装")
        results['DEAP'] = {'success': False, 'error': 'Not installed'}

    # 输出比较结果
    print("\n" + "="*30)
    print("算法比较结果")
    print("="*30)

    for algorithm, result in results.items():
        print(f"\n{algorithm}:")
        if result['success']:
            print(f"  ✅ 求解成功")
            print(f"  ⏱️  耗时: {result['time']:.2f}秒")
            print(f"  📊 目标值: {result.get('objective', 'N/A')}")
            print(f"  ⚠️  冲突数: {result.get('conflicts', 'N/A')}")
            print(f"  ⚖️  负荷极差: {result.get('load_range', 0):.2f}")
            print(f"  👥 安排数: {result.get('assignments', 0)}")
        else:
            print(f"  ❌ 求解失败")
            if 'error' in result:
                print(f"  💡 原因: {result['error']}")


def main():
    """运行所有测试"""
    print("智能排考系统测试套件")
    print("="*50)

    # 1. 单元测试
    print("\n1. 运行单元测试...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # 2. 性能基准测试
    print("\n2. 运行性能基准测试...")
    run_performance_benchmark()

    # 3. 算法比较测试
    print("\n3. 运行算法比较测试...")
    run_algorithm_comparison()

    print("\n" + "="*50)
    print("所有测试完成")
    print("="*50)


if __name__ == "__main__":
    main()
"""
智能排考系统主程序
整合OR-Tools和DEAP两种算法，提供完整的排考解决方案
"""
import argparse
import sys
import time
from typing import Dict, Any, Optional

from data_generator import DataGenerator
from ortools_solver import ORToolsSolver
from deap_solver import DEAPSolver
from visualization import ResultVisualizer
from models import SubjectType, ConstraintConfig


class IntelligentExamScheduler:
    """智能排考系统主类"""

    def __init__(self):
        self.generator = DataGenerator(seed=42)
        self.schedule = None
        self.result_schedule = None
        self.solve_time = 0
        self.algorithm_used = ""

    def generate_test_data(self, size: str = "small", custom_config: Optional[Dict] = None):
        """生成测试数据"""
        print(f"生成{size}规模测试数据...")

        if size == "small":
            self.schedule = self.generator.create_small_test_case()
        elif size == "medium":
            self.schedule = self.generator.create_medium_test_case()
        elif size == "large":
            self.schedule = self.generator.create_large_test_case()
        elif size == "custom" and custom_config:
            self.schedule = self._generate_custom_data(custom_config)
        else:
            raise ValueError(f"不支持的数据规模: {size}")

        # 应用自定义配置
        if custom_config and 'constraint_config' in custom_config:
            self.schedule.config = custom_config['constraint_config']

        print(f"数据生成完成:")
        print(f"  教师数量: {len(self.schedule.teachers)}")
        print(f"  考场数量: {len(self.schedule.rooms)}")
        print(f"  时间段数量: {len(self.schedule.time_slots)}")
        print(f"  考试数量: {len(self.schedule.exams)}")
        print(f"  总监考任务数: {sum(exam.get_total_rooms() for exam in self.schedule.exams)}")

    def _generate_custom_data(self, config: Dict):
        """生成自定义数据"""
        teacher_count = config.get('teacher_count', 200)
        subjects = config.get('subjects', list(SubjectType)[:5])
        rooms_per_exam = config.get('rooms_per_exam', 10)

        return self.generator.generate_schedule(
            teacher_count=teacher_count,
            exam_subjects=subjects,
            rooms_per_exam=rooms_per_exam
        )

    def solve_with_ortools(self, time_limit: int = 60) -> bool:
        """使用OR-Tools求解"""
        print("\n=== 使用OR-Tools求解 ===")

        try:
            solver = ORToolsSolver(self.schedule)
            solver.solver.parameters.max_time_in_seconds = time_limit

            # 构建模型
            build_start = time.time()
            solver.build_model()
            build_time = time.time() - build_start
            print(f"模型构建时间: {build_time:.2f}秒")

            # 求解
            solve_start = time.time()
            success = solver.solve()
            self.solve_time = time.time() - solve_start

            if success:
                self.result_schedule = solver.get_schedule()
                self.algorithm_used = "OR-Tools"

                solver.print_solution_stats()
                return True
            else:
                print("OR-Tools未找到可行解")
                return False

        except ImportError:
            print("错误: OR-Tools未安装，请先安装: pip install ortools")
            return False
        except Exception as e:
            print(f"OR-Tools求解出错: {e}")
            return False

    def solve_with_deap(self, population_size: int = 200, generations: int = 100) -> bool:
        """使用DEAP遗传算法求解"""
        print("\n=== 使用DEAP遗传算法求解 ===")

        try:
            solver = DEAPSolver(self.schedule, population_size, generations)

            # 求解
            solve_start = time.time()
            success = solver.solve()
            self.solve_time = solve_start - solve_start

            if success:
                self.result_schedule = solver.get_schedule()
                self.algorithm_used = "DEAP"

                solver.print_solution_stats()
                return True
            else:
                print("DEAP未找到可行解")
                return False

        except ImportError:
            print("错误: DEAP未安装，请先安装: pip install deap")
            return False
        except Exception as e:
            print(f"DEAP求解出错: {e}")
            return False

    def solve_auto(self, time_limit: int = 60, deap_population: int = 200, deap_generations: int = 100) -> bool:
        """自动选择最佳算法求解"""
        print("\n=== 自动算法选择求解 ===")

        # 对于小规模问题，优先使用OR-Tools
        total_tasks = sum(exam.get_total_rooms() for exam in self.schedule.exams)
        teacher_count = len(self.schedule.teachers)

        print(f"问题规模: {teacher_count}名教师, {total_tasks}个监考任务")

        if total_tasks <= 100 and teacher_count <= 200:
            print("检测到小规模问题，优先使用OR-Tools...")
            if self.solve_with_ortools(time_limit):
                return True
            print("OR-Tools失败，尝试DEAP...")

        # 使用DEAP求解
        print("使用DEAP遗传算法求解...")
        return self.solve_with_deap(deap_population, deap_generations)

    def analyze_result(self):
        """分析求解结果"""
        if not self.result_schedule:
            print("还没有求解结果，请先运行求解")
            return

        print("\n" + "="*50)
        print("结果分析")
        print("="*50)

        # 生成统计信息
        stats = self.result_schedule.generate_statistics()

        # 基本信息
        print(f"\n📊 基本信息:")
        print(f"  使用算法: {self.algorithm_used}")
        print(f"  求解时间: {self.solve_time:.2f}秒")
        print(f"  监考安排数: {len(self.result_schedule.assignments)}")

        # 公平性分析
        fairness_metrics = stats.get('fairness_metrics', {})
        print(f"\n⚖️ 公平性分析:")
        print(f"  最大负荷: {fairness_metrics.get('max_total_load', 0):.2f}")
        print(f"  最小负荷: {fairness_metrics.get('min_total_load', 0):.2f}")
        print(f"  平均负荷: {fairness_metrics.get('avg_total_load', 0):.2f}")
        print(f"  负荷极差: {fairness_metrics.get('load_range', 0):.2f}")
        print(f"  负荷标准差: {fairness_metrics.get('load_std', 0):.2f}")

        # 冲突检查
        constraint_stats = stats.get('constraint_stats', {})
        conflicts = constraint_stats.get('conflicts', [])
        conflict_count = constraint_stats.get('conflict_count', 0)

        print(f"\n⚠️ 冲突检查:")
        print(f"  硬约束冲突数: {conflict_count}")
        if conflicts:
            print(f"  前5个冲突:")
            for i, conflict in enumerate(conflicts[:5]):
                print(f"    {i+1}. {conflict}")
        else:
            print("  ✅ 无硬约束冲突")

        # 负荷分布
        teacher_stats = stats.get('teacher_stats', [])
        if teacher_stats:
            loads = [stat['total_weighted_load'] for stat in teacher_stats]
            print(f"\n📈 负荷分布:")
            print(f"  教师平均安排数: {len(self.result_schedule.assignments) / len(teacher_stats):.2f}")
            print(f"  负荷最大教师: {max(teacher_stats, key=lambda x: x['total_weighted_load'])['teacher_name']} "
                  f"({max(loads):.2f})")
            print(f"  负荷最小教师: {min(teacher_stats, key=lambda x: x['total_weighted_load'])['teacher_name']} "
                  f"({min(loads):.2f})")

    def export_results(self, output_dir: str = "output", formats: list = None):
        """导出结果"""
        if not self.result_schedule:
            print("还没有求解结果，请先运行求解")
            return

        if formats is None:
            formats = ['excel', 'html', 'charts']

        print(f"\n=== 导出结果到 {output_dir} ===")

        visualizer = ResultVisualizer(self.result_schedule)
        exported_files = []

        try:
            # 导出Excel
            if 'excel' in formats:
                excel_files = visualizer.export_to_excel(output_dir)
                exported_files.extend(excel_files)
                print(f"✅ Excel文件导出完成")

            # 导出HTML报告
            if 'html' in formats:
                html_file = visualizer.generate_comprehensive_report(output_dir)
                exported_files.append(html_file)
                print(f"✅ HTML报告导出完成")

            # 生成图表
            if 'charts' in formats:
                load_chart = visualizer.plot_load_distribution(output_dir)
                heatmap = visualizer.plot_schedule_heatmap(output_dir)
                exported_files.extend([load_chart, heatmap])
                print(f"✅ 可视化图表导出完成")

            # 导出CSV
            if 'csv' in formats:
                csv_files = visualizer.export_to_csv(output_dir)
                exported_files.extend(csv_files)
                print(f"✅ CSV文件导出完成")

            print(f"\n📁 总共导出 {len(exported_files)} 个文件:")
            for file_path in exported_files:
                print(f"  - {file_path}")

        except Exception as e:
            print(f"导出结果时出错: {e}")

    def run_benchmark(self, sizes: list = None, algorithms: list = None):
        """运行基准测试"""
        if sizes is None:
            sizes = ['small', 'medium', 'large']
        if algorithms is None:
            algorithms = ['ortools', 'deap']

        print("\n" + "="*60)
        print("智能排考系统基准测试")
        print("="*60)

        results = {}

        for size in sizes:
            print(f"\n--- {size.upper()} 规模测试 ---")
            results[size] = {}

            # 生成测试数据
            self.generate_test_data(size)

            # 测试各个算法
            for algorithm in algorithms:
                print(f"\n测试 {algorithm.upper()}:")

                if algorithm == 'ortools':
                    time_limit = 60 if size == 'large' else 30
                    success = self.solve_with_ortools(time_limit)
                elif algorithm == 'deap':
                    pop_size = 100 if size == 'large' else 200
                    generations = 50 if size == 'large' else 100
                    success = self.solve_with_deap(pop_size, generations)
                else:
                    continue

                if success:
                    stats = self.result_schedule.generate_statistics()
                    fairness_metrics = stats.get('fairness_metrics', {})
                    conflicts = stats.get('constraint_stats', {}).get('conflicts', [])

                    results[size][algorithm] = {
                        'success': True,
                        'time': self.solve_time,
                        'objective': getattr(self.result_schedule, 'objective_value', 0),
                        'conflicts': len(conflicts),
                        'load_range': fairness_metrics.get('load_range', 0),
                        'assignments': len(self.result_schedule.assignments)
                    }

                    print(f"  ✅ 成功 - 耗时: {self.solve_time:.2f}s, 冲突: {len(conflicts)}, "
                          f"负荷极差: {fairness_metrics.get('load_range', 0):.2f}")
                else:
                    results[size][algorithm] = {'success': False, 'time': self.solve_time}
                    print(f"  ❌ 失败 - 耗时: {self.solve_time:.2f}s")

        # 输出汇总结果
        self._print_benchmark_summary(results)

    def _print_benchmark_summary(self, results: Dict):
        """打印基准测试汇总"""
        print("\n" + "="*40)
        print("基准测试汇总")
        print("="*40)

        for size, size_results in results.items():
            print(f"\n{size.upper()} 规模:")
            for algorithm, result in size_results.items():
                if result['success']:
                    print(f"  {algorithm.upper()}: ✅ {result['time']:.2f}s | "
                          f"冲突:{result['conflicts']} | 极差:{result['load_range']:.2f}")
                else:
                    print(f"  {algorithm.upper()}: ❌ {result['time']:.2f}s")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能排考系统')
    parser.add_argument('--size', choices=['small', 'medium', 'large', 'custom'],
                       default='small', help='测试数据规模')
    parser.add_argument('--algorithm', choices=['ortools', 'deap', 'auto'],
                       default='auto', help='求解算法')
    parser.add_argument('--output', default='output', help='输出目录')
    parser.add_argument('--formats', nargs='+', choices=['excel', 'html', 'charts', 'csv'],
                       default=['excel', 'html'], help='导出格式')
    parser.add_argument('--time-limit', type=int, default=60, help='OR-Tools求解时间限制(秒)')
    parser.add_argument('--population', type=int, default=200, help='DEAP种群大小')
    parser.add_argument('--generations', type=int, default=100, help='DEAP迭代代数')
    parser.add_argument('--benchmark', action='store_true', help='运行基准测试')
    parser.add_argument('--no-export', action='store_true', help='不导出结果文件')

    args = parser.parse_args()

    # 创建排考系统实例
    scheduler = IntelligentExamScheduler()

    try:
        # 基准测试模式
        if args.benchmark:
            scheduler.run_benchmark()
            return

        # 生成测试数据
        scheduler.generate_test_data(args.size)

        # 求解
        success = False
        if args.algorithm == 'ortools':
            success = scheduler.solve_with_ortools(args.time_limit)
        elif args.algorithm == 'deap':
            success = scheduler.solve_with_deap(args.population, args.generations)
        elif args.algorithm == 'auto':
            success = scheduler.solve_auto(args.time_limit, args.population, args.generations)

        if not success:
            print("求解失败！")
            sys.exit(1)

        # 分析结果
        scheduler.analyze_result()

        # 导出结果
        if not args.no_export:
            scheduler.export_results(args.output, args.formats)

    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
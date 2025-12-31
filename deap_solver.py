"""
DEAP遗传算法求解器
基于DEAP库的遗传算法实现智能排考
"""
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from deap import base, creator, tools, algorithms

from models import (
    Teacher, Room, TimeSlot, Exam, SubjectType,
    Assignment, ConstraintConfig, ExamSchedule
)


class DEAPSolver:
    """DEAP遗传算法求解器"""

    def __init__(self, schedule: ExamSchedule, population_size: int = 200, generations: int = 100):
        self.schedule = schedule
        self.population_size = population_size
        self.generations = generations

        # 个体表示：为每个需要监考的考场分配一个教师ID
        self.chromosome_length = self._calculate_chromosome_length()

        # 求解结果
        self.best_individual = None
        self.best_assignments = []
        self.solve_time = 0
        self.fitness_history = []

        # 初始化DEAP
        self._setup_deap()

    def _calculate_chromosome_length(self) -> int:
        """计算染色体长度（总监考任务数）"""
        total_tasks = 0
        for exam in self.schedule.exams:
            total_tasks += len(exam.rooms)  # 每个考场需要一个监考教师
        return total_tasks

    def _setup_deap(self):
        """设置DEAP框架"""
        # 创建适应度类（最小化问题）
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

        # 创建个体类
        creator.create("Individual", list, fitness=creator.FitnessMin)

        # 创建工具箱
        self.toolbox = base.Toolbox()

        # 注册基因生成器（选择可用的教师）
        self.toolbox.register("attr_teacher", self._random_available_teacher)

        # 注册个体和种群生成器
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,
                             self.toolbox.attr_teacher, n=self.chromosome_length)
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # 注册遗传算子
        self.toolbox.register("evaluate", self._evaluate_individual)
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutate, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

        # 预计算可用教师映射
        self._precompute_teacher_availability()

    def _precompute_teacher_availability(self):
        """预计算教师在各时间段的可用性"""
        self.teacher_availability = {}

        for time_slot in self.schedule.time_slots:
            available_teachers = []

            for teacher in self.schedule.teachers:
                if self._is_teacher_available(teacher, time_slot):
                    available_teachers.append(teacher.id)

            self.teacher_availability[time_slot.id] = available_teachers

    def _random_available_teacher(self) -> int:
        """随机选择一个可用教师"""
        # 这里需要根据具体的时间段来选择，暂时简化
        all_teacher_ids = [t.id for t in self.schedule.teachers]
        return random.choice(all_teacher_ids)

    def _is_teacher_available(self, teacher: Teacher, time_slot: TimeSlot) -> bool:
        """检查教师在特定时间段是否可用"""
        # 1. 检查请假时间
        for leave_date, leave_slot in teacher.leave_times:
            if leave_date == time_slot.date and leave_slot in time_slot.name:
                return False

        # 2. 检查改卷时间
        for exam in self.schedule.exams:
            if (exam.subject == teacher.subject and
                self._is_grading_period(time_slot, exam.time_slot)):
                return False

        # 3. 检查固定任务
        for fixed_date, fixed_slot, fixed_room in teacher.fixed_duties:
            if fixed_date == time_slot.date and fixed_slot in time_slot.name:
                # 检查固定任务的考场是否匹配
                for room in self.schedule.rooms:
                    if room.name == fixed_room:
                        return True  # 如果是固定任务，则可用但必须分配到特定考场

        return True

    def _is_grading_period(self, current_time: TimeSlot, exam_time: TimeSlot) -> bool:
        """判断当前时间是否为改卷期间"""
        from datetime import datetime, timedelta
        current_dt = datetime.strptime(current_time.date, "%Y-%m-%d")
        exam_dt = datetime.strptime(exam_time.date, "%Y-%m-%d")
        date_diff = (current_dt - exam_dt).days
        return date_diff >= 1

    def _evaluate_individual(self, individual) -> Tuple[float]:
        """评估个体的适应度（惩罚分）"""
        try:
            # 将染色体转换为监考安排
            assignments = self._chromosome_to_assignments(individual)

            # 计算硬约束违反惩罚（非常高的权重）
            hard_penalty = self._calculate_hard_constraint_penalties(assignments)

            # 如果有硬约束违反，直接返回高惩罚值
            if hard_penalty > 0:
                return (hard_penalty * 10000,)

            # 计算软约束违反惩罚
            soft_penalty = self._calculate_soft_constraint_penalties(assignments)

            return (soft_penalty,)

        except Exception as e:
            # 如果评估出错，返回极高的惩罚值
            return (float('inf'),)

    def _chromosome_to_assignments(self, chromosome: List[int]) -> List[Assignment]:
        """将染色体转换为监考安排"""
        assignments = []
        task_index = 0

        for exam in self.schedule.exams:
            time_slot = exam.time_slot

            for room in exam.rooms:
                if task_index < len(chromosome):
                    teacher_id = chromosome[task_index]
                    teacher = self.schedule.teacher_map[teacher_id]

                    # 创建安排（学科回避约束在适应度函数中检查）
                    assignment = Assignment(
                        teacher=teacher,
                        room=room,
                        time_slot=time_slot,
                        subject=exam.subject,
                        is_invigilation=True
                    )
                    assignments.append(assignment)
                    task_index += 1

        return assignments

    def _calculate_hard_constraint_penalties(self, assignments: List[Assignment]) -> float:
        """计算硬约束违反惩罚"""
        penalty = 0.0

        # H-E-01: 教师时空冲突
        teacher_time_slots = {}
        for assignment in assignments:
            teacher_id = assignment.teacher.id
            time_slot_id = assignment.time_slot.id
            room_id = assignment.room.id

            key = (teacher_id, time_slot_id)
            if key in teacher_time_slots:
                penalty += 1000  # 教师在同一时间有多个任务
            else:
                teacher_time_slots[key] = assignment

        # H-E-01: 考场时空冲突
        room_time_slots = {}
        for assignment in assignments:
            room_id = assignment.room.id
            time_slot_id = assignment.time_slot.id

            key = (room_id, time_slot_id)
            if key in room_time_slots:
                penalty += 1000  # 考场在同一时间有多个考试
            else:
                room_time_slots[key] = assignment

        # H-E-02, 03, 04: 教师可用性约束
        for assignment in assignments:
            teacher = assignment.teacher
            time_slot = assignment.time_slot

            if not self._is_teacher_available(teacher, time_slot):
                penalty += 500  # 教师在不可用时间被安排

        # H-E-09: 固定任务约束
        for assignment in assignments:
            teacher = assignment.teacher
            time_slot = assignment.time_slot
            room = assignment.room

            # 检查是否为固定任务
            fixed_task_met = False
            for fixed_date, fixed_slot, fixed_room in teacher.fixed_duties:
                if (fixed_date == time_slot.date and
                    fixed_slot in time_slot.name and
                    fixed_room == room.name):
                    fixed_task_met = True
                    break

            # 如果有固定任务但未被满足
            if teacher.fixed_duties and not fixed_task_met:
                # 检查是否是固定任务的时间但分配到其他考场
                is_fixed_time = False
                for fixed_date, fixed_slot, _ in teacher.fixed_duties:
                    if fixed_date == time_slot.date and fixed_slot in time_slot.name:
                        is_fixed_time = True
                        break

                if is_fixed_time:
                    penalty += 200  # 固定任务未满足

        return penalty

    def _calculate_soft_constraint_penalties(self, assignments: List[Assignment]) -> float:
        """计算软约束违反惩罚"""
        config = self.schedule.config
        penalty = 0.0

        # 准备数据结构
        teacher_assignments = {t.id: [] for t in self.schedule.teachers}
        for assignment in assignments:
            teacher_assignments[assignment.teacher.id].append(assignment)

        # S-E-01: 核心公平性（加权总负荷极差）
        total_loads = []
        for teacher in self.schedule.teachers:
            teacher_assigns = teacher_assignments[teacher.id]

            # 计算当前负荷
            current_load = 0.0
            long_exam_count = 0

            for assignment in teacher_assigns:
                duration = assignment.time_slot.duration_minutes
                current_load += duration * config.invigilation_coefficient

                # 统计长时科目
                if any(e.subject == assignment.subject and e.is_long_subject
                      for e in self.schedule.exams):
                    long_exam_count += 1

            # 计算加权总负荷
            total_load = (config.current_weight * current_load +
                         config.historical_weight * teacher.historical_load)
            total_loads.append(total_load)

        if total_loads:
            max_load = max(total_loads)
            min_load = min(total_loads)
            load_range = max_load - min_load
            penalty += load_range * config.fairness_weight

        # S-E-03: 长时科目平衡
        long_counts = []
        for teacher in self.schedule.teachers:
            teacher_assigns = teacher_assignments[teacher.id]
            long_count = 0

            for assignment in teacher_assigns:
                if any(e.subject == assignment.subject and e.is_long_subject
                      for e in self.schedule.exams):
                    long_count += 1

            long_counts.append(long_count)

        if long_counts:
            avg_long = np.mean(long_counts)
            for count in long_counts:
                excess = max(0, count - avg_long)
                penalty += excess * config.long_exam_weight

        # S-E-04: 午休保障
        for teacher in self.schedule.teachers:
            teacher_assigns = teacher_assignments[teacher.id]

            # 按日期分组
            daily_assigns = {}
            for assignment in teacher_assigns:
                date = assignment.time_slot.date
                if date not in daily_assigns:
                    daily_assigns[date] = []
                daily_assigns[date].append(assignment)

            # 检查每天的午休配对
            for date, day_assigns in daily_assigns.items():
                morning_assigns = [a for a in day_assigns if a.time_slot.is_morning]
                afternoon_assigns = [a for a in day_assigns if a.time_slot.is_afternoon]

                # 检查午休违反
                for morning_assign in morning_assigns:
                    for afternoon_assign in afternoon_assigns:
                        # 检查是否为午休配对
                        if (morning_assign.time_slot.is_lunch_pair_with == afternoon_assign.time_slot.id or
                            afternoon_assign.time_slot.is_lunch_pair_with == morning_assign.time_slot.id):
                            penalty += config.lunch_weight

        # S-E-06: 每日负荷
        for teacher in self.schedule.teachers:
            teacher_assigns = teacher_assignments[teacher.id]

            # 按日期统计任务数
            daily_counts = {}
            for assignment in teacher_assigns:
                date = assignment.time_slot.date
                daily_counts[date] = daily_counts.get(date, 0) + 1

            for date, count in daily_counts.items():
                excess = max(0, count - config.daily_comfort_limit)
                penalty += excess * config.daily_limit_weight

        # S-E-05: 任务集中度
        for teacher in self.schedule.teachers:
            teacher_assigns = teacher_assignments[teacher.id]

            # 按日期检查上下午分布
            daily_distribution = {}
            for assignment in teacher_assigns:
                date = assignment.time_slot.date
                if date not in daily_distribution:
                    daily_distribution[date] = {'morning': False, 'afternoon': False}

                if assignment.time_slot.is_morning:
                    daily_distribution[date]['morning'] = True
                elif assignment.time_slot.is_afternoon:
                    daily_distribution[date]['afternoon'] = True

            for date, distribution in daily_distribution.items():
                if distribution['morning'] and distribution['afternoon']:
                    penalty += config.concentration_weight

        return penalty

    def _crossover(self, parent1, parent2):
        """交叉算子"""
        child1, child2 = [self.toolbox.clone(ind) for ind in (parent1, parent2)]

        # 单点交叉
        crossover_point = random.randint(1, len(child1) - 1)
        child1[crossover_point:], child2[crossover_point:] = child2[crossover_point:], child1[crossover_point:]

        return child1, child2

    def _mutate(self, individual, indpb):
        """变异算子"""
        for i in range(len(individual)):
            if random.random() < indpb:
                # 随机变异为另一个教师
                individual[i] = random.choice([t.id for t in self.schedule.teachers])

        return individual,

    def solve(self) -> bool:
        """运行遗传算法"""
        import time

        print("开始运行遗传算法...")
        start_time = time.time()

        # 创建初始种群
        population = self.toolbox.population(n=self.population_size)

        # 评估初始种群
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit

        # 统计信息
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("min", np.min)
        stats.register("avg", np.mean)
        stats.register("max", np.max)

        # 运行遗传算法
        algorithms.eaSimple(
            population,
            self.toolbox,
            cxpb=0.7,  # 交叉概率
            mutpb=0.3,  # 变异概率
            ngen=self.generations,
            stats=stats,
            verbose=True
        )

        self.solve_time = time.time() - start_time

        # 获取最佳个体
        self.best_individual = tools.selBest(population, k=1)[0]
        best_fitness = self.best_individual.fitness.values[0]

        print(f"遗传算法完成，耗时: {self.solve_time:.2f}秒")
        print(f"最佳适应度: {best_fitness}")

        # 转换为监考安排
        self.best_assignments = self._chromosome_to_assignments(self.best_individual)
        print(f"提取到 {len(self.best_assignments)} 个监考安排")

        return len(self.best_assignments) > 0

    def get_schedule(self) -> ExamSchedule:
        """获取求解后的排考安排"""
        result_schedule = ExamSchedule(
            teachers=self.schedule.teachers,
            rooms=self.schedule.rooms,
            time_slots=self.schedule.time_slots,
            exams=self.schedule.exams,
            assignments=self.best_assignments,
            config=self.schedule.config
        )

        return result_schedule

    def print_solution_stats(self):
        """打印求解统计信息"""
        print("\n=== 遗传算法求解统计信息 ===")
        print(f"种群大小: {self.population_size}")
        print(f"迭代代数: {self.generations}")
        print(f"求解时间: {self.solve_time:.2f}秒")
        print(f"最佳适应度: {self.best_individual.fitness.values[0] if self.best_individual else 'N/A'}")

        if self.best_assignments:
            print(f"监考安排数量: {len(self.best_assignments)}")

            # 统计教师安排情况
            teacher_counts = {}
            for assignment in self.best_assignments:
                teacher_id = assignment.teacher.id
                teacher_counts[teacher_id] = teacher_counts.get(teacher_id, 0) + 1

            if teacher_counts:
                avg_assignments = sum(teacher_counts.values()) / len(teacher_counts)
                max_assignments = max(teacher_counts.values())
                min_assignments = min(teacher_counts.values())

                print(f"教师平均安排数: {avg_assignments:.2f}")
                print(f"教师最多安排数: {max_assignments}")
                print(f"教师最少安排数: {min_assignments}")

        # 检查冲突
        if self.best_assignments:
            result_schedule = self.get_schedule()
            conflicts = result_schedule.check_conflicts()
            if conflicts:
                print(f"发现 {len(conflicts)} 个冲突:")
                for conflict in conflicts[:5]:  # 只显示前5个冲突
                    print(f"  - {conflict}")
            else:
                print("未发现硬约束冲突")

            # 生成统计报表
            stats = result_schedule.generate_statistics()
            print(f"\n公平性指标:")
            print(f"最大负荷: {stats['fairness_metrics'].get('max_total_load', 0):.2f}")
            print(f"最小负荷: {stats['fairness_metrics'].get('min_total_load', 0):.2f}")
            print(f"负荷极差: {stats['fairness_metrics'].get('load_range', 0):.2f}")


def main():
    """测试DEAP求解器"""
    from data_generator import DataGenerator

    # 生成测试数据
    generator = DataGenerator()
    schedule = generator.create_small_test_case()

    print("测试数据生成完成")
    print(f"教师数量: {len(schedule.teachers)}")
    print(f"考场数量: {len(schedule.rooms)}")
    print(f"时间段数量: {len(schedule.time_slots)}")
    print(f"考试数量: {len(schedule.exams)}")

    # 创建求解器
    solver = DEAPSolver(schedule, population_size=50, generations=20)

    # 求解
    if solver.solve():
        solver.print_solution_stats()


if __name__ == "__main__":
    main()
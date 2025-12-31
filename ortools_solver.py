"""
OR-Tools约束规划求解器
基于Google OR-Tools的CP-SAT求解器实现智能排考
"""
from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model

from models import (
    Teacher, Room, TimeSlot, Exam, SubjectType,
    Assignment, ConstraintConfig, ExamSchedule
)


class ORToolsSolver:
    """OR-Tools CP-SAT求解器"""

    def __init__(self, schedule: ExamSchedule):
        self.schedule = schedule
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        # 变量存储
        self.assign_vars = {}  # X[t][r][s] 教师t在时间段s被分配到教室r
        self.auxiliary_vars = {}  # 辅助变量

        # 求解结果
        self.assignments = []
        self.solve_time = 0
        self.objective_value = None

        # 设置求解器参数
        self.solver.parameters.max_time_in_seconds = 60  # 最大求解时间60秒
        self.solver.parameters.num_search_workers = 8    # 使用8个搜索线程
        self.solver.parameters.log_search_progress = False

    def build_model(self):
        """构建数学模型"""
        print("构建OR-Tools模型...")

        # 1. 创建决策变量
        self._create_decision_variables()

        # 2. 添加硬约束
        self._add_hard_constraints()

        # 3. 创建辅助变量
        self._create_auxiliary_variables()

        # 4. 添加软约束到目标函数
        self._add_objective_function()

        print("模型构建完成")

    def _create_decision_variables(self):
        """创建决策变量 X[t][r][s]"""
        print("创建决策变量...")

        # 为每个教师-考场-时间组合创建布尔变量
        for teacher in self.schedule.teachers:
            for room in self.schedule.rooms:
                for time_slot in self.schedule.time_slots:
                    var_name = f"assign_{teacher.id}_{room.id}_{time_slot.id}"
                    self.assign_vars[(teacher.id, room.id, time_slot.id)] = self.model.NewBoolVar(var_name)

    def _add_hard_constraints(self):
        """添加硬约束条件"""
        print("添加硬约束...")

        # H-E-01: 考场/自习室覆盖约束 - 每个考场在每个时间段必须有且仅有一名教师
        for time_slot in self.schedule.time_slots:
            for exam in self.schedule.exams:
                if exam.time_slot.id == time_slot.id:
                    # 为该时间段的每个考场添加约束
                    for room in exam.rooms:
                        teacher_assignments = []
                        for teacher in self.schedule.teachers:
                            teacher_assignments.append(
                                self.assign_vars[(teacher.id, room.id, time_slot.id)]
                            )
                        # 每个考场必须有且仅有一名教师
                        self.model.Add(sum(teacher_assignments) == 1)

        # H-E-01: 教师时空冲突约束 - 每个教师在同一时间只能在一个考场
        for teacher in self.schedule.teachers:
            for time_slot in self.schedule.time_slots:
                room_assignments = []
                for room in self.schedule.rooms:
                    room_assignments.append(
                        self.assign_vars[(teacher.id, room.id, time_slot.id)]
                    )
                # 每个教师在同一时间最多只能在一个考场
                self.model.Add(sum(room_assignments) <= 1)

        # H-E-02, 03, 04: 教师不可用约束
        self._add_teacher_availability_constraints()

        # H-E-05: 学科回避约束
        self._add_subject_avoidance_constraints()

        # H-E-09: 固定任务约束
        self._add_fixed_duty_constraints()

    def _add_teacher_availability_constraints(self):
        """添加教师可用性约束（授课、请假、改卷）"""
        for teacher in self.schedule.teachers:
            for time_slot in self.schedule.time_slots:

                # 检查是否有时间冲突
                is_unavailable = False

                # 1. 授课时间冲突 H-E-02
                if time_slot.date in teacher.teaching_schedule:
                    # 简化处理：如果时间与授课时间重叠，则不可用
                    teaching_slots = teacher.teaching_schedule[time_slot.date]
                    # 这里需要根据具体的时间映射来判断
                    # 简化版本：假设所有时间段都与授课时间有冲突
                    if teaching_slots:
                        # 实际实现中需要精确的时间判断
                        pass

                # 2. 请假时间冲突 H-E-03
                for leave_date, leave_slot in teacher.leave_times:
                    if leave_date == time_slot.date and leave_slot in time_slot.name:
                        is_unavailable = True
                        break

                # 3. 改卷时间冲突 H-E-04
                # 科目考完后T+1天该科目教师不可监考
                for exam in self.schedule.exams:
                    if (exam.subject == teacher.subject and
                        self._is_grading_period(time_slot, exam.time_slot)):
                        is_unavailable = True
                        break

                # 如果教师不可用，则不能分配任何监考任务
                if is_unavailable:
                    for room in self.schedule.rooms:
                        self.model.Add(
                            self.assign_vars[(teacher.id, room.id, time_slot.id)] == 0
                        )

    def _is_grading_period(self, current_time: TimeSlot, exam_time: TimeSlot) -> bool:
        """判断当前时间是否为改卷期间"""
        # 简化实现：如果当前时间在考试时间的下一天或之后，则为改卷期间
        current_date = current_time.date
        exam_date = exam_time.date

        # 计算日期差
        from datetime import datetime, timedelta
        current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        exam_dt = datetime.strptime(exam_date, "%Y-%m-%d")

        date_diff = (current_dt - exam_dt).days
        return date_diff >= 1  # T+1天及之后

    def _add_subject_avoidance_constraints(self):
        """添加学科回避约束 H-E-05"""
        for teacher in self.schedule.teachers:
            for exam in self.schedule.exams:
                if exam.subject == teacher.subject:
                    # 该教师不能监考自己教授的科目
                    for room in exam.rooms:
                        self.model.Add(
                            self.assign_vars[(teacher.id, room.id, exam.time_slot.id)] == 0
                        )

    def _add_fixed_duty_constraints(self):
        """添加固定任务约束 H-E-09"""
        for teacher in self.schedule.teachers:
            for fixed_date, fixed_slot, fixed_room in teacher.fixed_duties:
                # 查找对应的考场和时间
                target_room = None
                target_time_slot = None

                for room in self.schedule.rooms:
                    if room.name == fixed_room:
                        target_room = room
                        break

                for time_slot in self.schedule.time_slots:
                    if (time_slot.date == fixed_date and
                        fixed_slot in time_slot.name):
                        target_time_slot = time_slot
                        break

                # 如果找到了对应的考场和时间，强制分配
                if target_room and target_time_slot:
                    self.model.Add(
                        self.assign_vars[(teacher.id, target_room.id, target_time_slot.id)] == 1
                    )

    def _create_auxiliary_variables(self):
        """创建辅助变量用于计算软约束"""
        print("创建辅助变量...")

        # 1. 教师时段占用变量 IsAssigned[t][s]
        self.auxiliary_vars['is_assigned'] = {}
        for teacher in self.schedule.teachers:
            for time_slot in self.schedule.time_slots:
                var_name = f"is_assigned_{teacher.id}_{time_slot.id}"
                self.auxiliary_vars['is_assigned'][(teacher.id, time_slot.id)] = self.model.NewBoolVar(var_name)

        # 2. 教师负荷变量
        self.auxiliary_vars['current_inv_load'] = {}
        self.auxiliary_vars['current_study_load'] = {}
        self.auxiliary_vars['current_weighted_load'] = {}
        self.auxiliary_vars['total_weighted_load'] = {}

        for teacher in self.schedule.teachers:
            # 当前监考负荷
            var_name = f"current_inv_load_{teacher.id}"
            self.auxiliary_vars['current_inv_load'][teacher.id] = self.model.NewIntVar(0, 10000, var_name)

            # 当前自习负荷
            var_name = f"current_study_load_{teacher.id}"
            self.auxiliary_vars['current_study_load'][teacher.id] = self.model.NewIntVar(0, 10000, var_name)

            # 当前加权负荷 - 使用整数变量（放大100倍避免浮点数）
            var_name = f"current_weighted_load_{teacher.id}"
            self.auxiliary_vars['current_weighted_load'][teacher.id] = self.model.NewIntVar(0, 10000, var_name)

            # 总加权负荷 - 使用整数变量（放大100倍避免浮点数）
            var_name = f"total_weighted_load_{teacher.id}"
            self.auxiliary_vars['total_weighted_load'][teacher.id] = self.model.NewIntVar(0, 10000, var_name)

        # 3. 公平性极值变量
        self.auxiliary_vars['max_total_load'] = self.model.NewIntVar(0, 10000, "max_total_load")
        self.auxiliary_vars['min_total_load'] = self.model.NewIntVar(0, 10000, "min_total_load")

        # 4. 长时科目计数变量
        self.auxiliary_vars['long_exam_count'] = {}
        for teacher in self.schedule.teachers:
            var_name = f"long_exam_count_{teacher.id}"
            self.auxiliary_vars['long_exam_count'][teacher.id] = self.model.NewIntVar(0, 100, var_name)

        # 5. 午休违反变量
        self.auxiliary_vars['violates_lunch'] = {}
        for teacher in self.schedule.teachers:
            for time_slot in self.schedule.time_slots:
                if time_slot.is_lunch_pair_with:
                    var_name = f"violates_lunch_{teacher.id}_{time_slot.id}"
                    self.auxiliary_vars['violates_lunch'][(teacher.id, time_slot.id)] = self.model.NewBoolVar(var_name)

        # 6. 每日负荷变量
        self.auxiliary_vars['daily_count'] = {}
        for teacher in self.schedule.teachers:
            dates = set(ts.date for ts in self.schedule.time_slots)
            for date in dates:
                var_name = f"daily_count_{teacher.id}_{date}"
                self.auxiliary_vars['daily_count'][(teacher.id, date)] = self.model.NewIntVar(0, 10, var_name)

        # 7. 任务集中度变量
        self.auxiliary_vars['split_day'] = {}
        for teacher in self.schedule.teachers:
            dates = set(ts.date for ts in self.schedule.time_slots)
            for date in dates:
                var_name = f"split_day_{teacher.id}_{date}"
                self.auxiliary_vars['split_day'][(teacher.id, date)] = self.model.NewBoolVar(var_name)

    def _add_objective_function(self):
        """添加目标函数（最小化软约束违反）"""
        print("添加目标函数...")

        config = self.schedule.config
        objective_terms = []

        # 1. 添加辅助变量的定义约束
        self._add_auxiliary_constraints()

        # 2. S-E-01: 核心公平性惩罚 (加权总负荷极差)
        fairness_penalty = self.model.NewIntVar(0, 100000, "fairness_penalty")
        self.model.Add(fairness_penalty >= self.auxiliary_vars['max_total_load'] -
                       self.auxiliary_vars['min_total_load'])
        objective_terms.append(fairness_penalty * config.fairness_weight)

        # 3. S-E-03: 长时科目平衡惩罚
        long_exam_penalty = []
        for teacher in self.schedule.teachers:
            count = self.auxiliary_vars['long_exam_count'][teacher.id]
            # 计算超出平均的部分
            excess = self.model.NewIntVar(0, 100, f"excess_long_{teacher.id}")
            avg_long = 2.0  # 简化的平均值
            self.model.Add(excess >= count - int(avg_long))
            long_exam_penalty.append(excess)

        if long_exam_penalty:
            total_long_penalty = self.model.NewIntVar(0, 10000, "total_long_penalty")
            self.model.Add(total_long_penalty == sum(long_exam_penalty))
            objective_terms.append(total_long_penalty * config.long_exam_weight)

        # 4. S-E-04: 午休保障惩罚
        lunch_penalty = []
        for (teacher_id, time_slot_id), var in self.auxiliary_vars['violates_lunch'].items():
            lunch_penalty.append(var)

        if lunch_penalty:
            total_lunch_penalty = self.model.NewIntVar(0, 1000, "total_lunch_penalty")
            self.model.Add(total_lunch_penalty == sum(lunch_penalty))
            objective_terms.append(total_lunch_penalty * config.lunch_weight)

        # 5. S-E-06: 每日负荷惩罚
        daily_penalty = []
        for (teacher_id, date), var in self.auxiliary_vars['daily_count'].items():
            excess = self.model.NewIntVar(0, 10, f"excess_daily_{teacher_id}_{date}")
            self.model.Add(excess >= var - config.daily_comfort_limit)
            daily_penalty.append(excess)

        if daily_penalty:
            total_daily_penalty = self.model.NewIntVar(0, 1000, "total_daily_penalty")
            self.model.Add(total_daily_penalty == sum(daily_penalty))
            objective_terms.append(total_daily_penalty * config.daily_limit_weight)

        # 6. S-E-05: 任务集中度惩罚
        concentration_penalty = []
        for var in self.auxiliary_vars['split_day'].values():
            concentration_penalty.append(var)

        if concentration_penalty:
            total_concentration_penalty = self.model.NewIntVar(0, 100, "total_concentration_penalty")
            self.model.Add(total_concentration_penalty == sum(concentration_penalty))
            objective_terms.append(total_concentration_penalty * config.concentration_weight)

        # 设置目标函数
        if objective_terms:
            self.model.Minimize(sum(objective_terms))

    def _add_auxiliary_constraints(self):
        """添加辅助变量的定义约束"""
        config = self.schedule.config

        # 1. IsAssigned[t][s] 定义
        for teacher in self.schedule.teachers:
            for time_slot in self.schedule.time_slots:
                assignments = []
                for room in self.schedule.rooms:
                    assignments.append(self.assign_vars[(teacher.id, room.id, time_slot.id)])

                self.model.Add(
                    self.auxiliary_vars['is_assigned'][(teacher.id, time_slot.id)] == sum(assignments)
                )

        # 2. 负荷计算约束
        for teacher in self.schedule.teachers:
            inv_load_terms = []
            study_load_terms = []

            for exam in self.schedule.exams:
                time_slot = exam.time_slot

                for room in exam.rooms:
                    assign_var = self.assign_vars[(teacher.id, room.id, time_slot.id)]
                    duration = time_slot.duration_minutes

                    # 监考负荷
                    inv_load_terms.append(assign_var * duration)
                    # 自习负荷（这个可能需要根据自习室定义调整）
                    # 暂时简化处理

            # 当前监考负荷
            self.model.Add(
                self.auxiliary_vars['current_inv_load'][teacher.id] == sum(inv_load_terms)
            )

            # 当前自习负荷（暂时为0）
            self.model.Add(self.auxiliary_vars['current_study_load'][teacher.id] == 0)

            # 当前加权负荷 - 使用整数计算（系数放大100倍）
            self.model.Add(
                self.auxiliary_vars['current_weighted_load'][teacher.id] * 100 >=
                (self.auxiliary_vars['current_inv_load'][teacher.id] * int(config.invigilation_coefficient * 100) +
                 self.auxiliary_vars['current_study_load'][teacher.id] * int(config.study_coefficient * 100))
            )
            self.model.Add(
                self.auxiliary_vars['current_weighted_load'][teacher.id] * 100 <=
                (self.auxiliary_vars['current_inv_load'][teacher.id] * int(config.invigilation_coefficient * 100) +
                 self.auxiliary_vars['current_study_load'][teacher.id] * int(config.study_coefficient * 100) + 99)
            )

            # 总加权负荷 - 使用整数计算（系数放大100倍）
            hist_load_int = int(teacher.historical_load)
            self.model.Add(
                self.auxiliary_vars['total_weighted_load'][teacher.id] * 100 >=
                (int(config.current_weight * 100) * self.auxiliary_vars['current_weighted_load'][teacher.id] +
                 int(config.historical_weight * 100) * hist_load_int)
            )
            self.model.Add(
                self.auxiliary_vars['total_weighted_load'][teacher.id] * 100 <=
                (int(config.current_weight * 100) * self.auxiliary_vars['current_weighted_load'][teacher.id] +
                 int(config.historical_weight * 100) * hist_load_int + 99)
            )

        # 3. 公平性极值约束
        for teacher in self.schedule.teachers:
            self.model.Add(
                self.auxiliary_vars['max_total_load'] >=
                self.auxiliary_vars['total_weighted_load'][teacher.id]
            )
            self.model.Add(
                self.auxiliary_vars['min_total_load'] <=
                self.auxiliary_vars['total_weighted_load'][teacher.id]
            )

        # 4. 长时科目计数约束
        for teacher in self.schedule.teachers:
            long_exam_terms = []
            for exam in self.schedule.exams:
                if exam.is_long_subject:
                    time_slot = exam.time_slot
                    for room in exam.rooms:
                        assign_var = self.assign_vars[(teacher.id, room.id, time_slot.id)]
                        long_exam_terms.append(assign_var)

            self.model.Add(
                self.auxiliary_vars['long_exam_count'][teacher.id] == sum(long_exam_terms)
            )

        # 5. 午休违反约束
        for (teacher_id, time_slot_id), var in self.auxiliary_vars['violates_lunch'].items():
            time_slot = next(ts for ts in self.schedule.time_slots if ts.id == time_slot_id)
            paired_slot_id = time_slot.is_lunch_pair_with

            if paired_slot_id:
                is_assigned_current = self.auxiliary_vars['is_assigned'][(teacher_id, time_slot_id)]
                is_assigned_paired = self.auxiliary_vars['is_assigned'][(teacher_id, paired_slot_id)]

                # 如果两个时间段都被分配，则违反午休保障
                self.model.Add(var >= is_assigned_current + is_assigned_paired - 1)

        # 6. 每日负荷约束
        for teacher in self.schedule.teachers:
            dates = set(ts.date for ts in self.schedule.time_slots)
            for date in dates:
                daily_terms = []
                for time_slot in self.schedule.time_slots:
                    if time_slot.date == date:
                        daily_terms.append(self.auxiliary_vars['is_assigned'][(teacher.id, time_slot.id)])

                self.model.Add(
                    self.auxiliary_vars['daily_count'][(teacher.id, date)] == sum(daily_terms)
                )

        # 7. 任务集中度约束
        for teacher in self.schedule.teachers:
            dates = set(ts.date for ts in self.schedule.time_slots)
            for date in dates:
                morning_assigned = False
                afternoon_assigned = False

                for time_slot in self.schedule.time_slots:
                    if time_slot.date == date:
                        is_assigned = self.auxiliary_vars['is_assigned'][(teacher.id, time_slot.id)]

                        if time_slot.is_morning:
                            morning_assigned = True or morning_assigned
                        elif time_slot.is_afternoon:
                            afternoon_assigned = True or afternoon_assigned

                # 如果跨越了上下午，则违反任务集中度
                split_var = self.auxiliary_vars['split_day'][(teacher.id, date)]
                # 这里需要更精确的逻辑，暂时简化
                pass

    def solve(self) -> bool:
        """求解模型"""
        print("开始求解...")
        result = self.solver.Solve(self.model)

        self.solve_time = self.solver.WallTime()
        self.objective_value = self.solver.ObjectiveValue()

        print(f"求解完成，耗时: {self.solve_time/1000:.2f}秒")
        print(f"目标函数值: {self.objective_value}")

        if result == cp_model.OPTIMAL or result == cp_model.FEASIBLE:
            print("找到可行解")
            self._extract_solution()
            return True
        else:
            print("未找到可行解")
            return False

    def _extract_solution(self):
        """提取求解结果"""
        print("提取求解结果...")
        self.assignments = []

        for teacher in self.schedule.teachers:
            for room in self.schedule.rooms:
                for time_slot in self.schedule.time_slots:
                    var = self.assign_vars[(teacher.id, room.id, time_slot.id)]
                    if self.solver.Value(var) == 1:
                        # 判断是否为监考还是自习
                        is_invigilation = self._is_invigilation_assignment(room, time_slot)

                        assignment = Assignment(
                            teacher=teacher,
                            room=room,
                            time_slot=time_slot,
                            subject=self._get_assignment_subject(room, time_slot),
                            is_invigilation=is_invigilation
                        )
                        self.assignments.append(assignment)

        print(f"提取到 {len(self.assignments)} 个监考安排")

    def _is_invigilation_assignment(self, room: Room, time_slot: TimeSlot) -> bool:
        """判断是否为监考任务"""
        # 检查该房间在该时间段是否为考场
        for exam in self.schedule.exams:
            if (exam.time_slot.id == time_slot.id and
                any(r.id == room.id for r in exam.rooms)):
                return True
        return False

    def _get_assignment_subject(self, room: Room, time_slot: TimeSlot) -> SubjectType:
        """获取安排的科目"""
        for exam in self.schedule.exams:
            if (exam.time_slot.id == time_slot.id and
                any(r.id == room.id for r in exam.rooms)):
                return exam.subject

        # 默认返回语文科目
        return SubjectType.CHINESE

    def get_schedule(self) -> ExamSchedule:
        """获取求解后的排考安排"""
        # 创建新的安排对象
        result_schedule = ExamSchedule(
            teachers=self.schedule.teachers,
            rooms=self.schedule.rooms,
            time_slots=self.schedule.time_slots,
            exams=self.schedule.exams,
            assignments=self.assignments,
            config=self.schedule.config
        )

        return result_schedule

    def print_solution_stats(self):
        """打印求解统计信息"""
        print("\n=== 求解统计信息 ===")
        print(f"求解状态: {self.solver.StatusName()}")
        print(f"求解时间: {self.solve_time/1000:.2f}秒")
        print(f"目标函数值: {self.objective_value}")

        if self.assignments:
            print(f"监考安排数量: {len(self.assignments)}")

            # 统计教师安排情况
            teacher_counts = {}
            for assignment in self.assignments:
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
        result_schedule = self.get_schedule()
        conflicts = result_schedule.check_conflicts()
        if conflicts:
            print(f"发现 {len(conflicts)} 个冲突:")
            for conflict in conflicts[:5]:  # 只显示前5个冲突
                print(f"  - {conflict}")
        else:
            print("未发现硬约束冲突")


def main():
    """测试OR-Tools求解器"""
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
    solver = ORToolsSolver(schedule)

    # 构建模型
    solver.build_model()

    # 求解
    if solver.solve():
        solver.print_solution_stats()

        # 生成统计报表
        result_schedule = solver.get_schedule()
        stats = result_schedule.generate_statistics()
        print(f"\n公平性指标:")
        print(f"最大负荷: {stats['fairness_metrics'].get('max_total_load', 0):.2f}")
        print(f"最小负荷: {stats['fairness_metrics'].get('min_total_load', 0):.2f}")
        print(f"负荷极差: {stats['fairness_metrics'].get('load_range', 0):.2f}")


if __name__ == "__main__":
    main()
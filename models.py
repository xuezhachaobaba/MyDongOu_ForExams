"""
核心数据模型定义
智能排考系统的基础数据结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum


class ExamMode(Enum):
    """考场模式"""
    ORIGINAL_CLASS = "原班考试"  # 学生在原班教室考试
    SHUFFLED = "打乱考场"       # 学生打乱分配到不同考场


class SubjectType(Enum):
    """科目类型"""
    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"
    SCIENCE = "科学"


@dataclass
class Teacher:
    """教师类"""
    id: int
    name: str
    subject: SubjectType
    grade: str  # 高一/高二/高三

    # 历史数据
    historical_load: float = 0.0  # 本学期历史核算负荷

    # 约束相关
    teaching_schedule: Dict[str, List[str]] = field(default_factory=dict)  # 授课时间表 {date: [time_slots]}
    leave_times: List[Tuple[str, str]] = field(default_factory=list)  # 请假时间 [(date, time_slot)]
    fixed_duties: List[Tuple[str, str, str]] = field(default_factory=list)  # 固定坐班 [(date, time_slot, room)]

    # 统计信息
    current_load: float = 0.0  # 本次核算负荷
    total_weighted_load: float = 0.0  # 加权总负荷
    long_exam_count: int = 0  # 长时科目监考次数

    def __hash__(self):
        return hash(self.id)


@dataclass
class Room:
    """考场类"""
    id: int
    name: str
    capacity: int
    building: str = ""
    floor: str = ""


@dataclass
class TimeSlot:
    """时间段类"""
    id: str
    name: str
    date: str
    start_time: str
    end_time: str
    duration_minutes: int

    # 时间关系
    is_morning: bool = False
    is_afternoon: bool = False
    is_lunch_pair_with: Optional[str] = None  # 午休配对的时间段ID

    def __hash__(self):
        return hash(self.id)


@dataclass
class Exam:
    """考试类"""
    subject: SubjectType
    time_slot: TimeSlot
    rooms: List[Room]  # 该科目使用的考场列表
    is_long_subject: bool = False  # 是否为长时科目

    def get_total_rooms(self) -> int:
        """获取考场总数"""
        return len(self.rooms)


@dataclass
class Assignment:
    """监考安排类"""
    teacher: Teacher
    room: Room
    time_slot: TimeSlot
    subject: SubjectType
    is_invigilation: bool = True  # True: 监考, False: 自习坐班

    def __hash__(self):
        return hash((self.teacher.id, self.room.id, self.time_slot.id))


@dataclass
class ConstraintConfig:
    """约束配置"""
    # 负荷系数 (S-E-02)
    invigilation_coefficient: float = 1.0  # 监考负荷系数
    study_coefficient: float = 0.5         # 自习坐班负荷系数

    # 历史权重 (S-E-01)
    current_weight: float = 0.5           # 本次负荷权重
    historical_weight: float = 0.5        # 历史负荷权重

    # 软约束权重
    fairness_weight: float = 1000.0       # 公平性权重
    long_exam_weight: float = 100.0      # 长时科目平衡权重
    lunch_weight: float = 200.0           # 午休保障权重
    daily_limit_weight: float = 50.0     # 每日负荷权重
    concentration_weight: float = 30.0    # 任务集中度权重

    # 其他参数
    daily_comfort_limit: int = 2         # 每日舒适负荷上限 (S-E-06)
    lunch_break_duration: int = 90        # 午休时间(分钟)


@dataclass
class ExamSchedule:
    """考试安排总表"""
    teachers: List[Teacher] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    time_slots: List[TimeSlot] = field(default_factory=list)
    exams: List[Exam] = field(default_factory=list)
    assignments: List[Assignment] = field(default_factory=list)
    config: ConstraintConfig = field(default_factory=ConstraintConfig)

    # 索引映射
    teacher_map: Dict[int, Teacher] = field(default_factory=dict)
    room_map: Dict[int, Room] = field(default_factory=dict)
    time_slot_map: Dict[str, TimeSlot] = field(default_factory=dict)

    def __post_init__(self):
        """初始化索引映射"""
        self.teacher_map = {t.id: t for t in self.teachers}
        self.room_map = {r.id: r for r in self.rooms}
        self.time_slot_map = {ts.id: ts for ts in self.time_slots}

    def get_teacher_assignments(self, teacher_id: int) -> List[Assignment]:
        """获取某个教师的所有监考安排"""
        return [a for a in self.assignments if a.teacher.id == teacher_id]

    def get_room_assignments(self, room_id: int) -> List[Assignment]:
        """获取某个考场的所有监考安排"""
        return [a for a in self.assignments if a.room.id == room_id]

    def get_time_slot_assignments(self, time_slot_id: str) -> List[Assignment]:
        """获取某个时间段的所有监考安排"""
        return [a for a in self.assignments if a.time_slot.id == time_slot_id]

    def check_conflicts(self) -> List[str]:
        """检查硬约束冲突"""
        conflicts = []

        # H-E-01: 教师在同一时间只能监考一个考场
        for teacher in self.teachers:
            teacher_assignments = self.get_teacher_assignments(teacher.id)
            time_slot_counts = {}
            for assignment in teacher_assignments:
                ts_id = assignment.time_slot.id
                time_slot_counts[ts_id] = time_slot_counts.get(ts_id, 0) + 1

            for ts_id, count in time_slot_counts.items():
                if count > 1:
                    conflicts.append(f"教师{teacher.name}在时间段{ts_id}有{count}个监考任务")

        # H-E-01: 考场在同一时间只能有一场考试
        for room in self.rooms:
            room_assignments = self.get_room_assignments(room.id)
            time_slot_counts = {}
            for assignment in room_assignments:
                ts_id = assignment.time_slot.id
                time_slot_counts[ts_id] = time_slot_counts.get(ts_id, 0) + 1

            for ts_id, count in time_slot_counts.items():
                if count > 1:
                    conflicts.append(f"考场{room.name}在时间段{ts_id}有{count}个监考任务")

        return conflicts

    def calculate_teacher_load(self, teacher_id: int) -> Tuple[float, float, float]:
        """计算教师的负荷：(本次负荷, 历史负荷, 加权总负荷)"""
        teacher = self.teacher_map[teacher_id]
        assignments = self.get_teacher_assignments(teacher_id)

        # 计算本次负荷
        current_load = 0.0
        long_exam_count = 0

        for assignment in assignments:
            duration = assignment.time_slot.duration_minutes

            if assignment.is_invigilation:
                current_load += duration * self.config.invigilation_coefficient
                # 检查是否为长时科目
                if any(e.subject == assignment.subject and e.is_long_subject
                      for e in self.exams):
                    long_exam_count += 1
            else:
                current_load += duration * self.config.study_coefficient

        # 计算加权总负荷
        total_weighted = (self.config.current_weight * current_load +
                          self.config.historical_weight * teacher.historical_load)

        return current_load, teacher.historical_load, total_weighted

    def generate_statistics(self) -> Dict:
        """生成统计报表"""
        stats = {
            'teacher_stats': [],
            'constraint_stats': {},
            'fairness_metrics': {}
        }

        all_loads = []
        all_total_loads = []

        for teacher in self.teachers:
            current_load, historical_load, total_load = self.calculate_teacher_load(teacher.id)
            all_loads.append(current_load)
            all_total_loads.append(total_load)

            stats['teacher_stats'].append({
                'teacher_id': teacher.id,
                'teacher_name': teacher.name,
                'subject': teacher.subject.value,
                'current_load': current_load,
                'historical_load': historical_load,
                'total_weighted_load': total_load,
                'assignment_count': len(self.get_teacher_assignments(teacher.id)),
                'long_exam_count': self._count_long_exams(teacher.id)
            })

        # 公平性指标
        if all_total_loads:
            max_load = max(all_total_loads)
            min_load = min(all_total_loads)
            avg_load = sum(all_total_loads) / len(all_total_loads)

            stats['fairness_metrics'] = {
                'max_total_load': max_load,
                'min_total_load': min_load,
                'avg_total_load': avg_load,
                'load_range': max_load - min_load,
                'load_std': self._calculate_std(all_total_loads)
            }

        # 冲突检查
        conflicts = self.check_conflicts()
        stats['constraint_stats'] = {
            'conflict_count': len(conflicts),
            'conflicts': conflicts
        }

        return stats

    def _count_long_exams(self, teacher_id: int) -> int:
        """统计教师的长时科目监考次数"""
        assignments = self.get_teacher_assignments(teacher_id)
        count = 0
        for assignment in assignments:
            if (assignment.is_invigilation and
                any(e.subject == assignment.subject and e.is_long_subject
                    for e in self.exams)):
                count += 1
        return count

    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) <= 1:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
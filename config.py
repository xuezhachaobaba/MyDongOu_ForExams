#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理
集中管理所有硬编码值，避免分散在各文件中
"""

from datetime import datetime
import os
from typing import Dict, List, Tuple
from models import SubjectType


class ExamConfig:
    """考试相关配置"""

    # 考试时长配置（分钟）
    EXAM_DURATION: Dict[str, int] = {
        '语文': 150,
        '数学': 120,
        '外语': 120,
        '英语': 120,
        '物理': 90,
        '化学': 90,
        '生物': 90,
        '历史': 90,
        '地理': 90,
        '政治': 90,
        '技术': 90
    }

    # 长时科目
    LONG_SUBJECTS: set = {
        SubjectType.CHINESE, SubjectType.MATH, SubjectType.ENGLISH
    }

    # 时间段配置
    TIME_SLOTS: Dict[str, Tuple[str, str]] = {
        '上午': ('07:30', '12:00'),
        '下午': ('13:30', '17:25'),
        '晚上': ('19:30', '21:00')
    }

    # 考试间隔时间（分钟）
    EXAM_INTERVAL: int = 20

    # 时间段模板（用于排考系统）
    TIME_SLOT_TEMPLATES: Dict[str, Dict[str, str]] = {
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


class SubjectConfig:
    """科目相关配置"""

    # 科目名称映射
    SUBJECT_MAPPING: Dict[str, SubjectType] = {
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

    # 反向映射（SubjectType -> 中文）
    REVERSE_SUBJECT_MAPPING: Dict[SubjectType, str] = {
        SubjectType.CHINESE: "语文",
        SubjectType.MATH: "数学",
        SubjectType.ENGLISH: "英语",
        SubjectType.PHYSICS: "物理",
        SubjectType.CHEMISTRY: "化学",
        SubjectType.BIOLOGY: "生物",
        SubjectType.HISTORY: "历史",
        SubjectType.GEOGRAPHY: "地理",
        SubjectType.POLITICS: "政治",
        SubjectType.SCIENCE: "技术"
    }

    # 年级科目分配
    GRADE_SUBJECT_MAPPING: Dict[str, List[str]] = {
        "高三": ["语文", "数学", "英语"],
        "高二": ["物理", "化学", "生物"],
        "高一": ["历史", "地理", "政治"]
    }


class DataConfig:
    """数据生成配置"""

    # 基础参数
    STUDENT_COUNT_PER_CLASS: int = 40
    CLASSES_PER_GRADE: int = 10
    TEACHERS_PER_SUBJECT: int = 8

    # 考场配置
    ROOM_CAPACITY_SMALL: int = 30
    ROOM_CAPACITY_MEDIUM: int = 40
    ROOM_CAPACITY_LARGE: int = 50

    # 教师配置
    HISTORICAL_LOAD_MIN: float = 100.0
    HISTORICAL_LOAD_MAX: float = 500.0
    TEACHING_LOAD_RATIO: float = 0.3

    # 时间参数
    LUNCH_START_TIME: str = "12:00"
    LUNCH_END_TIME: str = "14:00"

    # 分配策略
    ROOM_ALLOCATION_STRATEGY: str = "grade_based"
    TEACHER_DISTRIBUTION_STRATEGY: str = "balanced"


class ConstraintConfig:
    """约束配置"""

    # 负荷系数
    INVIGILATION_COEFFICIENT: float = 1.0  # 监考负荷系数
    STUDY_COEFFICIENT: float = 0.5         # 自习坐班负荷系数

    # 历史权重
    CURRENT_WEIGHT: float = 0.5           # 本次负荷权重
    HISTORICAL_WEIGHT: float = 0.5        # 历史负荷权重

    # 软约束权重
    FAIRNESS_WEIGHT: float = 1000.0       # 公平性权重
    LONG_EXAM_WEIGHT: float = 100.0      # 长时科目平衡权重
    LUNCH_WEIGHT: float = 200.0           # 午休保障权重
    DAILY_LIMIT_WEIGHT: float = 50.0     # 每日负荷权重
    CONCENTRATION_WEIGHT: float = 30.0    # 任务集中度权重

    # 其他参数
    DAILY_COMFORT_LIMIT: int = 2         # 每日舒适负荷上限
    LUNCH_BREAK_DURATION: int = 90        # 午休时间(分钟)


class PathConfig:
    """文件路径配置"""

    # 目录配置
    DATA_DIR: str = "process_data"
    OUTPUT_DIR: str = "output"

    # 文件名配置
    TEACHERS_FILE: str = "teachers.json"
    ROOMS_FILE: str = "rooms.json"
    EXAM_SCHEDULE_FILE: str = "exam_schedule.json"
    INTERMEDIATE_EXAM_FILE: str = "intermediate_exam_schedule.json"
    CONVERTED_DATA_FILE: str = "converted_schedule.json"
    EXAM_TABLE_FILE: str = "考试安排表.txt"

    @classmethod
    def get_full_path(cls, filename: str) -> str:
        """获取文件完整路径"""
        if filename in [cls.TEACHERS_FILE, cls.ROOMS_FILE,
                       cls.EXAM_SCHEDULE_FILE, cls.INTERMEDIATE_EXAM_FILE,
                       cls.CONVERTED_DATA_FILE, cls.EXAM_TABLE_FILE]:
            return os.path.join(cls.DATA_DIR, filename)
        elif filename.startswith("监考安排表") or filename.startswith("comprehensive_report") or filename.startswith("load_distribution"):
            return os.path.join(cls.OUTPUT_DIR, filename)
        else:
            return filename

    @classmethod
    def get_teachers_file(cls) -> str:
        return cls.get_full_path(cls.TEACHERS_FILE)

    @classmethod
    def get_rooms_file(cls) -> str:
        return cls.get_full_path(cls.ROOMS_FILE)

    @classmethod
    def get_exam_schedule_file(cls) -> str:
        return cls.get_full_path(cls.EXAM_SCHEDULE_FILE)

    @classmethod
    def get_intermediate_exam_file(cls) -> str:
        return cls.get_full_path(cls.INTERMEDIATE_EXAM_FILE)

    @classmethod
    def get_converted_data_file(cls) -> str:
        return cls.get_full_path(cls.CONVERTED_DATA_FILE)

    @classmethod
    def get_exam_table_file(cls) -> str:
        return cls.get_full_path(cls.EXAM_TABLE_FILE)


class SystemConfig:
    """系统运行配置"""

    # 算法配置
    DEFAULT_TIME_LIMIT: int = 60  # 求解时间限制（秒）
    POPULATION_SIZE: int = 200    # 遗传算法种群大小
    GENERATIONS: int = 100         # 遗传算法迭代次数

    # 随机种子
    RANDOM_SEED: int = 42

    # 默认日期配置
    DEFAULT_BASE_DATE: str = "2024-01-15"

    # 年级列表
    GRADES: List[str] = ["高一", "高二", "高三"]

    # 教学时间段（用于生成教师授课表）
    TEACHING_SLOTS: List[str] = ["第1节", "第2节", "第3节", "第4节",
                                 "第5节", "第6节", "第7节", "第8节", "第9节"]


# 便捷访问函数
def get_exam_duration(subject: str) -> int:
    """获取科目考试时长"""
    return ExamConfig.EXAM_DURATION.get(subject, 120)


def get_subject_type(subject_name: str) -> SubjectType:
    """获取科目枚举类型"""
    return SubjectConfig.SUBJECT_MAPPING.get(subject_name, SubjectType.CHINESE)


def get_subject_name(subject_type: SubjectType) -> str:
    """获取科目中文名称"""
    return SubjectConfig.REVERSE_SUBJECT_MAPPING.get(subject_type, "语文")


def is_long_subject(subject_type: SubjectType) -> bool:
    """判断是否为长时科目"""
    return subject_type in ExamConfig.LONG_SUBJECTS


def get_time_slots() -> Dict[str, Tuple[str, str]]:
    """获取时间段配置"""
    return ExamConfig.TIME_SLOTS.copy()


def calculate_slot_duration(slot_name: str) -> int:
    """计算时间段可用总时长（分钟）"""
    if slot_name not in ExamConfig.TIME_SLOTS:
        return 0

    start_str, end_str = ExamConfig.TIME_SLOTS[slot_name]
    start = datetime.strptime(start_str, '%H:%M')
    end = datetime.strptime(end_str, '%H:%M')
    return int((end - start).total_seconds() / 60)


class ConversionConfig:
    """转换配置（从schedule_converter.py迁移）"""

    # 基础参数
    student_count_per_class: int = DataConfig.STUDENT_COUNT_PER_CLASS
    classes_per_grade: int = DataConfig.CLASSES_PER_GRADE
    teachers_per_subject: int = DataConfig.TEACHERS_PER_SUBJECT

    # 时间参数
    exam_interval_minutes: int = ExamConfig.EXAM_INTERVAL
    lunch_start_time: str = DataConfig.LUNCH_START_TIME
    lunch_end_time: str = DataConfig.LUNCH_END_TIME

    # 考场配置
    room_capacity_small: int = DataConfig.ROOM_CAPACITY_SMALL
    room_capacity_medium: int = DataConfig.ROOM_CAPACITY_MEDIUM
    room_capacity_large: int = DataConfig.ROOM_CAPACITY_LARGE

    # 教师配置
    historical_load_min: float = DataConfig.HISTORICAL_LOAD_MIN
    historical_load_max: float = DataConfig.HISTORICAL_LOAD_MAX
    teaching_load_ratio: float = DataConfig.TEACHING_LOAD_RATIO

    # 分配策略
    room_allocation_strategy: str = DataConfig.ROOM_ALLOCATION_STRATEGY
    teacher_distribution_strategy: str = DataConfig.TEACHER_DISTRIBUTION_STRATEGY
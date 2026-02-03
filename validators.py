#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据验证逻辑
将分散在各文件中的验证逻辑统一到基类中
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

from config import ExamConfig, get_exam_duration
from utils import TimeUtils, ValidationUtils, FileUtils


class BaseValidator:
    """基础验证器"""

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str],
                               context: str = "数据") -> Tuple[bool, List[str]]:
        """验证必填字段"""
        errors = []

        for field in required_fields:
            if field not in data:
                errors.append(f"{context}缺少必填字段: {field}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_data_types(data: Dict[str, Any], type_rules: Dict[str, type],
                          context: str = "数据") -> Tuple[bool, List[str]]:
        """验证数据类型"""
        errors = []

        for field, expected_type in type_rules.items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(f"{context}字段{field}类型错误，期望{expected_type.__name__}，实际{type(data[field]).__name__}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_value_range(value: Union[int, float], min_val: Optional[float] = None,
                           max_val: Optional[float] = None, field_name: str = "字段") -> Optional[str]:
        """验证数值范围"""
        if min_val is not None and value < min_val:
            return f"{field_name}值{value}小于最小值{min_val}"
        if max_val is not None and value > max_val:
            return f"{field_name}值{value}大于最大值{max_val}"
        return None


class ExamScheduleValidator(BaseValidator):
    """考试安排验证器"""

    def __init__(self):
        self.required_fields = ['date', 'time_slot', 'subject', 'start_time', 'end_time', 'duration']
        self.type_rules = {
            'date': str,
            'time_slot': str,
            'subject': str,
            'start_time': str,
            'end_time': str,
            'duration': int
        }

    def validate_single_exam(self, exam: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证单个考试"""
        errors = []

        # 验证必填字段
        has_required, field_errors = self.validate_required_fields(exam, self.required_fields, "考试记录")
        errors.extend(field_errors)

        if not has_required:
            return False, errors

        # 验证数据类型
        has_correct_types, type_errors = self.validate_data_types(exam, self.type_rules, "考试记录")
        errors.extend(type_errors)

        # 验证日期格式
        date_error = self._validate_date_format(exam['date'])
        if date_error:
            errors.append(date_error)

        # 验证时间格式
        time_errors = self._validate_time_format(exam['start_time'], exam['end_time'])
        errors.extend(time_errors)

        # 验证时长合理性
        duration_error = self._validate_duration(exam['subject'], exam['duration'])
        if duration_error:
            errors.append(duration_error)

        # 验证时间逻辑
        logic_error = self._validate_time_logic(exam['start_time'], exam['end_time'])
        if logic_error:
            errors.append(logic_error)

        return len(errors) == 0, errors

    def _validate_date_format(self, date_str: str) -> Optional[str]:
        """验证日期格式（第X天）"""
        if not date_str.startswith('第') or not date_str.endswith('天'):
            return f"日期格式错误: {date_str}，应为'第X天'格式"
        return None

    def _validate_time_format(self, start_time: str, end_time: str) -> List[str]:
        """验证时间格式"""
        errors = []

        if not TimeUtils.validate_time_format(start_time):
            errors.append(f"开始时间格式错误: {start_time}，应为HH:MM格式")

        if not TimeUtils.validate_time_format(end_time):
            errors.append(f"结束时间格式错误: {end_time}，应为HH:MM格式")

        return errors

    def _validate_duration(self, subject: str, duration: int) -> Optional[str]:
        """验证考试时长"""
        expected_duration = get_exam_duration(subject)
        if abs(duration - expected_duration) > 30:  # 允许30分钟误差
            return f"考试时长异常: {subject} 实际{duration}分钟，期望{expected_duration}分钟"
        return None

    def _validate_time_logic(self, start_time: str, end_time: str) -> Optional[str]:
        """验证时间逻辑"""
        start_minutes = TimeUtils.calculate_duration("00:00", start_time)
        end_minutes = TimeUtils.calculate_duration("00:00", end_time)

        if start_minutes >= end_minutes:
            return f"时间逻辑错误: 开始时间{start_time}不能晚于或等于结束时间{end_time}"

        return None

    def validate_schedule(self, exam_schedule: List[Dict[str, Any]]) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
        """验证完整考试安排"""
        all_errors = []
        validated_schedule = []

        for i, exam in enumerate(exam_schedule):
            is_valid, errors = self.validate_single_exam(exam)

            if is_valid:
                validated_schedule.append(exam)
            else:
                error_prefix = f"考试{i+1}({exam.get('subject', 'unknown')}):"
                all_errors.extend([f"{error_prefix} {error}" for error in errors])

        # 验证时间冲突
        conflict_errors = self._check_time_conflicts(validated_schedule)
        all_errors.extend(conflict_errors)

        return len(all_errors) == 0, all_errors, validated_schedule

    def _check_time_conflicts(self, exam_schedule: List[Dict[str, Any]]) -> List[str]:
        """检查时间冲突"""
        conflicts = []
        schedule_by_day = {}

        # 按日期分组
        for exam in exam_schedule:
            date = exam['date']
            if date not in schedule_by_day:
                schedule_by_day[date] = []
            schedule_by_day[date].append(exam)

        # 检查每日时间冲突
        for date, daily_exams in schedule_by_day.items():
            for i, exam1 in enumerate(daily_exams):
                for exam2 in daily_exams[i+1:]:
                    if self._has_time_overlap(exam1, exam2):
                        conflicts.append(
                            f"时间冲突: {date} {exam1['subject']}({exam1['start_time']}-{exam1['end_time']}) "
                            f"与 {exam2['subject']}({exam2['start_time']}-{exam2['end_time']}) 重叠"
                        )

        return conflicts

    def _has_time_overlap(self, exam1: Dict[str, Any], exam2: Dict[str, Any]) -> bool:
        """检查两个考试是否有时间重叠"""
        start1 = TimeUtils.calculate_duration("00:00", exam1['start_time'])
        end1 = TimeUtils.calculate_duration("00:00", exam1['end_time'])
        start2 = TimeUtils.calculate_duration("00:00", exam2['start_time'])
        end2 = TimeUtils.calculate_duration("00:00", exam2['end_time'])

        return not (end1 <= start2 or end2 <= start1)


class DataFileValidator(BaseValidator):
    """数据文件验证器"""

    @staticmethod
    def validate_teachers_file(teachers_file: str) -> Tuple[bool, List[str], Optional[List[Dict[str, Any]]]]:
        """验证教师数据文件"""
        errors = []

        teachers_data = FileUtils.load_json(teachers_file)
        if not teachers_data:
            errors.append("教师数据文件不存在或无效")
            return False, errors, None
        if not isinstance(teachers_data, list):
            errors.append("教师数据格式错误，应为列表")
            return False, errors, None

        if len(teachers_data) == 0:
            errors.append("教师数据为空")
            return False, errors, None

        # 验证教师记录
        for i, teacher in enumerate(teachers_data):
            teacher_errors = DataFileValidator._validate_teacher_record(teacher, i)
            errors.extend(teacher_errors)

        return len(errors) == 0, errors, teachers_data

    @staticmethod
    def _validate_teacher_record(teacher: Dict[str, Any], index: int) -> List[str]:
        """验证单个教师记录"""
        errors = []
        required_fields = ['id', 'name', 'subject', 'grade', 'historical_load']

        # 检查必填字段
        for field in required_fields:
            if field not in teacher:
                errors.append(f"教师{index+1}缺少必填字段: {field}")

        # 检查ID
        if 'id' in teacher and not isinstance(teacher['id'], int):
            errors.append(f"教师{index+1}的ID应为整数")

        # 检查历史负荷
        if 'historical_load' in teacher:
            if not isinstance(teacher['historical_load'], (int, float)):
                errors.append(f"教师{index+1}的历史负荷应为数值")
            elif teacher['historical_load'] < 0:
                errors.append(f"教师{index+1}的历史负荷不能为负数")

        return errors

    @staticmethod
    def validate_rooms_file(rooms_file: str) -> Tuple[bool, List[str], Optional[List[Dict[str, Any]]]]:
        """验证考场数据文件"""
        errors = []

        rooms_data = FileUtils.load_json(rooms_file)
        if not rooms_data:
            errors.append("考场数据文件不存在或无效")
            return False, errors, None

        rooms_data = FileUtils.load_json(rooms_file)
        if not isinstance(rooms_data, list):
            errors.append("考场数据格式错误，应为列表")
            return False, errors, None

        if len(rooms_data) == 0:
            errors.append("考场数据为空")
            return False, errors, None

        # 验证考场记录
        for i, room in enumerate(rooms_data):
            room_errors = DataFileValidator._validate_room_record(room, i)
            errors.extend(room_errors)

        return len(errors) == 0, errors, rooms_data

    @staticmethod
    def _validate_room_record(room: Dict[str, Any], index: int) -> List[str]:
        """验证单个考场记录"""
        errors = []
        required_fields = ['id', 'name', 'capacity']

        # 检查必填字段
        for field in required_fields:
            if field not in room:
                errors.append(f"考场{index+1}缺少必填字段: {field}")

        # 检查ID
        if 'id' in room and not isinstance(room['id'], int):
            errors.append(f"考场{index+1}的ID应为整数")

        # 检查容量
        if 'capacity' in room:
            if not isinstance(room['capacity'], int):
                errors.append(f"考场{index+1}的容量应为整数")
            elif room['capacity'] <= 0:
                errors.append(f"考场{index+1}的容量必须大于0")

        return errors


class ConversionValidator(BaseValidator):
    """转换过程验证器"""

    @staticmethod
    def validate_conversion_result(teachers: List, rooms: List, time_slots: List,
                                exams: List) -> Tuple[bool, List[str]]:
        """验证转换结果"""
        errors = []

        # 验证教师数量
        if len(teachers) == 0:
            errors.append("转换结果：教师数量为0")
        elif len(teachers) < 10:
            errors.append(f"转换结果：教师数量过少({len(teachers)}人)")

        # 验证考场数量
        if len(rooms) == 0:
            errors.append("转换结果：考场数量为0")
        elif len(rooms) < 5:
            errors.append(f"转换结果：考场数量过少({len(rooms)}个)")

        # 验证时间段数量
        if len(time_slots) == 0:
            errors.append("转换结果：时间段数量为0")

        # 验证考试数量
        if len(exams) == 0:
            errors.append("转换结果：考试数量为0")

        # 验证时间段与考试的关系
        if len(exams) > 0 and len(time_slots) > 0:
            exam_time_slot_ids = set(exam.time_slot.id for exam in exams)
            time_slot_ids = set(slot.id for slot in time_slots)

            missing_slots = exam_time_slot_ids - time_slot_ids
            if missing_slots:
                errors.append(f"转换结果：考试使用的时间段不存在: {missing_slots}")

        # 验证考场与考试的关系
        if len(exams) > 0:
            exam_room_ids = set()
            for exam in exams:
                for room in exam.rooms:
                    exam_room_ids.add(room.id)

            room_ids = set(room.id for room in rooms)
            missing_rooms = exam_room_ids - room_ids
            if missing_rooms:
                errors.append(f"转换结果：考试使用的考场不存在: {missing_rooms}")

        return len(errors) == 0, errors


# 便捷函数
def validate_all_data_files(teachers_file: str, rooms_file: str) -> Tuple[bool, List[str]]:
    """验证所有数据文件"""
    all_errors = []

    # 验证教师文件
    is_valid, teacher_errors, _ = DataFileValidator.validate_teachers_file(teachers_file)
    if not is_valid:
        all_errors.extend([f"教师文件: {error}" for error in teacher_errors])

    # 验证考场文件
    is_valid, room_errors, _ = DataFileValidator.validate_rooms_file(rooms_file)
    if not is_valid:
        all_errors.extend([f"考场文件: {error}" for error in room_errors])

    return len(all_errors) == 0, all_errors


def create_exam_schedule_validator() -> ExamScheduleValidator:
    """创建考试安排验证器实例"""
    return ExamScheduleValidator()
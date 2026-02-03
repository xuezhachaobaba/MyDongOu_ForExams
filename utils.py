#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共工具函数
提取各文件中重复的工具函数，统一管理
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

from models import Teacher, Room, SubjectType
from config import SubjectConfig, PathConfig, get_exam_duration


class TimeUtils:
    """时间处理工具类"""

    @staticmethod
    def calculate_duration(start: str, end: str) -> int:
        """计算时间差（分钟）"""
        try:
            start_hour, start_min = map(int, start.split(":"))
            end_hour, end_min = map(int, end.split(":"))

            start_dt = datetime.strptime(f"{start_hour:02d}:{start_min:02d}", "%H:%M")
            end_dt = datetime.strptime(f"{end_hour:02d}:{end_min:02d}", "%H:%M")

            duration = (end_dt - start_dt).total_seconds() / 60
            return int(duration)
        except Exception as e:
            print(f"时间计算错误 {start}-{end}: {e}")
            return 0

    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """验证时间格式是否为HH:MM"""
        time_pattern = re.compile(r'^\d{2}:\d{2}$')
        return bool(time_pattern.match(time_str))

    @staticmethod
    def normalize_time_slot_name(period: str, start_time: str, end_time: str) -> str:
        """标准化时间段名称"""
        return f"{period}_{start_time}-{end_time}"

    @staticmethod
    def parse_day_number(date_str: str) -> int:
        """从"第X天"格式中提取天数"""
        return int(date_str.replace('第', '').replace('天', ''))

    @staticmethod
    def calculate_actual_date(base_date: str, day_num: int) -> str:
        """计算实际日期"""
        base_dt = datetime.strptime(base_date, "%Y-%m-%d")
        actual_date = (base_dt + timedelta(days=day_num-1)).strftime("%Y-%m-%d")
        return actual_date


class FileUtils:
    """文件处理工具类"""

    @staticmethod
    def ensure_directory(directory: str) -> None:
        """确保目录存在"""
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def load_json(file_path: str, encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
        """安全加载JSON文件"""
        try:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return None

            with open(file_path, 'r', encoding=encoding) as f:
                return json.load(f)
        except Exception as e:
            print(f"加载JSON文件失败 {file_path}: {e}")
            return None

    @staticmethod
    def save_json(data: Any, file_path: str, encoding: str = 'utf-8', indent: int = 2) -> bool:
        """安全保存JSON文件"""
        try:
            # 确保目录存在
            FileUtils.ensure_directory(os.path.dirname(file_path))

            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
            return True
        except Exception as e:
            print(f"保存JSON文件失败 {file_path}: {e}")
            return False

    @staticmethod
    def read_text_file(file_path: str, encoding: str = 'utf-8') -> Optional[List[str]]:
        """读取文本文件"""
        try:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return None

            with open(file_path, 'r', encoding=encoding) as f:
                return f.readlines()
        except Exception as e:
            print(f"读取文本文件失败 {file_path}: {e}")
            return None

    @staticmethod
    def save_text_file(content: str, file_path: str, encoding: str = 'utf-8') -> bool:
        """保存文本文件"""
        try:
            FileUtils.ensure_directory(os.path.dirname(file_path))

            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"保存文本文件失败 {file_path}: {e}")
            return False


class DataUtils:
    """数据处理工具类"""

    @staticmethod
    def convert_to_teachers(teacher_data: List[Dict[str, Any]]) -> List[Teacher]:
        """转换教师数据为Teacher对象"""
        teachers = []

        for teacher_dict in teacher_data:
            try:
                # 获取科目类型
                subject_name = teacher_dict.get('subject', '')
                if isinstance(subject_name, str):
                    subject_type = SubjectConfig.SUBJECT_MAPPING.get(subject_name, SubjectType.CHINESE)
                else:
                    # 如果已经是SubjectType枚举，直接使用
                    subject_type = subject_name

                teacher = Teacher(
                    id=teacher_dict['id'],
                    name=teacher_dict['name'],
                    subject=subject_type,
                    grade=teacher_dict.get('grade', '高一'),
                    historical_load=teacher_dict.get('historical_load', 0.0),
                    teaching_schedule=teacher_dict.get('teaching_schedule', {}),
                    leave_times=teacher_dict.get('leave_times', []),
                    fixed_duties=teacher_dict.get('fixed_duties', [])
                )
                teachers.append(teacher)
            except Exception as e:
                print(f"转换教师数据失败 {teacher_dict.get('id', 'unknown')}: {e}")
                continue

        return teachers

    @staticmethod
    def convert_to_rooms(room_data: List[Dict[str, Any]]) -> List[Room]:
        """转换考场数据为Room对象"""
        rooms = []

        for room_dict in room_data:
            try:
                room = Room(
                    id=room_dict['id'],
                    name=room_dict['name'],
                    capacity=room_dict['capacity'],
                    building=room_dict.get('building', '教学楼'),
                    floor=room_dict.get('floor', '1')
                )
                rooms.append(room)
            except Exception as e:
                print(f"转换考场数据失败 {room_dict.get('id', 'unknown')}: {e}")
                continue

        return rooms

    @staticmethod
    def object_to_dict(obj: Any) -> Dict[str, Any]:
        """对象转字典，支持dataclass"""
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return {}

    @staticmethod
    def unique_list(items: List[Any]) -> List[Any]:
        """列表去重，保持顺序"""
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)
        return unique_items


class ValidationUtils:
    """验证工具类"""

    @staticmethod
    def validate_exam_schedule(exam_schedule: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证考试安排的合理性"""
        validated_schedule = []

        for exam in exam_schedule:
            try:
                # 验证必填字段
                required_fields = ['date', 'time_slot', 'subject', 'start_time', 'end_time', 'duration']
                if not all(field in exam for field in required_fields):
                    print(f"⚠️ 警告：考试记录缺少必填字段，已跳过: {exam}")
                    continue

                # 验证时间格式
                if not (TimeUtils.validate_time_format(exam['start_time']) and
                       TimeUtils.validate_time_format(exam['end_time'])):
                    print(f"⚠️ 警告：时间格式不正确，已跳过: {exam['start_time']}-{exam['end_time']}")
                    continue

                # 验证时长合理性
                expected_duration = get_exam_duration(exam['subject'])
                actual_duration = exam.get('duration', 0)
                if abs(actual_duration - expected_duration) > 30:  # 允许30分钟误差
                    print(f"⚠️ 警告：考试时长异常，已跳过: {exam['subject']} {actual_duration}分钟")
                    continue

                validated_schedule.append(exam)

            except Exception as e:
                print(f"⚠️ 警告：验证考试记录失败，已跳过: {exam.get('subject', 'unknown')} - {e}")
                continue

        return validated_schedule

    @staticmethod
    def validate_data_files(teachers_file: str, rooms_file: str) -> bool:
        """验证基础数据文件是否存在且有效"""
        try:
            teachers_data = FileUtils.load_json(teachers_file)
            rooms_data = FileUtils.load_json(rooms_file)

            if not teachers_data or not rooms_data:
                print("❌ 基础数据文件不存在或为空")
                return False

            if not isinstance(teachers_data, list) or not isinstance(rooms_data, list):
                print("❌ 基础数据文件格式不正确")
                return False

            print(f"✅ 验证通过：{len(teachers_data)}名教师，{len(rooms_data)}个考场")
            return True

        except Exception as e:
            print(f"❌ 验证基础数据文件失败: {e}")
            return False


class ParseUtils:
    """解析工具类"""

    @staticmethod
    def parse_exam_schedule_from_text(file_path: str) -> List[Dict[str, Any]]:
        """从文本文件解析考试安排"""
        lines = FileUtils.read_text_file(file_path)
        if not lines:
            return []

        exam_schedule = []

        try:
            # 跳过标题行，找到数据开始位置
            data_start = 0
            for i, line in enumerate(lines):
                if "日期" in line and "时间段" in line and "科目" in line:
                    data_start = i + 2  # 跳过分隔线和表头
                    break

            # 解析数据行
            for line in lines[data_start:]:
                line = line.strip()
                if not line or not ('第' in line and '天' in line):
                    continue

                # 过滤空字符串，处理多空格分隔问题
                parts = [p for p in line.split() if p.strip()]

                # 实际格式: "第1天      上午       语文       07:30      10:00      150"
                if len(parts) >= 6:
                    date_part = parts[0]
                    time_slot_part = parts[1]
                    subject_part = parts[2]
                    start_time = parts[3]
                    end_time = parts[4]

                    # 验证时间格式
                    if not (TimeUtils.validate_time_format(start_time) and
                           TimeUtils.validate_time_format(end_time)):
                        print(f"⚠️ 警告：时间格式不正确 {start_time}-{end_time}，使用默认时间")
                        start_time, end_time = '07:30', '09:30'

                    # 解析时长
                    try:
                        duration = int(parts[5])
                    except (ValueError, IndexError):
                        duration = get_exam_duration(subject_part)

                    exam_schedule.append({
                        'date': date_part,
                        'time_slot': time_slot_part,
                        'subject': subject_part,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration
                    })
                else:
                    print(f"⚠️ 警告：跳过格式不正确的行: {line}")

            print(f"解析出 {len(exam_schedule)} 场考试")
            return exam_schedule

        except Exception as e:
            print(f"解析考试安排表失败: {e}")
            return []


class ModelUtils:
    """模型工具类"""

    @staticmethod
    def serialize_schedule_data(teachers: List[Teacher],
                            rooms: List[Room],
                            time_slots: List[Any],
                            exams: List[Any],
                            config: Any) -> Dict[str, Any]:
        """序列化排考系统数据"""
        return {
            'teachers': [DataUtils.object_to_dict(t) for t in teachers],
            'rooms': [DataUtils.object_to_dict(r) for r in rooms],
            'time_slots': [DataUtils.object_to_dict(ts) for ts in time_slots],
            'exams': [DataUtils.object_to_dict(e) for e in exams],
            'config': DataUtils.object_to_dict(config)
        }

    @staticmethod
    def create_intermediate_exam_schedule(exam_schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建中间考试安排数据"""
        return {
            'version': '1.0',
            'generated_time': datetime.now().isoformat(),
            'source': 'exam_arrangement',
            'exam_count': len(exam_schedule),
            'exam_schedule': exam_schedule
        }


# 便捷函数
def validate_files_exist(*file_paths: str) -> bool:
    """验证多个文件是否存在"""
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
    return True


def get_project_root() -> str:
    """获取项目根目录"""
    return os.getcwd()
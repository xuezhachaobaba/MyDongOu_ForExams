#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的转换流程管理器
统一管理数据转换逻辑，减少重复和复杂性
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from config import (
    ExamConfig, SubjectConfig, DataConfig, PathConfig,
    get_subject_type, get_subject_name, get_exam_duration
)
from utils import DataUtils, FileUtils, TimeUtils, ModelUtils
from validators import ExamScheduleValidator, DataFileValidator, ConversionValidator
from models import (
    Teacher, Room, TimeSlot, Exam, SubjectType,
    ExamSchedule, ConstraintConfig
)
from config import ConversionConfig


class ConversionManager:
    """简化的转换管理器"""

    def __init__(self, config: Optional[ConversionConfig] = None):
        self.config = config or ConversionConfig()
        self.exam_schedule_validator = ExamScheduleValidator()

        # 统一存储转换结果
        self.teachers: List[Teacher] = []
        self.rooms: List[Room] = []
        self.time_slots: List[TimeSlot] = []
        self.exams: List[Exam] = []

        # 缓存数据避免重复加载
        self._loaded_teachers_data = None
        self._loaded_rooms_data = None

    def convert_exam_schedule(self, exam_schedule_data: List[Dict[str, Any]],
                            base_date: str = "2024-01-15",
                            use_existing_data: bool = True) -> ExamSchedule:
        """简化的主转换流程"""

        print("🔄 开始简化转换流程...")

        # Step 1: 统一验证输入数据
        validated_schedule = self._validate_and_clean_input(exam_schedule_data)

        # Step 2: 加载或生成基础数据
        self._load_or_generate_data(use_existing_data)

        # Step 3: 简化时间段生成
        self._generate_time_slots_simple(validated_schedule, base_date)

        # Step 4: 简化考试对象创建
        self._create_exam_objects_simple(validated_schedule)

        # Step 5: 创建最终排考数据结构
        final_schedule = self._create_exam_schedule()

        # Step 6: 统一验证转换结果
        self._validate_conversion_result()

        print("✅ 简化转换流程完成")
        return final_schedule

    def _validate_and_clean_input(self, exam_schedule_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """统一验证和清理输入数据"""
        is_valid, errors, validated_schedule = self.exam_schedule_validator.validate_schedule(exam_schedule_data)

        if not is_valid:
            print(f"⚠️ 输入数据验证失败，共{len(errors)}个问题:")
            for error in errors[:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  - ...还有{len(errors)-10}个问题")
            print("将使用有效的数据继续处理")

        if not validated_schedule:
            raise ValueError("没有有效的考试安排数据")

        print(f"✅ 输入验证完成，有效考试场次: {len(validated_schedule)}")
        return validated_schedule

    def _load_or_generate_data(self, use_existing_data: bool) -> None:
        """统一加载或生成基础数据"""
        teachers_file = PathConfig.get_teachers_file()
        rooms_file = PathConfig.get_rooms_file()

        if use_existing_data:
            print("📁 加载现有基础数据...")

            # 尝试加载现有数据
            try:
                is_valid, errors, teachers_data = DataFileValidator.validate_teachers_file(teachers_file)
                if is_valid:
                    self.teachers = DataUtils.convert_to_teachers(teachers_data)
                    self._loaded_teachers_data = teachers_data
                    print(f"  ✅ 成功加载{len(self.teachers)}名教师")
                else:
                    print(f"  ❌ 教师数据无效，将生成新数据")
                    use_existing_data = False

                is_valid, errors, rooms_data = DataFileValidator.validate_rooms_file(rooms_file)
                if is_valid:
                    self.rooms = DataUtils.convert_to_rooms(rooms_data)
                    self._loaded_rooms_data = rooms_data
                    print(f"  ✅ 成功加载{len(self.rooms)}个考场")
                else:
                    print(f"  ❌ 考场数据无效，将生成新数据")
                    use_existing_data = False

            except Exception as e:
                print(f"  ❌ 加载现有数据失败: {e}")
                use_existing_data = False

        if not use_existing_data:
            print("🔧 生成新的基础数据...")
            self._generate_basic_data()

    def _generate_basic_data(self) -> None:
        """生成基础数据（确保足够数量）"""
        from basic_data_generator import BasicDataGenerator

        generator = BasicDataGenerator(seed=42)

        # 动态计算合理的教师数量
        if hasattr(self.config, 'teachers_per_subject'):
            teachers_per_subject = self.config.teachers_per_subject
        else:
            teachers_per_subject = DataConfig.TEACHERS_PER_SUBJECT

        subjects_count = len(list(SubjectType))
        total_teachers = teachers_per_subject * subjects_count

        # 📊 计算需要的考场数量（基于实际需求）
        total_exams = 9  # 预期考试场次
        invigilators_per_room = 2  # 每考场2名监考老师
        rooms_needed_for_schedule = total_teachers // (total_exams * invigilators_per_room)

        # 确保至少20个考场以满足用户需求
        rooms_needed = max(20, rooms_needed_for_schedule)

        print(f"  📊 数据需求分析:")
        print(f"    - 总教师数: {total_teachers}")
        print(f"    - 预期考试场次: {total_exams}")
        print(f"    - 每考场监考老师: {invigilators_per_room}")
        print(f"    - 计算所需考场: {rooms_needed_for_schedule}")
        print(f"    - 最终生成考场: {rooms_needed}")

        print(f"  🔧 生成基础数据: {total_teachers}名教师，{rooms_needed}个考场...")

        self.teachers = generator.generate_teachers(total_teachers)
        self.rooms = generator.generate_rooms(rooms_needed)

        # 保存生成的数据，覆盖现有文件
        teachers_file = PathConfig.get_teachers_file()
        rooms_file = PathConfig.get_rooms_file()

        print(f"  💾 保存新生成的数据...")
        generator.save_to_files(self.teachers, self.rooms, teachers_file, rooms_file)
        print(f"  ✅ 基础数据生成完成，已覆盖旧数据")

    def _generate_time_slots_simple(self, exam_schedule: List[Dict[str, Any]], base_date: str) -> None:
        """简化时间段生成"""
        self.time_slots = []

        # 直接为每个考试创建唯一时间段，避免复杂逻辑
        used_slots = set()  # 避免重复
        slot_id = 1

        for exam in exam_schedule:
            # 计算实际日期
            day_num = TimeUtils.parse_day_number(exam['date'])
            actual_date = TimeUtils.calculate_actual_date(base_date, day_num)

            # 创建唯一标识
            slot_key = f"{actual_date}_{exam['time_slot']}_{exam['start_time']}-{exam['end_time']}"

            if slot_key not in used_slots:
                time_slot = TimeSlot(
                    id=f"slot_{slot_id}",
                    name=f"{actual_date} {exam['time_slot']} {exam['start_time']}-{exam['end_time']}",
                    date=actual_date,
                    start_time=exam['start_time'],
                    end_time=exam['end_time'],
                    duration_minutes=TimeUtils.calculate_duration(exam['start_time'], exam['end_time']),
                    is_morning=(exam['time_slot'] == '上午'),
                    is_afternoon=(exam['time_slot'] == '下午')
                )

                self.time_slots.append(time_slot)
                used_slots.add(slot_key)
                slot_id += 1

        print(f"✅ 创建了{len(self.time_slots)}个时间段")

    def _create_exam_objects_simple(self, exam_schedule: List[Dict[str, Any]]) -> None:
        """简化考试对象创建"""
        self.exams = []

        print(f"    📊 开始处理 {len(exam_schedule)} 场考试的安排...")

        # 创建时间段查找表（简化版）
        time_slot_map = {}
        for slot in self.time_slots:
            key = (slot.date, slot.start_time)  # 使用日期和开始时间作为唯一标识
            time_slot_map[key] = slot

        processed_exams = 0
        skipped_exams = 0

        for exam_data in exam_schedule:
            # 获取科目类型
            subject_type = get_subject_type(exam_data['subject'])

            # 计算实际日期
            day_num = TimeUtils.parse_day_number(exam_data['date'])
            actual_date = TimeUtils.calculate_actual_date("2024-01-15", day_num)

            # 查找对应的时间段（精确匹配）
            time_slot_key = (actual_date, exam_data['start_time'])
            time_slot = time_slot_map.get(time_slot_key)

            if not time_slot:
                print(f"⚠️ 警告：找不到对应时间段，跳过考试: {exam_data['subject']}")
                skipped_exams += 1
                continue

            # 分配考场（简化版）
            allocated_rooms = self._allocate_rooms_simple(exam_data['subject'])

            # 创建考试对象
            exam = Exam(
                subject=subject_type,
                time_slot=time_slot,
                rooms=allocated_rooms,
                is_long_subject=subject_type in ExamConfig.LONG_SUBJECTS
            )

            self.exams.append(exam)
            processed_exams += 1
            print(f"    📋 考试{exam_data['subject']}({exam_data['date']}-{exam_data['start_time']})分配了{len(allocated_rooms)}个考场")

        print(f"✅ 成功创建{processed_exams}个考试对象，跳过{skipped_exams}个")

        # 计算总的预期监考任务数
        total_invigilations = sum(len(exam.rooms) for exam in self.exams)
        print(f"    📊 预期监考任务总数: {total_invigilations} (基于{len(self.exams)}场考试)")

    def _allocate_rooms_simple(self, subject: str) -> List[Room]:
        """确保每场考试都分配20个考场"""
        total_rooms = len(self.rooms)
        target_rooms = min(20, total_rooms)  # 🔧 强制分配20个考场（如果不够则使用全部）

        # 🎯 优先选择合适容量的考场，但确保数量充足
        if target_rooms == 20:  # 确保有足够考场时
            # 长时科目优先选择大容量考场
            if subject in ['语文', '数学', '英语']:
                # 先尝试大容量考场，不足时补充其他考场
                large_rooms = [r for r in self.rooms if r.capacity >= 40]
                other_rooms = [r for r in self.rooms if r not in large_rooms]
                allocated_rooms = (large_rooms + other_rooms)[:target_rooms]
                room_type = "大容量优先"
            else:
                # 短时科目优先选择中等容量考场
                medium_rooms = [r for r in self.rooms if r.capacity >= 30]
                other_rooms = [r for r in self.rooms if r not in medium_rooms]
                allocated_rooms = (medium_rooms + other_rooms)[:target_rooms]
                room_type = "中等容量优先"
        else:
            # 考场总数不足20个时，使用所有考场
            allocated_rooms = self.rooms[:target_rooms]
            room_type = "全部可用"

        print(f"    🏫 {subject}考试分配{len(allocated_rooms)}个考场 ({room_type})")

        return allocated_rooms

    def _create_exam_schedule(self) -> ExamSchedule:
        """创建最终的排考数据结构"""
        # 使用统一的约束配置
        constraint_config = ConstraintConfig()

        return ExamSchedule(
            teachers=self.teachers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            exams=self.exams,
            assignments=[],
            config=constraint_config
        )

    def _validate_conversion_result(self) -> None:
        """验证转换结果"""
        is_valid, errors = ConversionValidator.validate_conversion_result(
            self.teachers, self.rooms, self.time_slots, self.exams
        )

        if not is_valid:
            print(f"⚠️ 转换结果验证发现问题:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ 转换结果验证通过")

    def save_conversion_results(self, output_file: Optional[str] = None) -> bool:
        """保存转换结果"""
        if output_file is None:
            output_file = PathConfig.get_converted_data_file()

        # 创建结果数据
        result_data = ModelUtils.serialize_schedule_data(
            self.teachers, self.rooms, self.time_slots, self.exams,
            self.config
        )

        # 添加转换元数据
        result_data['conversion_metadata'] = {
            'conversion_time': datetime.now().isoformat(),
            'total_teachers': len(self.teachers),
            'total_rooms': len(self.rooms),
            'total_time_slots': len(self.time_slots),
            'total_exams': len(self.exams),
            'conversion_version': '2.0'  # 标记为简化版本
        }

        success = FileUtils.save_json(result_data, output_file)

        if success:
            print(f"✅ 转换结果已保存到: {output_file}")

        return success

    def get_conversion_summary(self) -> Dict[str, Any]:
        """获取转换摘要"""
        return {
            'generated_teachers': len(self.teachers),
            'generated_rooms': len(self.rooms),
            'generated_time_slots': len(self.time_slots),
            'converted_exams': len(self.exams),
            'subjects': list(set(get_subject_name(exam.subject) for exam in self.exams)),
            'conversion_version': '2.0'
        }


# 便捷函数
def create_conversion_manager(config: Optional[ConversionConfig] = None) -> ConversionManager:
    """创建转换管理器实例"""
    return ConversionManager(config)


def convert_exam_schedule_simple(exam_schedule_data: List[Dict[str, Any]],
                               base_date: str = "2024-01-15",
                               use_existing_data: bool = True) -> ExamSchedule:
    """简化的转换函数，一键完成转换"""
    manager = ConversionManager()
    return manager.convert_exam_schedule(exam_schedule_data, base_date, use_existing_data)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合流程执行脚本
运行：考试安排 → 数据转换 → 监考安排的完整流程
"""
import os
import json
import sys
import re
from datetime import datetime
from typing import Dict, Any, List

# 导入各个组件
from basic_data_generator import BasicDataGenerator
from exam_scheduler import ExamScheduler
from schedule_converter import ScheduleConverter, ConversionConfig
from main import IntelligentExamScheduler
from visualization import ResultVisualizer


class IntegratedProcess:
    """整合流程执行器"""

    def __init__(self):
        self.data_dir = "process_data"
        self.output_dir = "output"

        # 创建目录
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # 文件路径
        self.teachers_file = os.path.join(self.data_dir, "teachers.json")
        self.rooms_file = os.path.join(self.data_dir, "rooms.json")
        self.exam_schedule_file = os.path.join(self.data_dir, "exam_schedule.json")
        self.converted_data_file = os.path.join(self.data_dir, "converted_schedule.json")
        # 新增：中间考试安排JSON文件
        self.intermediate_exam_file = os.path.join(self.data_dir, "intermediate_exam_schedule.json")

    def run_complete_process(self, skip_data_generation=False):
        """运行完整流程"""
        print("🚀 开始执行整合排考流程")
        print("=" * 60)

        try:
            # Step 1: 生成基础数据
            if not skip_data_generation:
                print("\n📊 Step 1: 生成基础数据")
                self._generate_basic_data()
            else:
                print("\n📊 Step 1: 跳过基础数据生成（使用现有数据）")
                self._verify_basic_data_exists()

            # Step 2: 考试安排
            print("\n📅 Step 2: 考试时间安排")
            exam_schedule = self._run_exam_arrangement()

            # Step 3: 数据转换
            print("\n🔄 Step 3: 数据格式转换")
            converted_schedule = self._run_data_conversion(exam_schedule)

            # Step 4: 监考安排
            print("\n👥 Step 4: 监考人员安排")
            final_result = self._run_invigilation_scheduling(converted_schedule)

            # Step 5: 结果输出
            print("\n📁 Step 5: 输出结果")
            self._export_results(final_result, exam_schedule)

            print("\n🎉 整合流程执行完成！")
            print(f"📁 结果文件保存在: {self.output_dir}/")

            return True

        except KeyboardInterrupt:
            print("\n⏹️ 用户中断了流程")
            return False

        except Exception as e:
            print(f"\n❌ 流程执行出错: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _generate_basic_data(self):
        """生成基础数据"""
        print("生成400个教师和20个考场...")

        generator = BasicDataGenerator(seed=42)

        # 生成数据
        teachers = generator.generate_teachers(400)
        rooms = generator.generate_rooms(20)

        # 保存到文件
        generator.save_to_files(teachers, rooms, self.teachers_file, self.rooms_file)

        print(f"✅ 基础数据已生成并保存到:")
        print(f"   - 教师数据: {self.teachers_file}")
        print(f"   - 考场数据: {self.rooms_file}")

    def _verify_basic_data_exists(self):
        """验证基础数据是否存在"""
        if not (os.path.exists(self.teachers_file) and os.path.exists(self.rooms_file)):
            raise Exception("基础数据文件不存在，请先运行基础数据生成")

        print(f"✅ 找到现有基础数据:")
        print(f"   - 教师数据: {self.teachers_file}")
        print(f"   - 考场数据: {self.rooms_file}")

    def _save_intermediate_exam_schedule(self, exam_schedule: List[Dict]):
        """保存中间考试安排文件"""
        """保存中间考试安排到JSON文件，供后续流程直接使用"""
        intermediate_data = {
            'version': '1.0',
            'generated_time': datetime.now().isoformat(),
            'source': 'exam_arrangement',
            'exam_count': len(exam_schedule),
            'exam_schedule': exam_schedule
        }

        with open(self.intermediate_exam_file, 'w', encoding='utf-8') as f:
            json.dump(intermediate_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 中间文件已保存: {self.intermediate_exam_file}")
        print(f"   - 包含 {len(exam_schedule)} 场考试")
        print(f"   - 生成时间: {intermediate_data['generated_time']}")

    def _load_intermediate_exam_schedule(self) -> List[Dict]:
        """加载中间考试安排文件"""
        """从JSON中间文件加载考试安排数据"""
        try:
            with open(self.intermediate_exam_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            exam_schedule = data['exam_schedule']
            print(f"✅ 加载中间文件成功: {self.intermediate_exam_file}")
            print(f"   - 包含 {len(exam_schedule)} 场考试")
            print(f"   - 文件版本: {data.get('version', 'unknown')}")
            print(f"   - 生成时间: {data.get('generated_time', 'unknown')}")

            return exam_schedule

        except Exception as e:
            print(f"❌ 加载中间文件失败: {e}")
            raise Exception(f"无法读取中间文件 {self.intermediate_exam_file}: {e}")

    def _run_exam_arrangement(self) -> List[Dict]:
        """运行考试安排"""
        print("启动考试时间安排...")

        # 🔥 新逻辑：优先检查中间JSON文件
        if os.path.exists(self.intermediate_exam_file):
            print(f"发现中间考试安排文件: {self.intermediate_exam_file}")
            print("直接使用缓存数据，跳过解析过程...")
            exam_schedule = self._load_intermediate_exam_schedule()
        else:
            # 检查txt文件作为数据源
            existing_file = "考试安排表.txt"
            if os.path.exists(existing_file):
                print(f"发现现有考试安排表: {existing_file}")
                print("解析txt文件并生成中间缓存文件...")
                exam_schedule = self._parse_existing_exam_schedule(existing_file)
            else:
                print("未发现现有考试安排表，生成默认安排...")
                # 使用预定义的考试安排（避免手动输入）
                exam_schedule = self._create_default_exam_schedule()

            # 🔥 保存中间JSON文件供下次使用
            self._save_intermediate_exam_schedule(exam_schedule)

        # 验证时间合理性
        validated_schedule = self._validate_exam_schedule(exam_schedule)

        # 保存最终结果到exam_schedule.json（保持向后兼容）
        with open(self.exam_schedule_file, 'w', encoding='utf-8') as f:
            json.dump(validated_schedule, f, ensure_ascii=False, indent=2)

        print(f"✅ 考试安排完成，共{len(validated_schedule)}场考试")
        print(f"   - 最终结果已保存到: {self.exam_schedule_file}")
        if os.path.exists(self.intermediate_exam_file):
            print(f"   - 缓存文件已保存到: {self.intermediate_exam_file}")

        return validated_schedule

    def _create_default_exam_schedule(self) -> List[Dict]:
        """创建默认考试安排（避免手动输入）"""
        return [
            # 第1天
            {'date': '第1天', 'time_slot': '上午', 'subject': '语文',
             'start_time': '07:30', 'end_time': '09:40', 'duration': 150},
            {'date': '第1天', 'time_slot': '下午', 'subject': '数学',
             'start_time': '14:00', 'end_time': '15:30', 'duration': 120},

            # 第2天
            {'date': '第2天', 'time_slot': '上午', 'subject': '英语',
             'start_time': '07:30', 'end_time': '09:30', 'duration': 120},
            {'date': '第2天', 'time_slot': '下午', 'subject': '物理',
             'start_time': '14:00', 'end_time': '15:30', 'duration': 90},

            # 第3天
            {'date': '第3天', 'time_slot': '上午', 'subject': '化学',
             'start_time': '07:30', 'end_time': '09:00', 'duration': 90},
            {'date': '第3天', 'time_slot': '下午', 'subject': '生物',
             'start_time': '14:00', 'end_time': '15:30', 'duration': 90},

            # 第4天
            {'date': '第4天', 'time_slot': '上午', 'subject': '历史',
             'start_time': '07:30', 'end_time': '09:00', 'duration': 90},
            {'date': '第4天', 'time_slot': '下午', 'subject': '地理',
             'start_time': '14:00', 'end_time': '15:30', 'duration': 90},

            # 第5天
            {'date': '第5天', 'time_slot': '上午', 'subject': '政治',
             'start_time': '07:30', 'end_time': '09:00', 'duration': 90},
        ]

    def _validate_exam_schedule(self, exam_schedule: List[Dict]) -> List[Dict]:
        """验证考试安排的合理性"""
        validated_schedule = []
        scheduler = ExamScheduler()

        for exam in exam_schedule:
            # 验证时间冲突
            duration = exam['duration']
            time_slot = exam['time_slot']

            # 获取时间段可用时长
            available_time = scheduler.calculate_slot_duration(time_slot)

            # 检查是否时间充足
            if duration <= available_time:
                validated_schedule.append(exam)
            else:
                print(f"⚠️ 警告：考试 {exam['subject']} 时间不足，已跳过")

        return validated_schedule

    def _run_data_conversion(self, exam_schedule: List[Dict]):
        """运行数据转换"""
        print("转换考试安排数据为排考系统格式...")

        # 创建转换配置
        conversion_config = ConversionConfig(
            student_count_per_class=40,
            teachers_per_subject=8,
            room_allocation_strategy="grade_based",
            historical_load_min=100.0,
            historical_load_max=500.0
        )

        # 创建转换器
        converter = ScheduleConverter(conversion_config)

        # 加载预生成的教师和考场数据
        pre_generated_teachers = self._load_pre_generated_teachers()
        pre_generated_rooms = self._load_pre_generated_rooms()

        # 执行转换，使用预生成的数据
        converted_schedule = converter.convert(
            exam_schedule,
            pre_generated_teachers=pre_generated_teachers,
            pre_generated_rooms=pre_generated_rooms
        )

        # 保存转换结果
        with open(self.converted_data_file, 'w', encoding='utf-8') as f:
            json.dump({
                'teachers': [t.__dict__ for t in converted_schedule.teachers],
                'rooms': [r.__dict__ for r in converted_schedule.rooms],
                'time_slots': [ts.__dict__ for ts in converted_schedule.time_slots],
                'exams': [e.__dict__ for e in converted_schedule.exams],
                'config': converted_schedule.config.__dict__
            }, f, ensure_ascii=False, indent=2, default=str)

        # 显示转换摘要
        summary = converter.get_conversion_summary()
        print(f"✅ 数据转换完成:")
        print(f"   - 教师数量: {summary['generated_teachers']}")
        print(f"   - 考场数量: {summary['generated_rooms']}")
        print(f"   - 时间段数量: {summary['generated_time_slots']}")
        print(f"   - 考试数量: {summary['converted_exams']}")
        print(f"   - 涉及科目: {', '.join(summary['subjects'])}")
        print(f"   - 转换结果已保存到: {self.converted_data_file}")

        return converted_schedule

    def _run_invigilation_scheduling(self, converted_schedule):
        """运行监考安排"""
        print("执行监考人员智能安排...")

        # 创建排考系统
        invigilation_scheduler = IntelligentExamScheduler()
        invigilation_scheduler.schedule = converted_schedule

        # 自动选择算法并求解
        success = invigilation_scheduler.solve_auto(time_limit=60)

        if not success:
            raise Exception("监考安排求解失败")

        # 分析结果
        invigilation_scheduler.analyze_result()

        return invigilation_scheduler

    def _export_results(self, invigilation_scheduler, exam_schedule):
        """导出最终结果"""
        print("生成最终结果文件...")

        # 直接使用可视化模块导出结果
        visualizer = ResultVisualizer(invigilation_scheduler.result_schedule)

        exported_files = []

        try:
            # 导出Excel
            excel_files = visualizer.export_to_excel(self.output_dir)
            exported_files.extend(excel_files)
            print("✅ Excel文件导出完成")

            # 导出HTML报告
            html_file = visualizer.generate_comprehensive_report(self.output_dir)
            exported_files.append(html_file)
            print("✅ HTML报告导出完成")

            # 生成图表
            load_chart = visualizer.plot_load_distribution(self.output_dir)
            heatmap = visualizer.plot_schedule_heatmap(self.output_dir)
            exported_files.extend([load_chart, heatmap])
            print("✅ 可视化图表导出完成")

            print(f"\n📁 总共导出 {len(exported_files)} 个文件:")
            for file_path in exported_files:
                print(f"  - {file_path}")

        except Exception as e:
            print(f"导出结果时出错: {e}")

        # 生成综合报告
        self._generate_integrated_report(invigilation_scheduler, exam_schedule)

    def _generate_integrated_report(self, invigilation_scheduler, exam_schedule):
        """生成整合报告"""
        report_file = os.path.join(self.output_dir, "整合流程报告.txt")

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("智能排考系统 - 整合流程执行报告\n")
            f.write("=" * 80 + "\n\n")

            # 考试安排部分
            f.write("📅 考试时间安排\n")
            f.write("-" * 40 + "\n")
            for exam in exam_schedule:
                f.write(f"{exam['date']} {exam['time_slot']}: {exam['subject']} "
                       f"({exam['start_time']}-{exam['end_time']})\n")

            f.write(f"\n总考试场次: {len(exam_schedule)}\n\n")

            # 监考安排部分
            f.write("👥 监考安排统计\n")
            f.write("-" * 40 + "\n")

            result_schedule = invigilation_scheduler.result_schedule
            stats = result_schedule.generate_statistics()

            fairness_metrics = stats.get('fairness_metrics', {})
            f.write(f"使用算法: {invigilation_scheduler.algorithm_used}\n")
            f.write(f"求解时间: {invigilation_scheduler.solve_time:.2f}秒\n")
            f.write(f"监考安排数量: {len(result_schedule.assignments)}\n")
            f.write(f"最大负荷: {fairness_metrics.get('max_total_load', 0):.2f}\n")
            f.write(f"最小负荷: {fairness_metrics.get('min_total_load', 0):.2f}\n")
            f.write(f"平均负荷: {fairness_metrics.get('avg_total_load', 0):.2f}\n")
            f.write(f"负荷极差: {fairness_metrics.get('load_range', 0):.2f}\n")

            # 冲突检查
            constraint_stats = stats.get('constraint_stats', {})
            conflicts = constraint_stats.get('conflicts', [])
            f.write(f"\n硬约束冲突数: {len(conflicts)}\n")

            if conflicts:
                f.write("\n冲突详情:\n")
                for i, conflict in enumerate(conflicts[:10]):
                    f.write(f"{i+1}. {conflict}\n")

            f.write("\n" + "=" * 80 + "\n")

        print(f"✅ 整合报告已生成: {report_file}")

    def _parse_existing_exam_schedule(self, file_path: str) -> List[Dict]:
        """解析现有的考试安排表.txt"""
        print(f"解析现有考试安排: {file_path}")

        exam_schedule = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

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

                # 🔧 修复：过滤空字符串，处理多空格分隔问题
                parts = [p for p in line.split() if p.strip()]

                # 实际格式: "第1天      上午       语文       07:30      10:00      150"
                if len(parts) >= 6:  # 确保有足够的字段
                    date_part = parts[0]
                    time_slot_part = parts[1]
                    subject_part = parts[2]
                    start_time = parts[3]        # 🔧 修复：直接获取开始时间
                    end_time = parts[4]          # 🔧 修复：直接获取结束时间

                    # 🔧 修复：验证时间格式
                    time_pattern = re.compile(r'^\d{2}:\d{2}$')
                    if not (time_pattern.match(start_time) and time_pattern.match(end_time)):
                        print(f"⚠️ 警告：时间格式不正确 {start_time}-{end_time}，使用默认时间")
                        start_time, end_time = '07:30', '09:30'

                    # 根据科目确定时长（备用方案）
                    duration_map = {
                        '语文': 150, '数学': 120, '英语': 120, '外语': 120,
                        '物理': 90, '化学': 90, '生物': 90,
                        '历史': 90, '地理': 90, '政治': 90, '技术': 90
                    }

                    # 🔧 修复：优先使用文件中的时长，其次使用科目映射
                    try:
                        duration = int(parts[5])
                    except (ValueError, IndexError):
                        duration = duration_map.get(subject_part, 120)

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
            print("使用默认考试安排...")
            return self._create_default_exam_schedule()

    def _load_pre_generated_teachers(self):
        """加载预生成的教师数据"""
        try:
            with open(self.teachers_file, 'r', encoding='utf-8') as f:
                teacher_data = json.load(f)

            # 转换为Teacher对象
            from models import Teacher, SubjectType

            subject_mapping = {
                '语文': SubjectType.CHINESE, '数学': SubjectType.MATH, '英语': SubjectType.ENGLISH,
                '外语': SubjectType.ENGLISH, '物理': SubjectType.PHYSICS, '化学': SubjectType.CHEMISTRY,
                '生物': SubjectType.BIOLOGY, '历史': SubjectType.HISTORY, '地理': SubjectType.GEOGRAPHY,
                '政治': SubjectType.POLITICS, '技术': SubjectType.SCIENCE
            }

            teachers = []
            for teacher_dict in teacher_data:
                teacher = Teacher(
                    id=teacher_dict['id'],
                    name=teacher_dict['name'],
                    subject=subject_mapping.get(teacher_dict['subject'], SubjectType.CHINESE),
                    grade=teacher_dict['grade'],
                    historical_load=teacher_dict['historical_load'],
                    teaching_schedule=teacher_dict.get('teaching_schedule', {}),
                    leave_times=teacher_dict.get('leave_times', []),
                    fixed_duties=teacher_dict.get('fixed_duties', [])
                )
                teachers.append(teacher)

            print(f"加载 {len(teachers)} 名预生成教师")
            return teachers

        except Exception as e:
            print(f"加载预生成教师数据失败: {e}")
            return None

    def _load_pre_generated_rooms(self):
        """加载预生成的考场数据"""
        try:
            with open(self.rooms_file, 'r', encoding='utf-8') as f:
                room_data = json.load(f)

            # 转换为Room对象
            from models import Room

            rooms = []
            for room_dict in room_data:
                room = Room(
                    id=room_dict['id'],
                    name=room_dict['name'],
                    capacity=room_dict['capacity'],
                    building=room_dict['building'],
                    floor=room_dict['floor']
                )
                rooms.append(room)

            print(f"加载 {len(rooms)} 个预生成考场")
            return rooms

        except Exception as e:
            print(f"加载预生成考场数据失败: {e}")
            return None


def main():
    """主函数"""
    print("智能排考系统 - 整合流程执行器")
    print("=" * 60)

    process = IntegratedProcess()

    # 解析命令行参数
    skip_data_gen = "--skip-data-gen" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print("用法:")
        print("  python run_integrated_process.py           # 完整流程")
        print("  python run_integrated_process.py --skip-data-gen  # 跳过基础数据生成")
        print("\n选项:")
        print("  --skip-data-gen    跳过基础数据生成步骤（使用现有数据）")
        print("  --help, -h         显示此帮助信息")
        return

    # 执行流程
    success = process.run_complete_process(skip_data_generation=skip_data_gen)

    if success:
        print("\n🎊 流程执行成功！")
        print(f"📁 请查看 {process.output_dir}/ 目录下的结果文件")
    else:
        print("\n💥 流程执行失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
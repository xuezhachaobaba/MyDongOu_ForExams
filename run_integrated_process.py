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
from schedule_converter import ScheduleConverter, ConversionConfig  # 保留向后兼容
from main import IntelligentExamScheduler
from visualization import ResultVisualizer

# 导入新的优化模块
from conversion_manager import ConversionManager, convert_exam_schedule_simple
from validators import validate_all_data_files, create_exam_schedule_validator
from utils import FileUtils, ParseUtils, ModelUtils
from config import PathConfig


class IntegratedProcess:
    """整合流程执行器"""

    def __init__(self):
        # 使用统一路径配置
        self.data_dir = PathConfig.DATA_DIR
        self.output_dir = PathConfig.OUTPUT_DIR

        # 创建目录
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # 使用PathConfig统一文件路径
        self.teachers_file = PathConfig.get_teachers_file()
        self.rooms_file = PathConfig.get_rooms_file()
        self.exam_schedule_file = PathConfig.get_exam_schedule_file()
        self.converted_data_file = PathConfig.get_converted_data_file()
        self.intermediate_exam_file = PathConfig.get_intermediate_exam_file()

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
        """验证基础数据是否存在（使用新的验证器）"""
        # 使用新的验证器
        is_valid, errors = validate_all_data_files(self.teachers_file, self.rooms_file)

        if not is_valid:
            print("❌ 基础数据验证失败:")
            for error in errors:
                print(f"   - {error}")
            raise Exception("基础数据文件不存在或无效，请先运行基础数据生成")

        print(f"✅ 找到现有基础数据并验证通过:")
        print(f"   - 教师数据: {self.teachers_file}")
        print(f"   - 考场数据: {self.rooms_file}")

    def _save_intermediate_exam_schedule(self, exam_schedule: List[Dict]):
        """保存中间考试安排文件（使用新的工具）"""
        # 使用新的模型工具创建中间数据
        intermediate_data = ModelUtils.create_intermediate_exam_schedule(exam_schedule)

        # 使用文件工具保存
        if FileUtils.save_json(intermediate_data, self.intermediate_exam_file):
            print(f"✅ 中间文件已保存: {self.intermediate_exam_file}")
            print(f"   - 包含 {len(exam_schedule)} 场考试")
            print(f"   - 生成时间: {intermediate_data['generated_time']}")
        else:
            print(f"❌ 保存中间文件失败: {self.intermediate_exam_file}")

    def _load_intermediate_exam_schedule(self) -> List[Dict]:
        """加载中间考试安排文件（使用新的工具）"""
        # 使用文件工具加载
        data = FileUtils.load_json(self.intermediate_exam_file)

        if not data or 'exam_schedule' not in data:
            print(f"❌ 加载中间文件失败: 文件格式错误或不存在")
            raise Exception(f"无法读取中间文件 {self.intermediate_exam_file}")

        exam_schedule = data['exam_schedule']
        print(f"✅ 加载中间文件成功: {self.intermediate_exam_file}")
        print(f"   - 包含 {len(exam_schedule)} 场考试")
        print(f"   - 文件版本: {data.get('version', 'unknown')}")
        print(f"   - 生成时间: {data.get('generated_time', 'unknown')}")

        return exam_schedule

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
            existing_file = os.path.join(self.data_dir, "考试安排表.txt")
            if os.path.exists(existing_file):
                print(f"发现现有考试安排表: {existing_file}")
                print("解析txt文件并生成中间缓存文件...")
                exam_schedule = self._parse_existing_exam_schedule(existing_file)
            else:
                print("未发现现有考试安排表和缓存文件")
                print("请选择数据来源：")
                print("0 - 使用默认数据")
                print("1 - 手动输入数据")

                while True:
                    choice = input("请输入选择（0或1）: ").strip()
                    if choice == '0':
                        print("使用默认考试安排...")
                        exam_schedule = self._create_default_exam_schedule()
                        break
                    elif choice == '1':
                        print("启动手动输入模式...")
                        scheduler = ExamScheduler()
                        scheduler.interactive_mode()

                        # 手动输入完成后，解析生成的文件
                        generated_file = os.path.join(self.data_dir, "考试安排表.txt")
                        if os.path.exists(generated_file):
                            print(f"解析手动输入的考试安排: {generated_file}")
                            exam_schedule = self._parse_existing_exam_schedule(generated_file)
                        else:
                            print("未找到手动输入的文件，使用默认安排...")
                            exam_schedule = self._create_default_exam_schedule()
                        break
                    else:
                        print("无效选择，请输入0或1")

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
        """运行数据转换（使用新的简化流程）"""
        print("🔄 使用简化的数据转换流程...")

        # 使用新的转换管理器
        manager = ConversionManager()

        # 执行简化的转换流程
        converted_schedule = manager.convert_exam_schedule(
            exam_schedule_data=exam_schedule,
            base_date="2024-01-15",
            use_existing_data=True
        )

        # 保存转换结果
        manager.save_conversion_results(self.converted_data_file)

        # 显示转换摘要
        summary = manager.get_conversion_summary()
        print(f"✅ 简化数据转换完成:")
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
            exported_files.extend([load_chart])
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
        """解析现有的考试安排表.txt（使用新的解析工具）"""
        print(f"🔍 使用新解析工具解析考试安排: {file_path}")

        # 使用新的解析工具
        exam_schedule = ParseUtils.parse_exam_schedule_from_text(file_path)

        if not exam_schedule:
            print("⚠️ 解析失败，使用默认考试安排...")
            return self._create_default_exam_schedule()

        return exam_schedule

    def _load_pre_generated_teachers(self):
        """加载预生成的教师数据（使用新的工具）"""
        # 使用新的数据工具加载和转换
        teacher_data = FileUtils.load_json(self.teachers_file)

        if not teacher_data:
            print(f"加载预生成教师数据失败: 文件不存在或为空")
            return None

        teachers = DataUtils.convert_to_teachers(teacher_data)
        print(f"✅ 加载 {len(teachers)} 名预生成教师")
        return teachers

    def _load_pre_generated_rooms(self):
        """加载预生成的考场数据（使用新的工具）"""
        # 使用新的数据工具加载和转换
        room_data = FileUtils.load_json(self.rooms_file)

        if not room_data:
            print(f"加载预生成考场数据失败: 文件不存在或为空")
            return None

        rooms = DataUtils.convert_to_rooms(room_data)
        print(f"✅ 加载 {len(rooms)} 个预生成考场")
        return rooms


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
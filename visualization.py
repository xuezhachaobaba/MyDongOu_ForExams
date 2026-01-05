"""
结果可视化和导出功能
用于生成监考安排的统计报表、可视化图表和导出文件
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

from models import ExamSchedule, Assignment, SubjectType


class ResultVisualizer:
    """结果可视化器"""

    def __init__(self, schedule: ExamSchedule):
        self.schedule = schedule
        self.stats = schedule.generate_statistics()

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置样式
        sns.set_style("whitegrid")
        self.colors = sns.color_palette("husl", 10)

    def generate_comprehensive_report(self, output_dir: str = "output") -> str:
        """生成综合报告"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"comprehensive_report_{timestamp}.html")

        # 生成HTML报告
        html_content = self._generate_html_report()

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"综合报告已生成: {report_path}")
        return report_path

    def _generate_html_report(self) -> str:
        """生成HTML格式的报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>智能排考系统结果报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .stats-table {{ width: 100%; border-collapse: collapse; }}
                .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .stats-table th {{ background-color: #f2f2f2; }}
                .conflict {{ color: red; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>智能排考系统结果报告</h1>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            {self._generate_overview_section()}
            {self._generate_fairness_section()}
            {self._generate_conflicts_section()}
            {self._generate_teacher_details_section()}
        </body>
        </html>
        """
        return html

    def _generate_overview_section(self) -> str:
        """生成概览部分"""
        overview = f"""
        <div class="section">
            <h2>📊 排考概览</h2>
            <table class="stats-table">
                <tr><th>项目</th><th>数值</th></tr>
                <tr><td>教师总数</td><td>{len(self.schedule.teachers)}</td></tr>
                <tr><td>考场总数</td><td>{len(self.schedule.rooms)}</td></tr>
                <tr><td>时间段总数</td><td>{len(self.schedule.time_slots)}</td></tr>
                <tr><td>考试科目数</td><td>{len(self.schedule.exams)}</td></tr>
                <tr><td>监考安排数</td><td>{len(self.schedule.assignments)}</td></tr>
            </table>
        </div>
        """
        return overview

    def _generate_fairness_section(self) -> str:
        """生成公平性分析部分"""
        fairness_metrics = self.stats.get('fairness_metrics', {})
        fairness = f"""
        <div class="section">
            <h2>⚖️ 公平性分析</h2>
            <table class="stats-table">
                <tr><th>指标</th><th>数值</th></tr>
                <tr><td>最大负荷</td><td>{fairness_metrics.get('max_total_load', 0):.2f}</td></tr>
                <tr><td>最小负荷</td><td>{fairness_metrics.get('min_total_load', 0):.2f}</td></tr>
                <tr><td>平均负荷</td><td>{fairness_metrics.get('avg_total_load', 0):.2f}</td></tr>
                <tr><td>负荷极差</td><td>{fairness_metrics.get('load_range', 0):.2f}</td></tr>
                <tr><td>负荷标准差</td><td>{fairness_metrics.get('load_std', 0):.2f}</td></tr>
            </table>
        </div>
        """
        return fairness

    def _generate_conflicts_section(self) -> str:
        """生成冲突分析部分"""
        constraint_stats = self.stats.get('constraint_stats', {})
        conflicts = constraint_stats.get('conflicts', [])
        conflict_count = constraint_stats.get('conflict_count', 0)

        conflict_class = "conflict" if conflict_count > 0 else "success"
        conflicts_section = f"""
        <div class="section">
            <h2>⚠️ 冲突检查</h2>
            <p class="{conflict_class}">发现 <strong>{conflict_count}</strong> 个硬约束冲突</p>
        """

        if conflicts:
            conflicts_section += "<h3>冲突详情:</h3><ul>"
            for i, conflict in enumerate(conflicts[:10]):  # 只显示前10个
                conflicts_section += f"<li>{conflict}</li>"
            if len(conflicts) > 10:
                conflicts_section += f"<li>... 还有 {len(conflicts) - 10} 个冲突</li>"
            conflicts_section += "</ul>"

        conflicts_section += "</div>"
        return conflicts_section

    def _generate_teacher_details_section(self) -> str:
        """生成教师详情部分"""
        teacher_stats = self.stats.get('teacher_stats', [])

        details = """
        <div class="section">
            <h2>👥 教师安排详情</h2>
            <table class="stats-table">
                <tr>
                    <th>教师姓名</th><th>科目</th><th>当前负荷</th>
                    <th>历史负荷</th><th>加权总负荷</th><th>安排数</th><th>长时科目数</th>
                </tr>
        """

        for stat in sorted(teacher_stats, key=lambda x: x['total_weighted_load'], reverse=True)[:20]:
            details += f"""
                <tr>
                    <td>{stat['teacher_name']}</td><td>{stat['subject']}</td>
                    <td>{stat['current_load']:.2f}</td>
                    <td>{stat['historical_load']:.2f}</td>
                    <td>{stat['total_weighted_load']:.2f}</td>
                    <td>{stat['assignment_count']}</td>
                    <td>{stat['long_exam_count']}</td>
                </tr>
            """

        details += "</table></div>"
        return details

    def plot_load_distribution(self, output_dir: str = "output") -> str:
        """绘制负荷分布图"""
        plt.figure(figsize=(12, 8))

        # 获取教师负荷数据
        teacher_stats = self.stats.get('teacher_stats', [])
        loads = [stat['total_weighted_load'] for stat in teacher_stats]

        # 创建子图
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('监考安排负荷分析', fontsize=16)

        # 1. 负荷分布直方图
        ax1.hist(loads, bins=20, alpha=0.7, color=self.colors[0])
        ax1.set_title('教师负荷分布')
        ax1.set_xlabel('加权总负荷')
        ax1.set_ylabel('教师人数')
        ax1.grid(True, alpha=0.3)

        # 2. 负荷箱线图
        ax2.boxplot(loads)
        ax2.set_title('负荷分布箱线图')
        ax2.set_ylabel('加权总负荷')
        ax2.grid(True, alpha=0.3)

        # 3. 负荷排序图
        sorted_loads = sorted(loads)
        ax3.plot(range(len(sorted_loads)), sorted_loads, color=self.colors[2])
        ax3.set_title('教师负荷排序图')
        ax3.set_xlabel('教师排名')
        ax3.set_ylabel('加权总负荷')
        ax3.grid(True, alpha=0.3)

        # 4. 长时科目分布
        long_counts = [stat['long_exam_count'] for stat in teacher_stats]
        unique, counts = np.unique(long_counts, return_counts=True)
        ax4.bar(unique, counts, color=self.colors[3])
        ax4.set_title('长时科目监考次数分布')
        ax4.set_xlabel('长时科目监考次数')
        ax4.set_ylabel('教师人数')
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存图片
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(output_dir, f"load_distribution_{timestamp}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"负荷分布图已保存: {image_path}")
        return image_path

    def plot_schedule_heatmap(self, output_dir: str = "output") -> str:
        """绘制监考安排热力图"""
        # 准备数据
        time_slots = sorted(self.schedule.time_slots, key=lambda x: (x.date, x.start_time))
        teachers = sorted(self.schedule.teachers, key=lambda x: x.name)

        # 创建矩阵
        matrix = np.zeros((len(teachers), len(time_slots)))

        for i, teacher in enumerate(teachers):
            assignments = self.schedule.get_teacher_assignments(teacher.id)
            for assignment in assignments:
                j = time_slots.index(assignment.time_slot)
                matrix[i][j] = 1 if assignment.is_invigilation else 0.5

        # 绘制热力图
        plt.figure(figsize=(16, 10))

        time_labels = [f"{ts.date[-5:]}\\n{ts.name}" for ts in time_slots]
        teacher_labels = [t.name[-3:] for t in teachers]  # 只显示后三位

        sns.heatmap(matrix,
                   xticklabels=time_labels,
                   yticklabels=teacher_labels,
                   cmap="YlOrRd",
                   cbar_kws={'label': '任务类型'})

        plt.title('监考安排热力图', fontsize=16)
        plt.xlabel('时间段')
        plt.ylabel('教师')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        # 保存图片
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(output_dir, f"schedule_heatmap_{timestamp}.png")
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"监考安排热力图已保存: {image_path}")
        return image_path

    def export_to_excel(self, output_dir: str = "output") -> List[str]:
        """导出Excel格式的监考表"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 创建Excel写入器
        excel_path = os.path.join(output_dir, f"监考安排表_{timestamp}.xlsx")

        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # 1. 监考安排表（新格式，类似Excel文件中的格式）
            self._export_monitoring_sheet(writer)

            # 2. 总监考表
            self._export_overall_sheet(writer)

            # 3. 按教师分表
            self._export_by_teacher_sheet(writer)

            # 4. 按时间分表
            self._export_by_time_sheet(writer)

            # 5. 按考场分表
            self._export_by_room_sheet(writer)

            # 6. 统计报表
            self._export_statistics_sheet(writer)

            # 7. 冲突报告
            self._export_conflicts_sheet(writer)

        print(f"Excel文件已导出: {excel_path}")
        return [excel_path]

    def _export_monitoring_sheet(self, writer):
        """导出监考安排表（类似Excel文件中的格式）"""
        # 获取所有时间段，按日期和时间排序
        time_slots = sorted(self.schedule.time_slots, key=lambda x: (x.date, x.start_time))

        # 按日期分组时间段
        dates = sorted(set(ts.date for ts in time_slots))
        date_time_slots = {date: [ts for ts in time_slots if ts.date == date] for date in dates}

        # 获取所有考场（按名称排序）
        rooms = sorted(self.schedule.rooms, key=lambda x: x.name)

        # 构建列名和数据
        columns = self._build_monitoring_columns(dates, date_time_slots)
        data_rows = []

        for room in rooms:
            row = self._build_monitoring_row(room, dates, date_time_slots)
            data_rows.append(row)

        # 创建DataFrame
        df = pd.DataFrame(data_rows, columns=columns)

        # 导出到Excel
        df.to_excel(writer, sheet_name="监考安排表", index=False)

    def _build_monitoring_columns(self, dates, date_time_slots):
        """构建监考安排表的列名"""
        columns = ['班级', '班级编号']

        for date in dates:
            time_slots_for_date = date_time_slots[date]
            for ts in time_slots_for_date:
                # 找到该时间段的考试科目
                exam_subject = self._get_exam_subject_for_timeslot(ts)
                time_range = f"{ts.start_time}-{ts.end_time}"

                # 为每个时间段创建3列：监考教师A、监考教师B、学生人数
                # 列名包含完整信息：日期_时间段_科目_时间_角色
                columns.extend([
                    f"{date}_{ts.name}_{exam_subject}_{time_range}_监考教师A",
                    f"{date}_{ts.name}_{exam_subject}_{time_range}_监考教师B",
                    f"{date}_{ts.name}_{exam_subject}_{time_range}_学生人数"
                ])

        return columns

    def _get_exam_subject_for_timeslot(self, time_slot):
        """获取指定时间段的考试科目"""
        for exam in self.schedule.exams:
            if exam.time_slot.id == time_slot.id:
                return exam.subject.value
        return ""

    def _build_monitoring_row(self, room, dates, date_time_slots):
        """为指定考场构建一行数据"""
        row_data = ['', '']  # 班级、班级编号占位符

        # 为考场确定班级信息（这里简单使用考场名称作为班级名）
        if room.name.startswith('高二'):
            # 提取班级信息，例如从"高二1班5001"中提取"高二1班"和"5001"
            if '班' in room.name:
                parts = room.name.split('班')
                if len(parts) >= 2:
                    class_name = parts[0] + '班'
                    class_id = parts[1] if parts[1] else str(room.id)
                    row_data[0] = class_name
                    row_data[1] = class_id
                else:
                    row_data[0] = room.name
                    row_data[1] = str(room.id)
            else:
                row_data[0] = room.name
                row_data[1] = str(room.id)
        else:
            row_data[0] = room.name
            row_data[1] = str(room.id)

        # 为每个时间段-考场组合添加监考信息
        for date in dates:
            time_slots_for_date = date_time_slots[date]
            for ts in time_slots_for_date:
                # 获取该时间段该考场的监考教师
                teachers = self._get_teachers_for_room_timeslot(room.id, ts.id)
                student_count = room.capacity

                # 添加3列数据：监考教师A、监考教师B、学生人数
                if len(teachers) >= 2:
                    row_data.extend([teachers[0], teachers[1], student_count])
                elif len(teachers) == 1:
                    row_data.extend([teachers[0], '/', student_count])
                else:
                    row_data.extend(['/', '/', student_count])

        return row_data

    def _get_teachers_for_room_timeslot(self, room_id, time_slot_id):
        """获取指定考场和时间段的监考教师"""
        assignments = []
        for assignment in self.schedule.assignments:
            if (assignment.room.id == room_id and
                assignment.time_slot.id == time_slot_id and
                assignment.is_invigilation):
                assignments.append(assignment.teacher.name)
        return assignments

    def _export_overall_sheet(self, writer):
        """导出总监考表"""
        data = []
        for assignment in self.schedule.assignments:
            data.append({
                '教师姓名': assignment.teacher.name,
                '教师科目': assignment.teacher.subject.value,
                '考场': assignment.room.name,
                '时间段': assignment.time_slot.name,
                '考试科目': assignment.subject.value,
                '任务类型': '监考' if assignment.is_invigilation else '自习坐班',
                '时长(分钟)': assignment.time_slot.duration_minutes
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='总监考表', index=False)

    def _export_by_teacher_sheet(self, writer):
        """按教师导出监考表"""
        teacher_groups = {}
        for assignment in self.schedule.assignments:
            teacher_id = assignment.teacher.id
            if teacher_id not in teacher_groups:
                teacher_groups[teacher_id] = []
            teacher_groups[teacher_id].append(assignment)

        for teacher_id, assignments in teacher_groups.items():
            teacher = self.schedule.teacher_map[teacher_id]
            data = []

            for assignment in assignments:
                data.append({
                    '日期': assignment.time_slot.date,
                    '时间': f"{assignment.time_slot.start_time}-{assignment.time_slot.end_time}",
                    '考场': assignment.room.name,
                    '考试科目': assignment.subject.value,
                    '任务类型': '监考' if assignment.is_invigilation else '自习坐班'
                })

            df = pd.DataFrame(data)
            sheet_name = f"{teacher.name[:15]}({teacher.subject.value[:2]})"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    def _export_by_time_sheet(self, writer):
        """按时间段导出监考表"""
        time_groups = {}
        for assignment in self.schedule.assignments:
            time_id = assignment.time_slot.id
            if time_id not in time_groups:
                time_groups[time_id] = []
            time_groups[time_id].append(assignment)

        for time_id, assignments in time_groups.items():
            time_slot = next(ts for ts in self.schedule.time_slots if ts.id == time_id)
            data = []

            for assignment in assignments:
                data.append({
                    '教师姓名': assignment.teacher.name,
                    '教师科目': assignment.teacher.subject.value,
                    '考场': assignment.room.name,
                    '考试科目': assignment.subject.value,
                    '任务类型': '监考' if assignment.is_invigilation else '自习坐班'
                })

            df = pd.DataFrame(data)
            sheet_name = f"{time_slot.date[-5:]}{time_slot.name[:4]}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    def _export_by_room_sheet(self, writer):
        """按考场导出监考表"""
        room_groups = {}
        for assignment in self.schedule.assignments:
            room_id = assignment.room.id
            if room_id not in room_groups:
                room_groups[room_id] = []
            room_groups[room_id].append(assignment)

        for room_id, assignments in room_groups.items():
            room = self.schedule.room_map[room_id]
            data = []

            for assignment in assignments:
                data.append({
                    '日期': assignment.time_slot.date,
                    '时间': f"{assignment.time_slot.start_time}-{assignment.time_slot.end_time}",
                    '教师姓名': assignment.teacher.name,
                    '教师科目': assignment.teacher.subject.value,
                    '考试科目': assignment.subject.value,
                    '任务类型': '监考' if assignment.is_invigilation else '自习坐班'
                })

            df = pd.DataFrame(data)
            sheet_name = f"{room.name[:15]}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    def _export_statistics_sheet(self, writer):
        """导出统计报表"""
        # 教师统计
        teacher_stats = self.stats.get('teacher_stats', [])
        df_teachers = pd.DataFrame(teacher_stats)
        df_teachers.to_excel(writer, sheet_name='教师统计', index=False)

        # 公平性指标
        fairness_metrics = self.stats.get('fairness_metrics', {})
        df_fairness = pd.DataFrame(list(fairness_metrics.items()),
                                 columns=['指标', '数值'])
        df_fairness.to_excel(writer, sheet_name='公平性指标', index=False)

    def _export_conflicts_sheet(self, writer):
        """导出冲突报告"""
        constraint_stats = self.stats.get('constraint_stats', {})
        conflicts = constraint_stats.get('conflicts', [])

        if conflicts:
            df_conflicts = pd.DataFrame({'冲突描述': conflicts})
            df_conflicts.to_excel(writer, sheet_name='冲突报告', index=False)
        else:
            # 创建空的数据框
            df_conflicts = pd.DataFrame({'状态': ['无硬约束冲突']})
            df_conflicts.to_excel(writer, sheet_name='冲突报告', index=False)

    def export_to_csv(self, output_dir: str = "output") -> List[str]:
        """导出CSV格式"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        csv_files = []

        # 1. 总监考表
        csv_path = os.path.join(output_dir, f"监考安排_{timestamp}.csv")
        data = []
        for assignment in self.schedule.assignments:
            data.append({
                'teacher_name': assignment.teacher.name,
                'teacher_subject': assignment.teacher.subject.value,
                'room_name': assignment.room.name,
                'time_slot': assignment.time_slot.id,
                'exam_subject': assignment.subject.value,
                'is_invigilation': assignment.is_invigilation,
                'duration_minutes': assignment.time_slot.duration_minutes
            })

        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        csv_files.append(csv_path)
        print(f"CSV文件已导出: {csv_path}")

        return csv_files

    def generate_summary_report(self) -> Dict[str, Any]:
        """生成摘要报告"""
        summary = {
            'basic_info': {
                'teacher_count': len(self.schedule.teachers),
                'room_count': len(self.schedule.rooms),
                'exam_count': len(self.schedule.exams),
                'assignment_count': len(self.schedule.assignments)
            },
            'fairness': self.stats.get('fairness_metrics', {}),
            'conflicts': {
                'count': len(self.stats.get('constraint_stats', {}).get('conflicts', [])),
                'details': self.stats.get('constraint_stats', {}).get('conflicts', [])[:5]
            },
            'load_analysis': {
                'avg_load': self.stats.get('fairness_metrics', {}).get('avg_total_load', 0),
                'load_range': self.stats.get('fairness_metrics', {}).get('load_range', 0),
                'max_load_teacher': '',
                'min_load_teacher': ''
            }
        }

        # 找出负荷最大和最小的教师
        teacher_stats = self.stats.get('teacher_stats', [])
        if teacher_stats:
            max_teacher = max(teacher_stats, key=lambda x: x['total_weighted_load'])
            min_teacher = min(teacher_stats, key=lambda x: x['total_weighted_load'])

            summary['load_analysis']['max_load_teacher'] = f"{max_teacher['teacher_name']}({max_teacher['total_weighted_load']:.2f})"
            summary['load_analysis']['min_load_teacher'] = f"{min_teacher['teacher_name']}({min_teacher['total_weighted_load']:.2f})"

        return summary


def main():
    """测试可视化功能"""
    from data_generator import DataGenerator
    from ortools_solver import ORToolsSolver

    print("生成测试数据...")
    generator = DataGenerator()
    schedule = generator.create_small_test_case()

    print("使用OR-Tools求解...")
    solver = ORToolsSolver(schedule)
    solver.build_model()

    if solver.solve():
        result_schedule = solver.get_schedule()

        print("生成可视化报告...")
        visualizer = ResultVisualizer(result_schedule)

        # 生成综合报告
        report_path = visualizer.generate_comprehensive_report()

        # 生成图表
        load_chart = visualizer.plot_load_distribution()
        heatmap = visualizer.plot_schedule_heatmap()

        # 导出Excel
        excel_files = visualizer.export_to_excel()

        # 导出CSV
        csv_files = visualizer.export_to_csv()

        # 生成摘要
        summary = visualizer.generate_summary_report()
        print("\n=== 摘要报告 ===")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
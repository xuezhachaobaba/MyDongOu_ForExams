# 智能排考系统

基于运筹学算法的智能监考排班系统，支持OR-Tools约束规划和DEAP遗传算法两种求解方法。

## 🎯 功能特性

- **智能排考**: 基于约束优化算法自动生成公平、无冲突的监考安排
- **双算法支持**: OR-Tools精确算法 + DEAP遗传算法
- **多规模支持**: 最大支持400名教师、10个科目、200个考场的排考任务
- **完整约束实现**: 9个硬约束 + 6个软约束
- **可视化报表**: 负荷分析、冲突检查、多种导出格式
- **命令行界面**: 简单易用的CLI操作

## 📋 约束规则

### 硬约束（必须100%满足）
- **H-E-01**: 教师时空冲突（同一时间只能监考一个考场）
- **H-E-02**: 授课时间冲突（不能与教师授课时间冲突）
- **H-E-03**: 请假时间（已请假教师不能排监考）
- **H-E-04**: 改卷时间（科目考完后T+1天该科目教师不可监考）
- **H-E-05**: 学科回避（教师不能监考自己教授的科目）
- **H-E-06**: 考场模式（支持原班考试和打乱考场）
- **H-E-07**: 学生匹配（按选课情况正确分配）
- **H-E-08**: 时段上限（半天最多3场考试）
- **H-E-09**: 固定任务计入（固定坐班时间计入负荷）

### 软约束（优化目标）
- **S-E-01**: 历史公平性（加权总负荷均衡）
- **S-E-02**: 当次任务负荷（监考=1.0，自习=0.5）
- **S-E-03**: 长时科目平衡（避免过多长时科目监考）
- **S-E-04**: 午休保障（不安排跨午休的连续监考）
- **S-E-05**: 任务集中度（任务尽量集中在半天）
- **S-E-06**: 每日负荷（每天舒适安排2场监考）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 基本使用

```bash
# 使用默认设置运行小型测试
python main.py

# 运行中等规模测试
python main.py --size medium

# 运行大型测试（400名教师）
python main.py --size large --algorithm auto
```

### 3. 高级用法

```bash
# 只使用OR-Tools求解
python main.py --size medium --algorithm ortools --time-limit 120

# 使用DEAP遗传算法
python main.py --size medium --algorithm deap --population 300 --generations 150

# 导出多种格式
python main.py --size medium --output my_results --formats excel html charts csv

# 运行基准测试
python main.py --benchmark
```

## 📊 结果输出

系统会生成以下输出文件：

- **Excel监考表**: 总监考表、分教师表、分时间表、分考场表
- **HTML报告**: 完整的分析报告和统计信息
- **可视化图表**: 负荷分布图、监考安排热力图
- **CSV数据**: 便于其他系统处理的原始数据

## 📁 项目结构

```
01my/
├── models.py              # 核心数据模型
├── data_generator.py      # 测试数据生成器
├── ortools_solver.py      # OR-Tools约束规划求解器
├── deap_solver.py         # DEAP遗传算法求解器
├── visualization.py       # 结果可视化和导出
├── test_cases.py         # 测试用例和基准测试
├── main.py              # 主程序入口
├── requirements.txt      # 依赖包列表
└── README.md           # 项目说明文档
```

## 🛠️ 开发使用

### 自定义数据生成

```python
from data_generator import DataGenerator, SubjectType
from main import IntelligentExamScheduler

# 创建自定义配置
custom_config = {
    'teacher_count': 300,
    'subjects': [SubjectType.CHINESE, SubjectType.MATH, SubjectType.PHYSICS],
    'rooms_per_exam': 15
}

scheduler = IntelligentExamScheduler()
scheduler.generate_test_data('custom', custom_config)
scheduler.solve_with_ortools()
scheduler.export_results('my_output')
```

### 直接调用算法

```python
from ortools_solver import ORToolsSolver
from deap_solver import DEAPSolver

# OR-Tools求解
solver = ORToolsSolver(schedule)
solver.build_model()
if solver.solve():
    result = solver.get_schedule()

# DEAP求解
solver = DEAPSolver(schedule, population_size=200, generations=100)
if solver.solve():
    result = solver.get_schedule()
```

## 📈 性能指标

| 问题规模 | 教师数 | 考场数 | OR-Tools时间 | DEAP时间 | 推荐算法 |
|---------|--------|--------|-------------|---------|----------|
| 小型    | 50     | 15     | <1秒        | <5秒    | OR-Tools |
| 中型    | 200    | 50     | 5-15秒      | 10-30秒 | OR-Tools |
| 大型    | 400    | 200    | 30-60秒     | 60-120秒| OR-Tools |

## ⚙️ 配置参数

### 约束权重配置

```python
from models import ConstraintConfig

config = ConstraintConfig(
    invigilation_coefficient=1.0,    # 监考负荷系数
    study_coefficient=0.5,           # 自习负荷系数
    current_weight=0.5,              # 本次负荷权重
    historical_weight=0.5,           # 历史负荷权重
    fairness_weight=1000.0,          # 公平性权重
    long_exam_weight=100.0,          # 长时科目权重
    lunch_weight=200.0,              # 午休保障权重
    daily_limit_weight=50.0,         # 每日负荷权重
    concentration_weight=30.0,        # 任务集中度权重
    daily_comfort_limit=2             # 每日舒适上限
)
```

### 求解器参数

- **OR-Tools**:
  - `max_time_in_seconds`: 最大求解时间（默认60秒）
  - `num_search_workers`: 搜索线程数（默认8）

- **DEAP**:
  - `population_size`: 种群大小（默认200）
  - `generations`: 迭代代数（默认100）
  - `cxpb`: 交叉概率（0.7）
  - `mutpb`: 变异概率（0.3）

## 🧪 测试

```bash
# 运行所有测试
python test_cases.py

# 运行特定测试
python -m unittest test_cases.TestExamScheduler.test_small_case
```

## 📋 命令行参数详解

| 参数 | 选项 | 默认值 | 说明 |
|------|------|--------|------|
| --size | small/medium/large/custom | small | 测试数据规模 |
| --algorithm | ortools/deap/auto | auto | 求解算法选择 |
| --output | 目录名 | output | 输出目录 |
| --formats | excel/html/charts/csv | [excel, html] | 导出格式 |
| --time-limit | 秒数 | 60 | OR-Tools时间限制 |
| --population | 整数 | 200 | DEAP种群大小 |
| --generations | 整数 | 100 | DEAP迭代代数 |
| --benchmark | 布尔值 | False | 运行基准测试 |
| --no-export | 布尔值 | False | 不导出结果 |

## 🔧 故障排除

### 常见问题

1. **OR-Tools安装失败**
   ```bash
   # 尝试使用conda安装
   conda install -c conda-forge ortools

   # 或使用国内镜像
   pip install ortools -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

2. **DEAP收敛慢**
   - 增加种群大小：`--population 500`
   - 增加迭代代数：`--generations 200`
   - 或改用OR-Tools算法

3. **内存不足**
   - 减小问题规模：使用small或medium
   - 减少种群大小：`--population 100`
   - 减少输出格式：只导出excel

4. **中文显示问题**
   ```python
   import matplotlib.pyplot as plt
   plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
   ```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📧 联系方式

如有问题或建议，请通过GitHub Issues联系。
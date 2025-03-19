# MySQL索引优化分析工具

这是一个用Python实现的MySQL索引性能分析和可视化工具，可以帮助数据库开发人员和管理员优化查询性能。通过自动化测试不同索引策略下的查询性能，直观展示索引效果，提供优化建议，助您提升数据库查询效率。

## 功能特点

- **自动化测试**：自动测试无索引、单列索引和联合索引下的查询性能
- **慢查询日志分析**：解析MySQL慢查询日志，识别潜在的性能问题
- **可视化报告**：生成丰富的图表和报告，直观展示索引效果
- **优化建议**：提供智能索引优化建议（包括单列索引、联合索引、覆盖索引等）
- **性能对比**：量化展示不同索引策略的性能提升百分比

## 项目结构

```
mysql_index_analyzer/
├── data/                 # 存放测试数据和结果
├── scripts/              # 脚本文件
│   ├── main.py                 # 主程序入口
│   ├── data_generator.py       # 生成测试数据
│   ├── index_tester.py         # 索引测试框架
│   ├── log_analyzer.py         # 慢查询日志分析
│   ├── visualizer.py           # 数据可视化
│   ├── cleanup.py              # 清理工具
│   └── check_environment.py    # 环境检查脚本
├── visualization/        # 存放生成的图表
└── logs/                 # 存放日志文件
```

## 环境要求

- Python 3.8+
- MySQL 8.0+
- 以下Python库：
  - mysql-connector-python
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - sqlparse
  - pymysql
  - faker

## 快速开始

1. 克隆本仓库：
```bash
git clone https://github.com/yourusername/mysql-index-analyzer.git
cd mysql-index-analyzer
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行完整工作流程：
```bash
python mysql_index_analyzer/scripts/main.py all --scale 0.1
```

## 使用方法

### 命令行界面

本工具提供了简单的命令行界面，可以方便地执行各项功能：

```bash
# 检查环境
python mysql_index_analyzer/scripts/main.py check

# 生成测试数据（可选择缩放因子调整数据量大小）
python mysql_index_analyzer/scripts/main.py generate --scale 0.1

# 运行索引测试
python mysql_index_analyzer/scripts/main.py test

# 分析慢查询日志
python mysql_index_analyzer/scripts/main.py analyze /path/to/slow-query.log

# 可视化结果
python mysql_index_analyzer/scripts/main.py visualize

# 执行完整工作流程（数据生成、测试和可视化）
python mysql_index_analyzer/scripts/main.py all --scale 0.1

# 清理数据（删除所有数据、索引和图表）
python mysql_index_analyzer/scripts/cleanup.py
```

### 单独使用各模块

也可以单独运行各个模块：

1. 检查环境：
```bash
python mysql_index_analyzer/scripts/check_environment.py
```

2. 生成测试数据：
```bash
# 使用默认数据量
python mysql_index_analyzer/scripts/data_generator.py

# 使用缩放因子调整数据量（例如，使用原始数据的10%）
python mysql_index_analyzer/scripts/data_generator.py 0.1
```

3. 执行索引测试：
```bash
python mysql_index_analyzer/scripts/index_tester.py
```

4. 分析慢查询日志：
```bash
python mysql_index_analyzer/scripts/log_analyzer.py /path/to/slow-query.log
```

5. 可视化结果：
```bash
python mysql_index_analyzer/scripts/visualizer.py /path/to/test_results.json
```

6. 清理数据：
```bash
python mysql_index_analyzer/scripts/cleanup.py
```

## 工作流程说明

1. **数据生成阶段**
   - 创建测试数据库和表（用户、产品、订单）
   - 生成大量随机测试数据
   - 根据参数调整数据量大小

2. **索引测试阶段**
   - 执行无索引情况下的基准测试
   - 创建并测试单列索引的性能
   - 创建并测试联合索引的性能
   - 记录每次测试的执行时间和查询计划

3. **数据分析阶段**
   - 计算各种索引策略的性能提升
   - 生成性能对比数据
   - 提供索引使用建议

4. **可视化报告阶段**
   - 生成柱状图和折线图对比查询时间
   - 生成性能提升百分比图表
   - 生成性能热图
   - 输出详细的文本报告

## 慢查询日志分析

本工具还提供了慢查询日志分析功能，可以帮助您分析生产环境中的实际查询性能问题：

1. 确保MySQL已启用慢查询日志：
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1; -- 设置阈值（秒）
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';
```

2. 使用工具分析慢查询日志：
```bash
python mysql_index_analyzer/scripts/log_analyzer.py /var/log/mysql/slow-query.log
```

3. 查看分析结果和优化建议

## 使用示例

以下是典型的使用流程示例：

```bash
# 1. 首先检查环境
python mysql_index_analyzer/scripts/main.py check

# 2. 生成测试数据（使用10%的默认数据量）
python mysql_index_analyzer/scripts/main.py generate --scale 0.1

# 3. 运行索引测试
python mysql_index_analyzer/scripts/main.py test

# 4. 查看可视化结果
python mysql_index_analyzer/scripts/main.py visualize

# 5. 完成后清理数据
python mysql_index_analyzer/scripts/cleanup.py
```

或者，简单地运行完整工作流程：

```bash
python mysql_index_analyzer/scripts/main.py all --scale 0.1
```

## 注意事项

- 生成大量测试数据可能需要较长时间，请耐心等待
- 测试结果保存在data目录下，可视化图表保存在visualization目录下
- 请确保MySQL服务正在运行且配置正确
- 默认使用root用户连接本地MySQL，如需修改连接信息，请编辑相应脚本中的DB_CONFIG变量
- 生产环境分析前建议备份数据库

## 贡献

欢迎提交问题和改进建议，您可以fork本项目并提交pull request。

## 许可证

MIT License 
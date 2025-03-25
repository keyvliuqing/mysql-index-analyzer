# MySQL慢查询日志分析工具

## 项目概述

这个工具是MySQL索引分析系统的组成部分，专门用于分析MySQL慢查询日志，识别性能瓶颈，并提供优化建议。通过分析慢查询日志，DBA和开发人员可以快速定位需要优化的SQL查询，并获得针对性的索引和查询重写建议。

## 功能特性

- **慢查询日志解析**：解析标准MySQL慢查询日志格式
- **查询分析**：识别执行慢的SQL查询，分析其执行计划
- **索引推荐**：基于查询模式推荐合适的索引结构
- **性能可视化**：生成查询时间分布、最慢查询排名等可视化图表
- **优化建议**：提供查询重写和数据库配置优化建议
- **离线分析**：提供不需要MySQL连接的简化版分析工具

## 目录结构

```
slow_query_analyzer/
├── parse_slow_log.py          # 简化版慢查询日志分析工具（无需MySQL连接）
├── example-slow-query.log     # 示例慢查询日志文件
├── slow_query_analysis_report.md  # 分析报告示例
├── mysql_slow_query_howto.md  # 使用指南
└── README.md                  # 本文档
```

同时，完整版分析工具位于：
```
mysql_index_analyzer/
└── scripts/
    └── log_analyzer.py        # 完整版慢查询日志分析工具（需要MySQL连接）
```

## 快速开始

### 1. 准备慢查询日志

确保MySQL已启用慢查询日志功能：

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
SET GLOBAL slow_query_log_file = '/path/to/mysql-slow.log';
```

### 2. 使用分析工具

#### 完整版分析（需要MySQL连接）

```bash
# 使用方法
python mysql_index_analyzer/scripts/log_analyzer.py <慢查询日志文件路径>

# 示例
python mysql_index_analyzer/scripts/log_analyzer.py /var/log/mysql/mysql-slow.log
```

#### 简化版分析（无需MySQL连接）

```bash
# 使用方法
python slow_query_analyzer/parse_slow_log.py <慢查询日志文件路径>

# 示例
python slow_query_analyzer/parse_slow_log.py slow_query_analyzer/example-slow-query.log
```

### 3. 查看分析结果

- 分析结果将保存在JSON文件中
- 控制台将输出关键的优化建议摘要

## 示例

本项目提供了示例慢查询日志文件`example-slow-query.log`和相应的分析报告`slow_query_analysis_report.md`，您可以参考这些文件了解分析结果的格式和内容。

## 使用指南

详细的使用指南请参考[MySQL慢查询日志分析使用指南](mysql_slow_query_howto.md)。

## 依赖项

- Python 3.6+
- 如果使用完整版分析工具，还需要：
  - mysql-connector-python
  - pandas
  - matplotlib
  - numpy

## 注意事项

- 使用完整版分析工具时，请确保MySQL服务器正在运行且连接配置正确
- 处理大型日志文件可能需要较长时间，请耐心等待
- 某些优化建议可能需要结合具体业务场景进行评估

## 常见问题

**Q: 工具无法连接到MySQL服务器怎么办？**  
A: 检查`log_analyzer.py`文件开头的`DB_CONFIG`配置，确保用户名、密码和主机信息正确。

**Q: 如何解读"效率比"指标？**  
A: 效率比是返回行数与检查行数的比值。比值越低，表示查询效率越差，优化空间越大。

**Q: 慢查询日志文件的格式不正确怎么办？**  
A: 确保使用标准的MySQL慢查询日志格式。非标准格式可能导致解析错误。

## 维护者

该工具由MySQL索引分析系统团队开发和维护。

## 许可证

使用开源MIT许可证。详见LICENSE文件。 
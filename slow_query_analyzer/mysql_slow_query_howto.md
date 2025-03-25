# MySQL慢查询日志分析使用指南

## 1. 慢查询日志简介

MySQL慢查询日志是一种重要的性能诊断工具，它记录执行时间超过指定阈值的SQL查询。通过分析这些慢查询，DBA和开发人员可以识别数据库性能瓶颈，针对性地进行优化。

## 2. 开启MySQL慢查询日志

在使用分析工具前，需要先开启MySQL的慢查询日志功能：

### Windows系统配置

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
-- 设置慢查询时间阈值（单位：秒）
SET GLOBAL long_query_time = 1;
-- 设置慢查询日志文件位置（Windows示例）
SET GLOBAL slow_query_log_file = 'C:/ProgramData/MySQL/MySQL Server 8.0/Data/mysql-slow.log';
```

### Linux系统配置

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
-- 设置慢查询时间阈值（单位：秒）
SET GLOBAL long_query_time = 1;
-- 设置慢查询日志文件位置（Linux示例）
SET GLOBAL slow_query_log_file = '/var/log/mysql/mysql-slow.log';
```

### my.cnf文件配置（推荐）

在MySQL配置文件中添加以下内容，可以在MySQL重启后依然保持设置：

```
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/mysql-slow.log
long_query_time = 1
log_queries_not_using_indexes = 1
```

## 3. 使用我们的分析工具

本项目提供了两种分析慢查询日志的方式：

### 3.1 使用原始log_analyzer.py（需要MySQL连接）

使用这种方式，工具会解析日志并尝试连接到MySQL以获取额外的信息，如表结构和索引信息，便于提供更精确的优化建议。

```bash
# 使用方法
python mysql_index_analyzer/scripts/log_analyzer.py <慢查询日志文件路径>

# 示例
python mysql_index_analyzer/scripts/log_analyzer.py /var/log/mysql/mysql-slow.log
```

**注意**：使用这种方式需要满足以下条件：
- MySQL服务器正在运行
- 连接配置正确（默认用户名：root，密码：123456，可在脚本文件开头修改）
- 对应的数据库存在

### 3.2 使用简化版parse_slow_log.py（无需MySQL连接）

如果您只想分析日志文件，而不需要获取额外的数据库信息，可以使用我们提供的简化版分析工具：

```bash
# 使用方法
python slow_query_analyzer/parse_slow_log.py <慢查询日志文件路径>

# 示例
python slow_query_analyzer/parse_slow_log.py slow_query_analyzer/example-slow-query.log
```

这种方式的优点是：
- 不需要MySQL连接
- 适用于离线分析或没有数据库访问权限的情况
- 执行速度更快

## 4. 分析报告解读

分析完成后，工具会生成以下内容：

1. **JSON格式的查询详情**：包含所有慢查询的详细信息
2. **分析报告摘要**：显示最慢的查询和主要优化建议
3. **可视化图表**（仅完整版）：包括查询时间分布、最慢查询排名等

### 报告中的关键指标：

- **查询时间**：执行SQL语句所需的总时间
- **锁定时间**：在获取锁时所花费的时间
- **检查行数**：MySQL扫描的行数
- **返回行数**：最终返回给客户端的行数
- **效率比**：返回行数/检查行数，越低表示查询效率越低

## 5. 常见优化建议

基于分析报告，通常可以采取以下优化措施：

1. **添加合适的索引**：
   - 为WHERE子句中的列添加索引
   - 为JOIN条件中的列添加索引
   - 为GROUP BY和ORDER BY中的列添加索引

2. **优化查询语句**：
   - 避免SELECT *，只选择需要的列
   - 限制返回的行数（使用LIMIT）
   - 重写复杂查询为更简单的形式

3. **数据库配置优化**：
   - 调整缓冲区大小
   - 优化连接池
   - 调整排序和临时表的内存分配

## 6. 示例日志

本项目包含一个示例的慢查询日志文件`slow_query_analyzer/example-slow-query.log`，您可以用它来测试分析工具：

```bash
python slow_query_analyzer/parse_slow_log.py slow_query_analyzer/example-slow-query.log
```

## 7. 故障排除

如果遇到问题，请检查：

1. 日志文件格式是否正确
2. MySQL连接配置是否正确
3. 是否有足够的权限读取日志文件和连接数据库

## 8. 后续开发计划

我们计划为该工具添加更多功能：

- 自动索引推荐和应用
- 图形用户界面
- 持续监控和报警机制

如有问题或建议，请通过GitHub Issues与我们联系。 
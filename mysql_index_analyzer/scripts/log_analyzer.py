#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL索引测试 - 慢查询日志分析器
分析MySQL慢查询日志，提取查询模式，并提供索引优化建议
"""

import re
import os
import sys
import json
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import sqlparse
import mysql.connector
from collections import defaultdict, Counter

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['font.family'] = 'sans-serif'

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # 使用root用户
    'password': '123456',  # root用户密码
    'charset': 'utf8mb4',
    'use_unicode': True,
    'get_warnings': True
}

# 输出目录配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RESULT_DIR = os.path.join(PROJECT_DIR, "data")  # 结果保存目录
VISUALIZATION_DIR = os.path.join(PROJECT_DIR, "visualization")  # 可视化结果保存目录

# 确保结果目录存在
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(VISUALIZATION_DIR, exist_ok=True)

class SlowQueryLogParser:
    """慢查询日志解析器"""
    
    def __init__(self, log_file=None):
        """初始化解析器"""
        self.log_file = log_file
        self.queries = []
        self.current_query = None
        
    def parse_log_file(self, log_file=None):
        """解析慢查询日志文件"""
        if log_file:
            self.log_file = log_file
            
        if not self.log_file:
            raise ValueError("未指定慢查询日志文件")
            
        print(f"开始解析慢查询日志文件: {self.log_file}")
        
        # 正则表达式模式
        time_pattern = re.compile(r"# Time: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z)")
        user_pattern = re.compile(r"# User@Host: ([^\[]+)")
        query_time_pattern = re.compile(r"# Query_time: (\d+\.\d+)\s+Lock_time: (\d+\.\d+)\s+Rows_sent: (\d+)\s+Rows_examined: (\d+)")
        schema_pattern = re.compile(r"use ([^;]+);")
        
        # 解析日志
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = []
            in_query = False
            self.queries = []
            
            for line in f:
                line = line.strip()
                
                # 检查是否是新查询的开始
                if line.startswith("# Time:"):
                    # 如果已经在处理一个查询，保存它
                    if in_query and lines:
                        self._process_query(lines)
                        lines = []
                        
                    # 开始新的查询
                    in_query = True
                    lines.append(line)
                elif in_query:
                    lines.append(line)
                    
            # 处理最后一个查询
            if in_query and lines:
                self._process_query(lines)
                
        print(f"解析完成，共提取到 {len(self.queries)} 条慢查询")
        return self.queries
    
    def _process_query(self, lines):
        """处理单个查询的日志行"""
        query_info = {
            'timestamp': None,
            'user': None,
            'host': None,
            'query_time': None,
            'lock_time': None,
            'rows_sent': None,
            'rows_examined': None,
            'schema': None,
            'query': None
        }
        
        query_lines = []
        for line in lines:
            if line.startswith("# Time:"):
                match = re.search(r"# Time: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z)", line)
                if match:
                    query_info['timestamp'] = match.group(1)
            elif line.startswith("# User@Host:"):
                match = re.search(r"# User@Host: ([^[]+)(?:\[([^]]+)\])? @ ([^[]+)(?:\[([^]]+)\])?", line)
                if match:
                    query_info['user'] = match.group(1).strip()
                    query_info['host'] = match.group(3).strip() if match.group(3) else None
            elif line.startswith("# Query_time:"):
                match = re.search(r"# Query_time: (\d+\.\d+)\s+Lock_time: (\d+\.\d+)\s+Rows_sent: (\d+)\s+Rows_examined: (\d+)", line)
                if match:
                    query_info['query_time'] = float(match.group(1))
                    query_info['lock_time'] = float(match.group(2))
                    query_info['rows_sent'] = int(match.group(3))
                    query_info['rows_examined'] = int(match.group(4))
            elif line.startswith("use "):
                match = re.search(r"use ([^;]+);", line)
                if match:
                    query_info['schema'] = match.group(1).strip()
            elif not line.startswith("#"):
                query_lines.append(line)
                
        # 合并查询行
        query_text = " ".join(query_lines).strip()
        if query_text:
            query_info['query'] = query_text
            self.queries.append(query_info)
    
    def get_dataframe(self):
        """将查询信息转换为DataFrame"""
        return pd.DataFrame(self.queries)
    
    def save_to_json(self, output_file):
        """保存查询信息到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.queries, f, ensure_ascii=False, indent=2)
        print(f"查询信息已保存到: {output_file}")


class QueryAnalyzer:
    """查询分析器"""
    
    def __init__(self, db_config=None):
        """初始化分析器"""
        self.db_config = db_config or DB_CONFIG
        self.conn = None
        self.cursor = None
        
    def connect_to_db(self):
        """连接到数据库"""
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor(dictionary=True)
            print(f"已连接到MySQL服务器")
            return True
        except Exception as e:
            print(f"连接到数据库时出错: {e}")
            return False
            
    def close_connection(self):
        """关闭数据库连接"""
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print("数据库连接已关闭")
    
    def analyze_query(self, query, schema=None):
        """分析单个查询"""
        if not self.conn or not self.conn.is_connected():
            if not self.connect_to_db():
                return None
                
        # 解析查询
        try:
            # 如果指定了数据库，切换到该数据库
            if schema:
                self.cursor.execute(f"USE {schema}")
                
            # 使用EXPLAIN分析查询
            explain_query = "EXPLAIN " + query
            self.cursor.execute(explain_query)
            explain_result = self.cursor.fetchall()
            
            # 分析结果
            analysis = {
                'query': query,
                'schema': schema,
                'explain': explain_result,
                'suggestions': self._generate_suggestions(explain_result, query)
            }
            
            return analysis
        except Exception as e:
            print(f"分析查询时出错: {e}")
            print(f"查询: {query}")
            return {
                'query': query,
                'schema': schema,
                'error': str(e)
            }
    
    def _generate_suggestions(self, explain_result, query):
        """根据EXPLAIN结果生成索引建议"""
        suggestions = []
        
        # 解析查询
        parsed = sqlparse.parse(query)
        if not parsed:
            return suggestions
            
        stmt = parsed[0]
        
        # 检查是否为SELECT查询
        if stmt.get_type() != 'SELECT':
            return suggestions
            
        # 检查EXPLAIN结果
        for row in explain_result:
            # 检查是否使用了索引
            key = row.get('key', None)
            table = row.get('table', None)
            
            if not key and table:
                # 没有使用索引
                suggestions.append({
                    'type': 'missing_index',
                    'table': table,
                    'message': f"表 {table} 没有使用索引，可能需要添加索引"
                })
                
            # 检查是否进行了全表扫描
            if row.get('type', '') in ('ALL', 'index'):
                suggestions.append({
                    'type': 'full_scan',
                    'table': table,
                    'message': f"表 {table} 进行了{'全表' if row['type'] == 'ALL' else '索引全'}扫描，应考虑优化查询或添加合适的索引"
                })
                
            # 检查是否有大量行被扫描
            rows = row.get('rows', 0)
            if rows and int(rows) > 1000:
                suggestions.append({
                    'type': 'high_rows',
                    'table': table,
                    'rows': rows,
                    'message': f"查询扫描了大量行 ({rows})，可能需要优化索引或查询条件"
                })
                
            # 检查是否使用了临时表或文件排序
            extra = row.get('Extra', '')
            if 'Using temporary' in extra:
                suggestions.append({
                    'type': 'temp_table',
                    'table': table,
                    'message': f"查询使用了临时表，可能需要添加索引以避免这种情况"
                })
                
            if 'Using filesort' in extra:
                suggestions.append({
                    'type': 'filesort',
                    'table': table,
                    'message': f"查询使用了文件排序，可能需要添加适合的索引以优化ORDER BY子句"
                })
        
        # 提取查询中的WHERE条件字段
        where_columns = self._extract_where_columns(stmt)
        if where_columns:
            suggestions.append({
                'type': 'where_columns',
                'columns': where_columns,
                'message': f"考虑在以下WHERE条件字段上创建索引: {', '.join(where_columns)}"
            })
            
            # 检查是否有多个AND条件，可能适合联合索引
            if len(where_columns) > 1:
                suggestions.append({
                    'type': 'composite_index',
                    'columns': where_columns,
                    'message': f"多个WHERE条件字段可能适合使用联合索引: {', '.join(where_columns)}"
                })
        
        # 提取ORDER BY和GROUP BY列
        order_by_columns = self._extract_order_by_columns(stmt)
        group_by_columns = self._extract_group_by_columns(stmt)
        
        if order_by_columns:
            suggestions.append({
                'type': 'order_by',
                'columns': order_by_columns,
                'message': f"ORDER BY子句中的列可能需要索引: {', '.join(order_by_columns)}"
            })
            
        if group_by_columns:
            suggestions.append({
                'type': 'group_by',
                'columns': group_by_columns,
                'message': f"GROUP BY子句中的列可能需要索引: {', '.join(group_by_columns)}"
            })
            
        # 检查是否可以使用覆盖索引
        select_columns = self._extract_select_columns(stmt)
        if select_columns and where_columns:
            all_columns = list(set(select_columns + where_columns + order_by_columns + group_by_columns))
            if 1 < len(all_columns) <= 5:  # 限制索引列数
                suggestions.append({
                    'type': 'covering_index',
                    'columns': all_columns,
                    'message': f"可以考虑创建覆盖索引，包含所有相关列: {', '.join(all_columns)}"
                })
        
        return suggestions
    
    def _extract_where_columns(self, stmt):
        """提取WHERE子句中的列名"""
        columns = []
        
        def _process_token(token):
            if token.ttype is None and token.is_group:
                if token.tokens[0].value.upper() == 'WHERE':
                    # 这是一个WHERE子句
                    for where_token in token.tokens:
                        if isinstance(where_token, sqlparse.sql.Comparison):
                            # 提取比较操作符左侧的列名
                            left = where_token.left
                            if isinstance(left, sqlparse.sql.Identifier):
                                columns.append(left.value)
                        elif where_token.ttype is None and where_token.is_group:
                            # 递归处理子组
                            _process_token(where_token)
                else:
                    # 递归处理所有子组
                    for sub_token in token.tokens:
                        _process_token(sub_token)
        
        for token in stmt.tokens:
            _process_token(token)
            
        return list(set(columns))
    
    def _extract_order_by_columns(self, stmt):
        """提取ORDER BY子句中的列名"""
        columns = []
        
        def _process_token(token):
            if token.ttype is None and token.is_group:
                if token.tokens[0].value.upper() == 'ORDER BY':
                    # 这是一个ORDER BY子句
                    for i, order_token in enumerate(token.tokens):
                        if isinstance(order_token, sqlparse.sql.Identifier):
                            columns.append(order_token.value)
                        elif order_token.ttype is None and order_token.is_group:
                            # 递归处理子组
                            _process_token(order_token)
                else:
                    # 递归处理所有子组
                    for sub_token in token.tokens:
                        _process_token(sub_token)
        
        for token in stmt.tokens:
            _process_token(token)
            
        return list(set(columns))
    
    def _extract_group_by_columns(self, stmt):
        """提取GROUP BY子句中的列名"""
        columns = []
        
        def _process_token(token):
            if token.ttype is None and token.is_group:
                if token.tokens[0].value.upper() == 'GROUP BY':
                    # 这是一个GROUP BY子句
                    for i, group_token in enumerate(token.tokens):
                        if isinstance(group_token, sqlparse.sql.Identifier):
                            columns.append(group_token.value)
                        elif group_token.ttype is None and group_token.is_group:
                            # 递归处理子组
                            _process_token(group_token)
                else:
                    # 递归处理所有子组
                    for sub_token in token.tokens:
                        _process_token(sub_token)
        
        for token in stmt.tokens:
            _process_token(token)
            
        return list(set(columns))
    
    def _extract_select_columns(self, stmt):
        """提取SELECT子句中的列名"""
        columns = []
        
        for token in stmt.tokens:
            if isinstance(token, sqlparse.sql.IdentifierList):
                # 多个列
                for identifier in token.get_identifiers():
                    if not '*' in identifier.value:  # 忽略 *
                        columns.append(identifier.value)
            elif isinstance(token, sqlparse.sql.Identifier):
                # 单个列
                if not '*' in token.value:  # 忽略 *
                    columns.append(token.value)
                    
        return columns


class SlowQueryAnalyzer:
    """慢查询分析器"""
    
    def __init__(self, log_file=None, db_config=None):
        """初始化"""
        self.log_file = log_file
        self.db_config = db_config or DB_CONFIG
        self.parser = SlowQueryLogParser(log_file)
        self.query_analyzer = QueryAnalyzer(db_config)
        self.queries = []
        self.analysis_results = []
        
    def load_log(self, log_file=None):
        """加载慢查询日志"""
        if log_file:
            self.log_file = log_file
        self.queries = self.parser.parse_log_file(self.log_file)
        return self.queries
        
    def analyze_queries(self):
        """分析所有慢查询"""
        print("开始分析慢查询...")
        self.query_analyzer.connect_to_db()
        
        self.analysis_results = []
        total_queries = len(self.queries)
        
        for i, query_info in enumerate(self.queries):
            print(f"分析查询 {i+1}/{total_queries}...")
            query = query_info.get('query')
            schema = query_info.get('schema')
            
            if query:
                # 清理查询文本
                query = query.strip()
                if query.endswith(';'):
                    query = query[:-1]
                    
                # 只分析SELECT查询
                if query.upper().startswith('SELECT'):
                    analysis = self.query_analyzer.analyze_query(query, schema)
                    if analysis:
                        # 合并查询信息和分析结果
                        result = {**query_info, **analysis}
                        self.analysis_results.append(result)
                else:
                    print(f"跳过非SELECT查询: {query[:60]}...")
            
        self.query_analyzer.close_connection()
        print(f"查询分析完成，共分析 {len(self.analysis_results)} 条查询")
        return self.analysis_results
    
    def generate_report(self):
        """生成分析报告"""
        if not self.analysis_results:
            print("没有分析结果，请先调用analyze_queries()")
            return None
            
        # 提取所有的建议
        all_suggestions = []
        for result in self.analysis_results:
            if 'suggestions' in result:
                for suggestion in result['suggestions']:
                    suggestion_copy = suggestion.copy()
                    suggestion_copy['query'] = result['query'][:100] + '...' if len(result['query']) > 100 else result['query']
                    suggestion_copy['query_time'] = result.get('query_time', 0)
                    all_suggestions.append(suggestion_copy)
        
        # 按建议类型分组
        suggestions_by_type = defaultdict(list)
        for suggestion in all_suggestions:
            suggestions_by_type[suggestion['type']].append(suggestion)
            
        # 统计每种建议类型的数量
        suggestion_counts = {type_name: len(suggestions) for type_name, suggestions in suggestions_by_type.items()}
        
        # 按表分组建议
        suggestions_by_table = defaultdict(list)
        for suggestion in all_suggestions:
            if 'table' in suggestion:
                suggestions_by_table[suggestion['table']].append(suggestion)
        
        # 统计需要添加索引的列
        index_columns = Counter()
        for suggestion in all_suggestions:
            if 'columns' in suggestion:
                for column in suggestion['columns']:
                    index_columns[column] += 1
                    
        # 生成报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_queries_analyzed': len(self.analysis_results),
            'total_suggestions': len(all_suggestions),
            'suggestion_counts': suggestion_counts,
            'suggestions_by_type': dict(suggestions_by_type),
            'suggestions_by_table': dict(suggestions_by_table),
            'recommended_indexes': [{'column': column, 'count': count} 
                                   for column, count in index_columns.most_common(20)]
        }
        
        return report
    
    def save_report(self, report, output_file):
        """保存报告到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"分析报告已保存到: {output_file}")
        
    def visualize_results(self, output_dir=None):
        """可视化分析结果"""
        if not self.analysis_results:
            print("没有分析结果，请先调用analyze_queries()")
            return
            
        output_dir = output_dir or VISUALIZATION_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 准备数据
        df = pd.DataFrame(self.analysis_results)
        
        if 'query_time' in df.columns:
            # 1. 查询时间分布
            plt.figure(figsize=(10, 6))
            plt.hist(df['query_time'], bins=20, alpha=0.7)
            plt.xlabel('查询时间 (秒)')
            plt.ylabel('查询数量')
            plt.title('慢查询时间分布')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"slow_query_time_distribution_{timestamp}.png"))
            plt.close()
            
            # 2. 最慢的10个查询
            if len(df) > 10:
                top_slow = df.nlargest(10, 'query_time')
                plt.figure(figsize=(12, 8))
                bars = plt.barh(range(len(top_slow)), top_slow['query_time'], alpha=0.7)
                plt.yticks(range(len(top_slow)), [q[:50] + '...' for q in top_slow['query']])
                plt.xlabel('查询时间 (秒)')
                plt.title('最慢的10个查询')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, f"top_10_slowest_queries_{timestamp}.png"))
                plt.close()
        
        # 3. 建议类型分布
        report = self.generate_report()
        if report and 'suggestion_counts' in report:
            suggestion_counts = report['suggestion_counts']
            plt.figure(figsize=(10, 6))
            plt.bar(suggestion_counts.keys(), suggestion_counts.values(), alpha=0.7)
            plt.xlabel('建议类型')
            plt.ylabel('数量')
            plt.title('索引优化建议类型分布')
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f"suggestion_type_distribution_{timestamp}.png"))
            plt.close()
            
            # 4. 推荐的索引列
            if 'recommended_indexes' in report and report['recommended_indexes']:
                top_indexes = report['recommended_indexes'][:10]  # 取前10个
                plt.figure(figsize=(12, 8))
                plt.barh([idx['column'] for idx in top_indexes], 
                        [idx['count'] for idx in top_indexes], 
                        alpha=0.7)
                plt.xlabel('推荐次数')
                plt.ylabel('列名')
                plt.title('推荐创建索引的前10个列')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, f"recommended_index_columns_{timestamp}.png"))
                plt.close()
        
        print(f"可视化结果已保存到目录: {output_dir}")


def main():
    """主函数"""
    print("========== MySQL索引测试 - 慢查询日志分析器 ==========")
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python log_analyzer.py <慢查询日志文件路径>")
        print("示例: python log_analyzer.py /var/log/mysql/slow-query.log")
        sys.exit(1)
        
    log_file = sys.argv[1]
    if not os.path.isfile(log_file):
        print(f"错误: 找不到慢查询日志文件: {log_file}")
        sys.exit(1)
        
    # 分析慢查询日志
    try:
        analyzer = SlowQueryAnalyzer(log_file)
        
        # 加载并解析日志
        print(f"加载慢查询日志: {log_file}")
        queries = analyzer.load_log()
        
        # 输出查询信息
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        queries_json = os.path.join(RESULT_DIR, f"slow_queries_{timestamp}.json")
        analyzer.parser.save_to_json(queries_json)
        
        # 分析查询
        print("\n开始分析查询...")
        analyzer.analyze_queries()
        
        # 生成报告
        print("\n生成分析报告...")
        report = analyzer.generate_report()
        if report:
            report_file = os.path.join(RESULT_DIR, f"slow_query_report_{timestamp}.json")
            analyzer.save_report(report, report_file)
            
            # 输出一些主要建议
            print("\n主要索引优化建议:")
            for i, idx in enumerate(report['recommended_indexes'][:5]):
                print(f"{i+1}. 列 '{idx['column']}' - 推荐次数: {idx['count']}")
                
            # 输出建议最多的表
            if report['suggestions_by_table']:
                print("\n需要优化的主要表:")
                table_counts = {table: len(suggestions) 
                              for table, suggestions in report['suggestions_by_table'].items()}
                for i, (table, count) in enumerate(sorted(table_counts.items(), 
                                                       key=lambda x: x[1], reverse=True)[:5]):
                    print(f"{i+1}. 表 '{table}' - 建议数: {count}")
            
        # 可视化结果
        print("\n生成可视化图表...")
        analyzer.visualize_results()
        
        print("\n分析完成！")
        
    except KeyboardInterrupt:
        print("\n分析被用户中断")
    except Exception as e:
        print(f"\n分析时出错: {e}")

if __name__ == "__main__":
    main() 
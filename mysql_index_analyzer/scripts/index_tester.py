#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL索引测试 - 索引测试框架
测试不同索引策略下的查询性能
"""

import time
import sys
import json
import os
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import random
from functools import wraps

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['font.family'] = 'sans-serif'

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # 使用root用户
    'password': '123456',  # root用户密码
    'database': 'index_analyzer_db',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'get_warnings': True
}

# 测试配置
TEST_ITERATIONS = 5  # 每个查询重复执行的次数
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RESULT_DIR = os.path.join(PROJECT_DIR, "data")  # 结果保存目录
VISUALIZATION_DIR = os.path.join(PROJECT_DIR, "visualization")  # 可视化结果保存目录

# 确保结果目录存在
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(VISUALIZATION_DIR, exist_ok=True)

def time_query(func):
    """装饰器：计时查询执行时间"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        return result, elapsed_time
    return wrapper

class IndexTester:
    """索引测试类"""
    
    def __init__(self):
        """初始化"""
        self.connect_to_db()
        self.results = {}
        
    def connect_to_db(self):
        """连接到数据库"""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            print(f"已连接到数据库: {DB_CONFIG['database']}")
        except Exception as e:
            print(f"连接到数据库时出错: {e}")
            sys.exit(1)
            
    def close_connection(self):
        """关闭数据库连接"""
        if self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()
            print("数据库连接已关闭")
            
    def execute_query(self, query, params=None, explain=False):
        """执行查询并返回结果"""
        try:
            if explain:
                query = "EXPLAIN " + query
                
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            if not explain:
                results = self.cursor.fetchall()
                return results
            else:
                explain_result = self.cursor.fetchall()
                return explain_result
        except Exception as e:
            print(f"执行查询时出错: {e}")
            print(f"查询: {query}")
            if params:
                print(f"参数: {params}")
            return None
            
    def create_index(self, table, columns, index_name=None, unique=False):
        """创建索引"""
        try:
            if not index_name:
                index_name = f"idx_{'_'.join(columns)}"
                
            index_type = "UNIQUE" if unique else ""
            column_str = ", ".join(columns)
            
            query = f"CREATE {index_type} INDEX {index_name} ON {table} ({column_str})"
            print(f"创建索引: {query}")
            
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"创建索引时出错: {e}")
            return False
            
    def drop_index(self, table, index_name):
        """删除索引"""
        try:
            query = f"DROP INDEX {index_name} ON {table}"
            print(f"删除索引: {query}")
            
            self.cursor.execute(query)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"删除索引时出错: {e}")
            return False
            
    def drop_all_indexes(self, table):
        """删除表上的所有非主键索引"""
        try:
            # 获取表上的所有索引
            query = f"""
            SELECT DISTINCT INDEX_NAME 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}' 
            AND TABLE_NAME = '{table}'
            AND INDEX_NAME != 'PRIMARY'
            """
            
            self.cursor.execute(query)
            indexes = self.cursor.fetchall()
            
            for index in indexes:
                self.drop_index(table, index['INDEX_NAME'])
                
            print(f"已删除表 {table} 上的所有非主键索引")
            return True
        except Exception as e:
            print(f"删除所有索引时出错: {e}")
            return False
            
    @time_query
    def run_single_query(self, query, params=None):
        """运行单个查询并返回结果"""
        return self.execute_query(query, params)
            
    def run_test_case(self, name, query, params=None, iterations=TEST_ITERATIONS):
        """运行测试用例，多次执行查询取平均时间"""
        print(f"\n执行测试用例: {name}")
        print(f"查询: {query}")
        if params:
            print(f"参数: {params}")
            
        # 执行EXPLAIN分析查询执行计划
        explain_results = self.execute_query(query, params, explain=True)
        print("\n查询执行计划:")
        for row in explain_results:
            print(json.dumps(row, ensure_ascii=False, indent=2))
            
        # 多次执行查询，记录时间
        total_time = 0
        times = []
        
        for i in range(iterations):
            print(f"执行第 {i+1}/{iterations} 次...")
            _, query_time = self.run_single_query(query, params)
            times.append(query_time)
            total_time += query_time
            print(f"耗时: {query_time:.6f}秒")
            
        # 计算平均时间和标准差
        avg_time = total_time / iterations
        
        # 保存结果
        test_result = {
            'name': name,
            'query': query,
            'explain': explain_results,
            'times': times,
            'avg_time': avg_time
        }
        
        if params:
            test_result['params'] = params
            
        print(f"\n测试用例 {name} 完成，平均耗时: {avg_time:.6f}秒")
        
        return test_result
        
    def run_index_tests(self):
        """运行所有索引测试"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 测试不同的索引策略
        self.test_no_indexes()
        self.test_single_column_indexes()
        self.test_multi_column_indexes()
        
        # 保存结果
        result_file = os.path.join(RESULT_DIR, f"index_test_results_{timestamp}.json")
        
        # 转换datetime对象为字符串，解决JSON序列化问题
        def datetime_converter(obj):
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=datetime_converter)
            
        print(f"\n测试结果已保存到: {result_file}")
        
        # 生成可视化
        self.visualize_results(timestamp)
        
    def test_no_indexes(self):
        """测试没有索引的情况"""
        print("\n==================== 测试没有索引的情况 ====================")
        
        # 删除所有非主键索引
        self.drop_all_indexes("users")
        self.drop_all_indexes("products")
        self.drop_all_indexes("orders")
        
        # 存储测试结果
        self.results['no_indexes'] = []
        
        # 测试用例1：按用户名查询
        query = "SELECT * FROM users WHERE username = %s"
        # 随机选择一个存在的用户名
        self.cursor.execute("SELECT username FROM users ORDER BY RAND() LIMIT 1")
        random_username = self.cursor.fetchone()['username']
        
        result = self.run_test_case(
            name="按用户名查询（无索引）",
            query=query,
            params=(random_username,)
        )
        self.results['no_indexes'].append(result)
        
        # 测试用例2：按用户注册日期范围查询
        query = """
        SELECT * FROM users 
        WHERE registration_date BETWEEN %s AND %s
        """
        # 设置一个随机的日期范围
        self.cursor.execute("SELECT MIN(registration_date), MAX(registration_date) FROM users")
        min_date, max_date = self.cursor.fetchone().values()
        
        # 将最小日期和最大日期之间分成10个区间，随机选择其中一个
        date_range = (max_date - min_date).days
        if date_range > 10:
            start_offset = random.randint(0, date_range // 2)
            end_offset = random.randint(date_range // 2, date_range)
            start_date = min_date + pd.Timedelta(days=start_offset)
            end_date = min_date + pd.Timedelta(days=end_offset)
            
            result = self.run_test_case(
                name="按用户注册日期范围查询（无索引）",
                query=query,
                params=(start_date, end_date)
            )
            self.results['no_indexes'].append(result)
        
        # 测试用例3：联表查询（用户订单）
        query = """
        SELECT u.username, o.order_date, o.total_price
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.credit_score > %s
        LIMIT 1000
        """
        
        result = self.run_test_case(
            name="用户订单联表查询（无索引）",
            query=query,
            params=(700,)  # 信用分大于700
        )
        self.results['no_indexes'].append(result)
        
        # 测试用例4：按产品类别统计订单数量
        query = """
        SELECT p.category, COUNT(*) as order_count, SUM(o.total_price) as total_sales
        FROM products p
        JOIN orders o ON p.id = o.product_id
        GROUP BY p.category
        """
        
        result = self.run_test_case(
            name="按产品类别统计订单（无索引）",
            query=query
        )
        self.results['no_indexes'].append(result)
        
    def test_single_column_indexes(self):
        """测试单列索引"""
        print("\n==================== 测试单列索引 ====================")
        
        # 删除所有非主键索引
        self.drop_all_indexes("users")
        self.drop_all_indexes("products")
        self.drop_all_indexes("orders")
        
        # 创建单列索引
        self.create_index("users", ["username"], "idx_username")
        self.create_index("users", ["registration_date"], "idx_registration_date")
        self.create_index("users", ["credit_score"], "idx_credit_score")
        self.create_index("products", ["category"], "idx_category")
        
        # 存储测试结果
        self.results['single_column_indexes'] = []
        
        # 测试用例1：按用户名查询
        query = "SELECT * FROM users FORCE INDEX (idx_username) WHERE username = %s"
        # 随机选择一个存在的用户名
        self.cursor.execute("SELECT username FROM users ORDER BY RAND() LIMIT 1")
        random_username = self.cursor.fetchone()['username']
        
        result = self.run_test_case(
            name="按用户名查询（单列索引）",
            query=query,
            params=(random_username,)
        )
        self.results['single_column_indexes'].append(result)
        
        # 测试用例2：按用户注册日期范围查询
        query = """
        SELECT * FROM users FORCE INDEX (idx_registration_date)
        WHERE registration_date BETWEEN %s AND %s
        """
        # 选择一个日期范围
        now = datetime.now()
        start_date = now - timedelta(days=random.randint(365, 730))
        end_date = now - timedelta(days=random.randint(0, 300))
        
        result = self.run_test_case(
            name="按用户注册日期范围查询（单列索引）",
            query=query,
            params=(start_date, end_date)
        )
        self.results['single_column_indexes'].append(result)
        
        # 测试用例3：用户订单联表查询
        query = """
        SELECT u.username, o.order_date, o.total_price
        FROM users u FORCE INDEX (idx_credit_score)
        JOIN orders o ON u.id = o.user_id
        WHERE u.credit_score > %s
        LIMIT 1000
        """
        
        result = self.run_test_case(
            name="用户订单联表查询（单列索引）",
            query=query,
            params=(700,)
        )
        self.results['single_column_indexes'].append(result)
        
        # 测试用例4：按产品类别统计订单
        query = """
        SELECT p.category, COUNT(*) as order_count, SUM(o.total_price) as total_sales
        FROM products p FORCE INDEX (idx_category)
        JOIN orders o ON p.id = o.product_id
        GROUP BY p.category
        """
        
        result = self.run_test_case(
            name="按产品类别统计订单（单列索引）",
            query=query
        )
        self.results['single_column_indexes'].append(result)
        
    def test_multi_column_indexes(self):
        """测试多列（联合）索引"""
        print("\n==================== 测试多列（联合）索引 ====================")
        
        # 删除所有非主键索引
        self.drop_all_indexes("users")
        self.drop_all_indexes("products")
        self.drop_all_indexes("orders")
        
        # 创建联合索引
        self.create_index("users", ["username", "credit_score"], "idx_username_credit_score")
        self.create_index("users", ["registration_date", "status"], "idx_registration_date_status")
        self.create_index("orders", ["user_id", "product_id"], "idx_user_id_product_id")
        self.create_index("products", ["category", "price"], "idx_category_price")
        
        # 存储测试结果
        self.results['multi_column_indexes'] = []
        
        # 测试用例1：按用户名和信用分查询
        query = "SELECT * FROM users FORCE INDEX (idx_username_credit_score) WHERE username = %s AND credit_score > %s"
        # 随机选择一个存在的用户名
        self.cursor.execute("SELECT username FROM users ORDER BY RAND() LIMIT 1")
        random_username = self.cursor.fetchone()['username']
        
        result = self.run_test_case(
            name="按用户名和信用分查询（联合索引）",
            query=query,
            params=(random_username, 500)
        )
        self.results['multi_column_indexes'].append(result)
        
        # 测试用例2：按用户注册日期和状态查询
        query = """
        SELECT * FROM users FORCE INDEX (idx_registration_date_status)
        WHERE registration_date BETWEEN %s AND %s
        AND status = %s
        """
        # 选择一个日期范围
        now = datetime.now()
        start_date = now - timedelta(days=random.randint(365, 730))
        end_date = now - timedelta(days=random.randint(0, 300))
        
        result = self.run_test_case(
            name="按用户注册日期和状态查询（联合索引）",
            query=query,
            params=(start_date, end_date, 'active')
        )
        self.results['multi_column_indexes'].append(result)
        
        # 测试用例3：用户订单联表查询（使用联合索引）
        query = """
        SELECT u.username, o.order_date, o.total_price
        FROM users u
        JOIN orders o FORCE INDEX (idx_user_id_product_id) ON u.id = o.user_id AND o.product_id = %s
        WHERE u.credit_score > %s
        LIMIT 1000
        """
        # 随机选择一个存在的产品ID
        self.cursor.execute("SELECT id FROM products ORDER BY RAND() LIMIT 1")
        random_product_id = self.cursor.fetchone()['id']
        
        result = self.run_test_case(
            name="用户订单联表查询（联合索引）",
            query=query,
            params=(random_product_id, 700)
        )
        self.results['multi_column_indexes'].append(result)
        
        # 测试用例4：按产品类别和价格范围统计订单
        query = """
        SELECT p.category, COUNT(*) as order_count, SUM(o.total_price) as total_sales
        FROM products p FORCE INDEX (idx_category_price)
        JOIN orders o ON p.id = o.product_id
        WHERE p.category = %s AND p.price BETWEEN %s AND %s
        GROUP BY p.category
        """
        # 随机选择一个产品类别
        self.cursor.execute("SELECT DISTINCT category FROM products ORDER BY RAND() LIMIT 1")
        random_category = self.cursor.fetchone()['category']
        
        result = self.run_test_case(
            name="按产品类别和价格范围统计订单（联合索引）",
            query=query,
            params=(random_category, 100, 5000)
        )
        self.results['multi_column_indexes'].append(result)
        
    def visualize_results(self, timestamp):
        """可视化测试结果"""
        print("\n生成测试结果可视化...")
        
        # 准备数据
        categories = []
        no_index_times = []
        single_index_times = []
        multi_index_times = []
        
        # 按测试用例名称匹配结果
        for no_idx_test in self.results.get('no_indexes', []):
            test_name = no_idx_test['name']
            base_name = test_name.split('（')[0]  # 提取基本名称
            
            # 查找对应的单列索引和多列索引测试结果
            single_idx_test = next((t for t in self.results.get('single_column_indexes', []) 
                                   if t['name'].startswith(base_name)), None)
            multi_idx_test = next((t for t in self.results.get('multi_column_indexes', []) 
                                  if t['name'].startswith(base_name)), None)
            
            if single_idx_test and multi_idx_test:
                categories.append(base_name)
                no_index_times.append(no_idx_test['avg_time'])
                single_index_times.append(single_idx_test['avg_time'])
                multi_index_times.append(multi_idx_test['avg_time'])
        
        # 创建柱状图
        fig, ax = plt.subplots(figsize=(12, 8))
        
        x = range(len(categories))
        width = 0.25
        
        ax.bar([i - width for i in x], no_index_times, width, label='无索引')
        ax.bar(x, single_index_times, width, label='单列索引')
        ax.bar([i + width for i in x], multi_index_times, width, label='联合索引')
        
        ax.set_ylabel('平均查询时间（秒）')
        ax.set_title('不同索引策略下的查询性能对比')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        
        # 保存图表
        chart_file = os.path.join(VISUALIZATION_DIR, f"index_performance_comparison_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(chart_file)
        print(f"图表已保存到: {chart_file}")
        
        # 计算性能提升百分比
        improvements = []
        
        for i in range(len(categories)):
            no_idx_time = no_index_times[i]
            single_idx_time = single_index_times[i]
            multi_idx_time = multi_index_times[i]
            
            single_improvement = (no_idx_time - single_idx_time) / no_idx_time * 100
            multi_improvement = (no_idx_time - multi_idx_time) / no_idx_time * 100
            
            improvements.append({
                'test_case': categories[i],
                'single_column_improvement': single_improvement,
                'multi_column_improvement': multi_improvement
            })
        
        # 创建性能提升百分比图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        single_improvements = [imp['single_column_improvement'] for imp in improvements]
        multi_improvements = [imp['multi_column_improvement'] for imp in improvements]
        
        ax.bar([i - width/2 for i in x], single_improvements, width, label='单列索引')
        ax.bar([i + width/2 for i in x], multi_improvements, width, label='联合索引')
        
        ax.set_ylabel('性能提升百分比（%）')
        ax.set_title('不同索引策略的性能提升百分比（相对于无索引）')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        
        # 保存图表
        improvement_file = os.path.join(VISUALIZATION_DIR, f"index_improvement_percentage_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(improvement_file)
        print(f"性能提升百分比图表已保存到: {improvement_file}")
        
        # 计算平均提升百分比
        avg_single_improvement = sum(single_improvements) / len(single_improvements)
        avg_multi_improvement = sum(multi_improvements) / len(multi_improvements)
        
        print(f"\n单列索引平均性能提升: {avg_single_improvement:.2f}%")
        print(f"联合索引平均性能提升: {avg_multi_improvement:.2f}%")
        
        # 保存提升数据
        improvement_data = {
            'improvements': improvements,
            'avg_single_improvement': avg_single_improvement,
            'avg_multi_improvement': avg_multi_improvement
        }
        
        improvement_data_file = os.path.join(RESULT_DIR, f"index_improvement_data_{timestamp}.json")
        with open(improvement_data_file, 'w', encoding='utf-8') as f:
            json.dump(improvement_data, f, ensure_ascii=False, indent=2)

def main():
    """主函数"""
    print("========== MySQL索引测试 - 索引测试框架 ==========")
    
    tester = IndexTester()
    
    try:
        # 运行索引测试
        tester.run_index_tests()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试时出错: {e}")
    finally:
        # 关闭数据库连接
        tester.close_connection()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL索引测试 - 数据可视化
生成索引性能对比的可视化图表和报告
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.font_manager as fm
import seaborn as sns
from datetime import datetime

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei', 'SimSun', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['font.family'] = 'sans-serif'

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RESULT_DIR = os.path.join(PROJECT_DIR, "data")  # 结果数据目录
VISUALIZATION_DIR = os.path.join(PROJECT_DIR, "visualization")  # 可视化结果保存目录

# 确保结果目录存在
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(VISUALIZATION_DIR, exist_ok=True)

class IndexPerformanceVisualizer:
    """索引性能可视化类"""
    
    def __init__(self, result_file=None):
        """初始化"""
        self.result_file = result_file
        self.data = None
        self.improvement_data = None
        
    def load_data(self, result_file=None):
        """加载测试结果数据"""
        if result_file:
            self.result_file = result_file
            
        if not self.result_file:
            raise ValueError("未指定结果文件")
            
        print(f"加载测试结果数据: {self.result_file}")
        
        with open(self.result_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        print("数据加载完成")
        return self.data
    
    def load_improvement_data(self, improvement_file):
        """加载改进数据"""
        print(f"加载性能改进数据: {improvement_file}")
        
        with open(improvement_file, 'r', encoding='utf-8') as f:
            self.improvement_data = json.load(f)
            
        print("改进数据加载完成")
        return self.improvement_data
    
    def generate_visualizations(self, output_dir=None):
        """生成各种可视化图表"""
        if not self.data:
            print("没有数据，请先调用load_data()")
            return
            
        output_dir = output_dir or VISUALIZATION_DIR
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成各种图表
        self._create_query_time_comparison(output_dir, timestamp)
        self._create_query_time_bar_chart(output_dir, timestamp)
        self._create_improvement_percentage_chart(output_dir, timestamp)
        
        if self.improvement_data:
            self._create_improvement_heatmap(output_dir, timestamp)
            
        print(f"可视化图表已保存到: {output_dir}")
    
    def _create_query_time_comparison(self, output_dir, timestamp):
        """创建查询时间对比图"""
        # 准备数据
        categories = []
        no_index_times = []
        single_index_times = []
        multi_index_times = []
        
        # 从每个测试类型中提取测试用例
        no_indexes = self.data.get('no_indexes', [])
        single_column_indexes = self.data.get('single_column_indexes', [])
        multi_column_indexes = self.data.get('multi_column_indexes', [])
        
        # 匹配相同的测试用例
        for no_idx_test in no_indexes:
            test_name = no_idx_test['name']
            base_name = test_name.split('（')[0]  # 提取基本名称
            
            # 查找对应的单列索引和多列索引测试结果
            single_idx_test = next((t for t in single_column_indexes 
                                   if t['name'].startswith(base_name)), None)
            multi_idx_test = next((t for t in multi_column_indexes 
                                  if t['name'].startswith(base_name)), None)
            
            if single_idx_test and multi_idx_test:
                categories.append(base_name)
                no_index_times.append(no_idx_test['avg_time'])
                single_index_times.append(single_idx_test['avg_time'])
                multi_index_times.append(multi_idx_test['avg_time'])
        
        # 创建折线图
        plt.figure(figsize=(12, 8))
        
        x = range(len(categories))
        
        plt.plot(x, no_index_times, 'o-', linewidth=2, label='无索引', markersize=8)
        plt.plot(x, single_index_times, 's-', linewidth=2, label='单列索引', markersize=8)
        plt.plot(x, multi_index_times, '^-', linewidth=2, label='联合索引', markersize=8)
        
        plt.ylabel('平均查询时间（秒）', fontsize=14)
        plt.title('不同索引策略下的查询性能对比', fontsize=16)
        plt.xticks(x, categories, rotation=45, ha='right', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # 在每个点上标注具体的时间值
        for i, v in enumerate(no_index_times):
            plt.text(i, v+0.01, f'{v:.4f}s', ha='center', va='bottom')
        
        for i, v in enumerate(single_index_times):
            plt.text(i, v+0.01, f'{v:.4f}s', ha='center', va='bottom')
            
        for i, v in enumerate(multi_index_times):
            plt.text(i, v+0.01, f'{v:.4f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"query_time_line_{timestamp}.png"), dpi=300)
        plt.close()
    
    def _create_query_time_bar_chart(self, output_dir, timestamp):
        """创建查询时间柱状图"""
        # 准备数据
        categories = []
        no_index_times = []
        single_index_times = []
        multi_index_times = []
        
        # 从每个测试类型中提取测试用例
        no_indexes = self.data.get('no_indexes', [])
        single_column_indexes = self.data.get('single_column_indexes', [])
        multi_column_indexes = self.data.get('multi_column_indexes', [])
        
        # 匹配相同的测试用例
        for no_idx_test in no_indexes:
            test_name = no_idx_test['name']
            base_name = test_name.split('（')[0]  # 提取基本名称
            
            # 查找对应的单列索引和多列索引测试结果
            single_idx_test = next((t for t in single_column_indexes 
                                   if t['name'].startswith(base_name)), None)
            multi_idx_test = next((t for t in multi_column_indexes 
                                  if t['name'].startswith(base_name)), None)
            
            if single_idx_test and multi_idx_test:
                categories.append(base_name)
                no_index_times.append(no_idx_test['avg_time'])
                single_index_times.append(single_idx_test['avg_time'])
                multi_index_times.append(multi_idx_test['avg_time'])
        
        # 创建分组柱状图
        fig, ax = plt.subplots(figsize=(14, 8))
        
        x = range(len(categories))
        width = 0.25
        
        # 柱状图
        rects1 = ax.bar([i - width for i in x], no_index_times, width, label='无索引', color='#FF9999')
        rects2 = ax.bar(x, single_index_times, width, label='单列索引', color='#66B2FF')
        rects3 = ax.bar([i + width for i in x], multi_index_times, width, label='联合索引', color='#99FF99')
        
        # 添加标签、标题和图例
        ax.set_ylabel('平均查询时间（秒）', fontsize=14)
        ax.set_title('不同索引策略下的查询性能对比', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=12)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 添加数据标签
        def add_labels(rects):
            for rect in rects:
                height = rect.get_height()
                ax.text(rect.get_x() + rect.get_width()/2., height,
                        f'{height:.4f}s',
                        ha='center', va='bottom', fontsize=9)
        
        add_labels(rects1)
        add_labels(rects2)
        add_labels(rects3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"query_time_bar_{timestamp}.png"), dpi=300)
        plt.close()
    
    def _create_improvement_percentage_chart(self, output_dir, timestamp):
        """创建性能提升百分比图表"""
        # 准备数据
        categories = []
        no_index_times = []
        single_index_times = []
        multi_index_times = []
        
        # 从每个测试类型中提取测试用例
        no_indexes = self.data.get('no_indexes', [])
        single_column_indexes = self.data.get('single_column_indexes', [])
        multi_column_indexes = self.data.get('multi_column_indexes', [])
        
        # 匹配相同的测试用例
        for no_idx_test in no_indexes:
            test_name = no_idx_test['name']
            base_name = test_name.split('（')[0]  # 提取基本名称
            
            # 查找对应的单列索引和多列索引测试结果
            single_idx_test = next((t for t in single_column_indexes 
                                   if t['name'].startswith(base_name)), None)
            multi_idx_test = next((t for t in multi_column_indexes 
                                  if t['name'].startswith(base_name)), None)
            
            if single_idx_test and multi_idx_test:
                categories.append(base_name)
                no_index_times.append(no_idx_test['avg_time'])
                single_index_times.append(single_idx_test['avg_time'])
                multi_index_times.append(multi_idx_test['avg_time'])
                
        # 计算性能提升百分比
        single_improvements = [(no_time - single_time) / no_time * 100 
                              for no_time, single_time in zip(no_index_times, single_index_times)]
        multi_improvements = [(no_time - multi_time) / no_time * 100 
                             for no_time, multi_time in zip(no_index_times, multi_index_times)]
        
        # 创建水平条形图
        plt.figure(figsize=(12, 10))
        
        y_pos = range(len(categories))
        
        plt.barh(y_pos, single_improvements, 0.4, alpha=0.8, label='单列索引', color='#66B2FF')
        
        # 使用不同的y位置，这样两个条不会重叠
        adjusted_y_pos = [y + 0.4 for y in y_pos]
        plt.barh(adjusted_y_pos, multi_improvements, 0.4, alpha=0.8, label='联合索引', color='#99FF99')
        
        # 添加网格线
        plt.grid(True, alpha=0.3, axis='x')
        
        # 设置坐标轴标签和标题
        plt.xlabel('性能提升百分比 (%)', fontsize=14)
        plt.title('不同索引策略的性能提升百分比', fontsize=16)
        
        # 设置y轴刻度和标签
        # 我们使用y_pos和categories来设置刻度和标签
        # 但需要调整y_pos，使其处于两个条的中间
        middle_y_pos = [y + 0.2 for y in y_pos]
        plt.yticks(middle_y_pos, categories, fontsize=12)
        
        # 添加数据标签
        for i, v in enumerate(single_improvements):
            plt.text(v + 1, y_pos[i], f'{v:.2f}%', va='center', fontsize=10)
            
        for i, v in enumerate(multi_improvements):
            plt.text(v + 1, adjusted_y_pos[i], f'{v:.2f}%', va='center', fontsize=10)
        
        # 添加图例
        plt.legend(fontsize=12)
        
        # 计算平均提升
        avg_single = sum(single_improvements) / len(single_improvements)
        avg_multi = sum(multi_improvements) / len(multi_improvements)
        
        # 添加平均提升标注
        plt.axvline(x=avg_single, color='#66B2FF', linestyle='--', alpha=0.7)
        plt.axvline(x=avg_multi, color='#99FF99', linestyle='--', alpha=0.7)
        
        plt.text(avg_single + 1, len(categories) - 1, f'平均提升: {avg_single:.2f}%', 
                color='#66B2FF', fontsize=12, va='center')
        plt.text(avg_multi + 1, len(categories) - 0.5, f'平均提升: {avg_multi:.2f}%', 
                color='#99FF99', fontsize=12, va='center')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"improvement_percentage_{timestamp}.png"), dpi=300)
        plt.close()
    
    def _create_improvement_heatmap(self, output_dir, timestamp):
        """创建性能提升热图"""
        if not self.improvement_data:
            return
            
        # 提取改进数据
        improvements = self.improvement_data.get('improvements', [])
        
        if not improvements:
            return
            
        # 准备热图数据
        test_cases = [imp['test_case'] for imp in improvements]
        single_improvements = [imp['single_column_improvement'] for imp in improvements]
        multi_improvements = [imp['multi_column_improvement'] for imp in improvements]
        
        # 创建数据框
        df = pd.DataFrame({
            'test_case': test_cases,
            'single_column': single_improvements,
            'multi_column': multi_improvements
        })
        
        # 数据透视为适合热图的格式
        pivot_df = df.set_index('test_case').T
        
        # 绘制热图
        plt.figure(figsize=(14, 6))
        ax = sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap="YlGnBu", linewidths=.5,
                        cbar_kws={'label': '性能提升百分比 (%)'})
        
        plt.title('索引策略对不同查询的性能提升热图', fontsize=16)
        plt.ylabel('索引策略', fontsize=14)
        plt.xlabel('查询类型', fontsize=14)
        
        # 设置Y轴标签
        ax.set_yticklabels(['单列索引', '联合索引'], rotation=0, fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"improvement_heatmap_{timestamp}.png"), dpi=300)
        plt.close()
        
    def generate_summary_report(self, output_file=None):
        """生成总结报告"""
        if not self.data:
            print("没有数据，请先调用load_data()")
            return
            
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(RESULT_DIR, f"index_performance_summary_{timestamp}.txt")
            
        # 准备数据
        categories = []
        no_index_times = []
        single_index_times = []
        multi_index_times = []
        
        # 从每个测试类型中提取测试用例
        no_indexes = self.data.get('no_indexes', [])
        single_column_indexes = self.data.get('single_column_indexes', [])
        multi_column_indexes = self.data.get('multi_column_indexes', [])
        
        # 匹配相同的测试用例
        for no_idx_test in no_indexes:
            test_name = no_idx_test['name']
            base_name = test_name.split('（')[0]  # 提取基本名称
            
            # 查找对应的单列索引和多列索引测试结果
            single_idx_test = next((t for t in single_column_indexes 
                                   if t['name'].startswith(base_name)), None)
            multi_idx_test = next((t for t in multi_column_indexes 
                                  if t['name'].startswith(base_name)), None)
            
            if single_idx_test and multi_idx_test:
                categories.append(base_name)
                no_index_times.append(no_idx_test['avg_time'])
                single_index_times.append(single_idx_test['avg_time'])
                multi_index_times.append(multi_idx_test['avg_time'])
                
        # 计算性能提升百分比
        single_improvements = [(no_time - single_time) / no_time * 100 
                              for no_time, single_time in zip(no_index_times, single_index_times)]
        multi_improvements = [(no_time - multi_time) / no_time * 100 
                             for no_time, multi_time in zip(no_index_times, multi_index_times)]
        
        # 计算平均提升
        avg_single = sum(single_improvements) / len(single_improvements)
        avg_multi = sum(multi_improvements) / len(multi_improvements)
        
        # 生成报告文本
        report = []
        report.append("===============================================================")
        report.append("                MySQL索引性能测试 - 总结报告                    ")
        report.append("===============================================================")
        report.append("")
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("1. 总体性能提升情况")
        report.append("---------------------------------------------------------------")
        report.append(f"单列索引平均性能提升: {avg_single:.2f}%")
        report.append(f"联合索引平均性能提升: {avg_multi:.2f}%")
        report.append("")
        
        # 按性能提升排序的查询类型
        sorted_categories = [x for _, x in sorted(zip(multi_improvements, categories), reverse=True)]
        sorted_single_imp = [x for _, x in sorted(zip(multi_improvements, single_improvements), reverse=True)]
        sorted_multi_imp = sorted(multi_improvements, reverse=True)
        
        report.append("2. 各查询类型的性能提升（按联合索引提升降序排列）")
        report.append("---------------------------------------------------------------")
        for i, category in enumerate(sorted_categories):
            report.append(f"{i+1}. {category}")
            report.append(f"   - 单列索引提升: {sorted_single_imp[i]:.2f}%")
            report.append(f"   - 联合索引提升: {sorted_multi_imp[i]:.2f}%")
            report.append("")
            
        report.append("3. 各查询类型的执行时间对比")
        report.append("---------------------------------------------------------------")
        report.append(f"{'查询类型':<30} {'无索引(秒)':<15} {'单列索引(秒)':<15} {'联合索引(秒)':<15}")
        report.append("-" * 80)
        
        for i, category in enumerate(categories):
            report.append(f"{category:<30} {no_index_times[i]:<15.6f} {single_index_times[i]:<15.6f} {multi_index_times[i]:<15.6f}")
            
        report.append("")
        report.append("4. 索引优化建议")
        report.append("---------------------------------------------------------------")
        report.append("1) 对于简单的等值查询（如按用户名查询），单列索引通常已经足够")
        report.append("2) 对于复杂查询（如联表查询、多条件查询），联合索引通常效果更好")
        report.append("3) 创建索引时应考虑索引选择性和使用频率，避免索引过多")
        report.append("4) 对于频繁连接的表，应在外键上创建索引")
        report.append("5) 针对特定查询场景，可以考虑使用覆盖索引进一步提升性能")
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
            
        print(f"总结报告已保存到: {output_file}")
        
        return output_file


def main():
    """主函数"""
    print("========== MySQL索引测试 - 数据可视化 ==========")
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python visualizer.py <测试结果JSON文件>")
        print("示例: python visualizer.py ../data/index_test_results_20230401_120000.json")
        sys.exit(1)
        
    result_file = sys.argv[1]
    if not os.path.isfile(result_file):
        print(f"错误: 找不到测试结果文件: {result_file}")
        sys.exit(1)
        
    # 查找对应的improvement数据文件
    base_name = os.path.basename(result_file)
    timestamp = base_name.replace("index_test_results_", "").replace(".json", "")
    improvement_file = os.path.join(RESULT_DIR, f"index_improvement_data_{timestamp}.json")
    
    # 创建可视化
    try:
        visualizer = IndexPerformanceVisualizer(result_file)
        
        # 加载测试结果数据
        visualizer.load_data()
        
        # 加载改进数据（如果存在）
        if os.path.isfile(improvement_file):
            visualizer.load_improvement_data(improvement_file)
        
        # 生成可视化图表
        visualizer.generate_visualizations()
        
        # 生成总结报告
        visualizer.generate_summary_report()
        
        print("\n可视化完成！")
        
    except KeyboardInterrupt:
        print("\n可视化被用户中断")
    except Exception as e:
        print(f"\n可视化时出错: {e}")

if __name__ == "__main__":
    main() 
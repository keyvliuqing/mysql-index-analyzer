#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL索引优化分析工具 - 主程序
提供命令行界面，调用各个模块执行相应的功能
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
VISUALIZATION_DIR = os.path.join(PROJECT_DIR, "visualization")
LOGS_DIR = os.path.join(PROJECT_DIR, "logs")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VISUALIZATION_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def print_header():
    """打印程序头部"""
    print("\n" + "=" * 70)
    print("               MySQL索引优化分析工具                ")
    print("=" * 70)

def run_script(script_name, args=None):
    """运行指定的脚本"""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    cmd = [sys.executable, script_path]
    
    if args:
        if isinstance(args, list):
            cmd.extend(args)
        else:
            cmd.append(args)
            
    print(f"\n运行: {' '.join(cmd)}")
    
    # 运行脚本
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                  text=True, bufsize=1, universal_newlines=True)
        
        # 读取并打印输出
        for line in process.stdout:
            print(line, end='')
            
        process.stdout.close()
        return_code = process.wait()
        
        if return_code != 0:
            print(f"脚本执行失败，返回码: {return_code}")
            return False
            
        return True
    except Exception as e:
        print(f"运行脚本时出错: {e}")
        return False

def check_environment():
    """检查环境"""
    print_header()
    print("\n检查环境...")
    return run_script("check_environment.py")

def generate_data(scale_factor=None):
    """生成测试数据"""
    print_header()
    print("\n生成测试数据...")
    
    args = []
    if scale_factor:
        args.append(str(scale_factor))
        
    return run_script("data_generator.py", args)

def run_index_test():
    """运行索引测试"""
    print_header()
    print("\n运行索引测试...")
    return run_script("index_tester.py")

def analyze_log(log_file):
    """分析慢查询日志"""
    print_header()
    print("\n分析慢查询日志...")
    return run_script("log_analyzer.py", log_file)

def visualize_results(result_file):
    """可视化结果"""
    print_header()
    print("\n可视化结果...")
    return run_script("visualizer.py", result_file)

def find_latest_result_file():
    """查找最新的测试结果文件"""
    result_files = [f for f in os.listdir(DATA_DIR) if f.startswith("index_test_results_") and f.endswith(".json")]
    
    if not result_files:
        return None
        
    # 按文件修改时间排序
    result_files.sort(key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)), reverse=True)
    return os.path.join(DATA_DIR, result_files[0])

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="MySQL索引优化分析工具")
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="要执行的命令")
    
    # check命令 - 检查环境
    check_parser = subparsers.add_parser("check", help="检查环境")
    
    # generate命令 - 生成测试数据
    generate_parser = subparsers.add_parser("generate", help="生成测试数据")
    generate_parser.add_argument("--scale", type=float, help="数据量缩放因子（默认为1.0）", default=1.0)
    
    # test命令 - 运行索引测试
    test_parser = subparsers.add_parser("test", help="运行索引测试")
    
    # analyze命令 - 分析慢查询日志
    analyze_parser = subparsers.add_parser("analyze", help="分析慢查询日志")
    analyze_parser.add_argument("log_file", help="慢查询日志文件路径")
    
    # visualize命令 - 可视化结果
    visualize_parser = subparsers.add_parser("visualize", help="可视化结果")
    visualize_parser.add_argument("--result", help="测试结果JSON文件路径（默认使用最新的结果文件）")
    
    # all命令 - 执行完整工作流程
    all_parser = subparsers.add_parser("all", help="执行完整工作流程（生成数据、运行测试、可视化结果）")
    all_parser.add_argument("--scale", type=float, help="数据量缩放因子（默认为0.01）", default=0.01)
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行相应的命令
    if args.command == "check":
        check_environment()
    elif args.command == "generate":
        generate_data(args.scale)
    elif args.command == "test":
        run_index_test()
    elif args.command == "analyze":
        analyze_log(args.log_file)
    elif args.command == "visualize":
        result_file = args.result if args.result else find_latest_result_file()
        if result_file:
            visualize_results(result_file)
        else:
            print("错误: 找不到测试结果文件")
            sys.exit(1)
    elif args.command == "all":
        # 执行完整工作流程
        print_header()
        print("\n开始执行完整工作流程...")
        
        # 记录开始时间
        start_time = time.time()
        
        # 1. 检查环境
        if not check_environment():
            print("环境检查失败，中止工作流程")
            sys.exit(1)
            
        # 2. 生成测试数据
        if not generate_data(args.scale):
            print("生成测试数据失败，中止工作流程")
            sys.exit(1)
            
        # 3. 运行索引测试
        if not run_index_test():
            print("索引测试失败，中止工作流程")
            sys.exit(1)
            
        # 4. 可视化结果
        result_file = find_latest_result_file()
        if result_file:
            if not visualize_results(result_file):
                print("结果可视化失败")
        else:
            print("警告: 找不到测试结果文件，跳过可视化步骤")
            
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "=" * 70)
        print(f"工作流程完成！总用时: {elapsed_time:.2f}秒")
        print("=" * 70)
    else:
        # 如果没有指定命令，显示帮助信息
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1) 
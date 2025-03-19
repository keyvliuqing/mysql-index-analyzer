#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL索引测试 - 清理脚本
删除之前生成的所有数据、索引和图表
"""

import os
import sys
import shutil
import mysql.connector

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # 使用root用户
    'password': '123456',  # root用户密码
    'charset': 'utf8mb4',
    'use_unicode': True,
    'get_warnings': True
}

# 数据库名称
DB_NAME = 'index_analyzer_db'

# 脚本目录和项目目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data")
VISUALIZATION_DIR = os.path.join(PROJECT_DIR, "visualization")

def cleanup_database():
    """清理数据库"""
    print("\n清理数据库...")
    try:
        # 连接MySQL服务器
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除数据库
        print(f"删除数据库: {DB_NAME}")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        conn.commit()
        
        print("数据库清理完成！")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"清理数据库时出错: {e}")
        return False

def cleanup_files():
    """清理文件（数据文件和图表）"""
    print("\n清理文件...")
    
    # 清理数据目录
    if os.path.exists(DATA_DIR):
        print(f"清理数据目录: {DATA_DIR}")
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"已删除: {filename}")
            except Exception as e:
                print(f"删除文件时出错: {e}")
    
    # 清理可视化目录
    if os.path.exists(VISUALIZATION_DIR):
        print(f"清理可视化目录: {VISUALIZATION_DIR}")
        for filename in os.listdir(VISUALIZATION_DIR):
            file_path = os.path.join(VISUALIZATION_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    print(f"已删除: {filename}")
            except Exception as e:
                print(f"删除文件时出错: {e}")
    
    print("文件清理完成！")
    return True

def main():
    """主函数"""
    print("========== MySQL索引测试 - 清理工具 ==========")
    
    # 询问确认
    confirm = input("将删除所有数据、索引和图表！确定要继续吗？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消。")
        return
    
    # 清理数据库
    cleanup_database()
    
    # 清理文件
    cleanup_files()
    
    print("\n清理完成！系统已恢复到初始状态。")

if __name__ == "__main__":
    main() 
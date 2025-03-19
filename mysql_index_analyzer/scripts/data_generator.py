#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MySQL索引测试 - 数据生成器
生成大量测试数据并导入MySQL数据库
"""

import time
import random
import sys
from datetime import datetime, timedelta
import mysql.connector
from faker import Faker

# 初始化Faker
fake = Faker('zh_CN')

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # 使用root用户
    'password': '123456',  # root用户密码
    'charset': 'utf8mb4',
    'use_unicode': True,
    'get_warnings': True
}

# 数据生成配置
DB_NAME = 'index_analyzer_db'
USERS_COUNT = 500000  # 用户表记录数量 (原来的2倍)
ORDERS_COUNT = 1000000  # 订单表记录数量 (原来的2倍)
PRODUCTS_COUNT = 25000  # 产品表记录数量 (原来的2倍)
BATCH_SIZE = 20000  # 批量插入大小 (增大批量以提高性能)

def create_database():
    """创建数据库和测试表"""
    try:
        # 连接MySQL服务器
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建数据库
        print(f"创建数据库: {DB_NAME}")
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # 创建用户表
        print("创建用户表")
        cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            registration_date DATETIME NOT NULL,
            last_login DATETIME NOT NULL,
            status ENUM('active', 'inactive', 'suspended') NOT NULL,
            credit_score INT NOT NULL
        ) ENGINE=InnoDB
        """)
        
        # 创建产品表
        print("创建产品表")
        cursor.execute("""
        CREATE TABLE products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock INT NOT NULL,
            description TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        ) ENGINE=InnoDB
        """)
        
        # 创建订单表
        print("创建订单表")
        cursor.execute("""
        CREATE TABLE orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            order_date DATETIME NOT NULL,
            quantity INT NOT NULL,
            total_price DECIMAL(10, 2) NOT NULL,
            status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        ) ENGINE=InnoDB
        """)
        
        conn.commit()
        print("数据库和表创建成功！")
        
        return conn, cursor
    except Exception as e:
        print(f"创建数据库和表时出错: {e}")
        sys.exit(1)

def generate_users(conn, cursor, count):
    """生成用户数据并插入数据库"""
    print(f"开始生成 {count} 条用户数据...")
    start_time = time.time()
    
    # 准备批量插入
    users_data = []
    sql = """INSERT INTO users 
             (username, email, phone, registration_date, last_login, status, credit_score)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
    status_options = ['active', 'inactive', 'suspended']
    now = datetime.now()
    
    for i in range(1, count + 1):
        # 生成一个随机的注册日期（过去3年内）
        reg_date = now - timedelta(days=random.randint(1, 1095))
        # 生成一个随机的最后登录日期（注册日期之后）
        last_login = reg_date + timedelta(days=random.randint(0, (now - reg_date).days))
        
        user = (
            fake.user_name(),
            fake.email(),
            fake.phone_number(),
            reg_date,
            last_login,
            random.choice(status_options),
            random.randint(300, 850)  # 信用分数范围
        )
        users_data.append(user)
        
        # 批量插入
        if len(users_data) >= BATCH_SIZE or i == count:
            cursor.executemany(sql, users_data)
            conn.commit()
            users_data = []
            # 显示进度
            progress = min(i / count * 100, 100)
            print(f"用户数据生成进度: {progress:.2f}% ({i}/{count})")
    
    elapsed_time = time.time() - start_time
    print(f"用户数据生成完成！耗时: {elapsed_time:.2f}秒")

def generate_products(conn, cursor, count):
    """生成产品数据并插入数据库"""
    print(f"开始生成 {count} 条产品数据...")
    start_time = time.time()
    
    # 准备批量插入
    products_data = []
    sql = """INSERT INTO products 
             (name, category, price, stock, description, created_at, updated_at)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
    categories = [
        '电子产品', '服装鞋帽', '家居用品', '食品饮料', '美妆护肤',
        '母婴用品', '运动户外', '图书音像', '汽车用品', '数码配件'
    ]
    
    now = datetime.now()
    
    for i in range(1, count + 1):
        # 生成一个随机的创建日期（过去2年内）
        created_at = now - timedelta(days=random.randint(1, 730))
        # 生成一个随机的更新日期（创建日期之后）
        updated_at = created_at + timedelta(days=random.randint(0, (now - created_at).days))
        
        product = (
            fake.word() + ' ' + fake.word(),  # 产品名称
            random.choice(categories),  # 类别
            round(random.uniform(10, 9999.99), 2),  # 价格
            random.randint(0, 10000),  # 库存
            fake.paragraph(),  # 描述
            created_at,
            updated_at
        )
        products_data.append(product)
        
        # 批量插入
        if len(products_data) >= BATCH_SIZE or i == count:
            cursor.executemany(sql, products_data)
            conn.commit()
            products_data = []
            # 显示进度
            progress = min(i / count * 100, 100)
            print(f"产品数据生成进度: {progress:.2f}% ({i}/{count})")
    
    elapsed_time = time.time() - start_time
    print(f"产品数据生成完成！耗时: {elapsed_time:.2f}秒")

def generate_orders(conn, cursor, count):
    """生成订单数据并插入数据库"""
    print(f"开始生成 {count} 条订单数据...")
    start_time = time.time()
    
    # 获取用户ID范围
    cursor.execute("SELECT MIN(id), MAX(id) FROM users")
    user_min_id, user_max_id = cursor.fetchone()
    
    # 获取产品ID范围和价格
    cursor.execute("SELECT id, price FROM products")
    products = {row[0]: row[1] for row in cursor.fetchall()}
    product_ids = list(products.keys())
    
    # 准备批量插入
    orders_data = []
    sql = """INSERT INTO orders 
             (user_id, product_id, order_date, quantity, total_price, status, payment_method)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    
    status_options = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    payment_methods = ['信用卡', '借记卡', '支付宝', '微信支付', '现金', '银行转账']
    now = datetime.now()
    
    for i in range(1, count + 1):
        # 随机用户ID
        user_id = random.randint(user_min_id, user_max_id)
        # 随机产品ID
        product_id = random.choice(product_ids)
        # 获取产品价格 (从缓存中获取)
        price = products[product_id]
        
        # 随机数量
        quantity = random.randint(1, 10)
        # 计算总价
        total_price = round(price * quantity, 2)
        
        # 随机订单日期（过去1年内）
        order_date = now - timedelta(days=random.randint(0, 365))
        
        order = (
            user_id,
            product_id,
            order_date,
            quantity,
            total_price,
            random.choice(status_options),
            random.choice(payment_methods)
        )
        orders_data.append(order)
        
        # 批量插入
        if len(orders_data) >= BATCH_SIZE or i == count:
            cursor.executemany(sql, orders_data)
            conn.commit()
            orders_data = []
            # 显示进度
            progress = min(i / count * 100, 100)
            print(f"订单数据生成进度: {progress:.2f}% ({i}/{count})")
    
    elapsed_time = time.time() - start_time
    print(f"订单数据生成完成！耗时: {elapsed_time:.2f}秒")

def add_indexes(conn, cursor):
    """为表添加索引以提高查询性能"""
    print("\n添加索引...")
    start_time = time.time()
    
    try:
        # 为用户表添加索引
        print("为用户表添加索引...")
        cursor.execute("CREATE INDEX idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX idx_users_status ON users(status)")
        cursor.execute("CREATE INDEX idx_users_registration ON users(registration_date)")
        
        # 为产品表添加索引
        print("为产品表添加索引...")
        cursor.execute("CREATE INDEX idx_products_name ON products(name)")
        cursor.execute("CREATE INDEX idx_products_category ON products(category)")
        cursor.execute("CREATE INDEX idx_products_price ON products(price)")
        
        # 为订单表添加索引
        print("为订单表添加索引...")
        cursor.execute("CREATE INDEX idx_orders_date ON orders(order_date)")
        cursor.execute("CREATE INDEX idx_orders_status ON orders(status)")
        cursor.execute("CREATE INDEX idx_orders_user_product ON orders(user_id, product_id)")
        
        conn.commit()
        elapsed_time = time.time() - start_time
        print(f"索引添加完成！耗时: {elapsed_time:.2f}秒")
    except Exception as e:
        print(f"添加索引时出错: {e}")

def main():
    """主函数"""
    total_start_time = time.time()
    
    print("========== MySQL索引测试 - 数据生成器 ==========")
    
    # 根据命令行参数调整数据量
    global USERS_COUNT, ORDERS_COUNT, PRODUCTS_COUNT
    create_indexes = True
    
    if len(sys.argv) > 1:
        try:
            if sys.argv[1].lower() == "noindex":
                create_indexes = False
                print("将不创建索引")
            else:
                scale_factor = float(sys.argv[1])
                USERS_COUNT = int(USERS_COUNT * scale_factor)
                ORDERS_COUNT = int(ORDERS_COUNT * scale_factor)
                PRODUCTS_COUNT = int(PRODUCTS_COUNT * scale_factor)
                print(f"数据量调整为原来的 {scale_factor} 倍")
                
                if len(sys.argv) > 2 and sys.argv[2].lower() == "noindex":
                    create_indexes = False
                    print("将不创建索引")
        except ValueError:
            print("参数必须是数字，表示数据量的缩放因子，或者是'noindex'表示不创建索引")
            sys.exit(1)
    
    print(f"\n将生成以下数据:")
    print(f"- 用户: {USERS_COUNT:,} 条记录")
    print(f"- 产品: {PRODUCTS_COUNT:,} 条记录")
    print(f"- 订单: {ORDERS_COUNT:,} 条记录")
    print(f"- 总计: {USERS_COUNT + PRODUCTS_COUNT + ORDERS_COUNT:,} 条记录")
    
    # 创建数据库和表
    conn, cursor = create_database()
    
    # 生成数据
    try:
        phase_time = time.time()
        # 生成产品数据
        generate_products(conn, cursor, PRODUCTS_COUNT)
        products_time = time.time() - phase_time
        
        phase_time = time.time()
        # 生成用户数据
        generate_users(conn, cursor, USERS_COUNT)
        users_time = time.time() - phase_time
        
        phase_time = time.time()
        # 生成订单数据
        generate_orders(conn, cursor, ORDERS_COUNT)
        orders_time = time.time() - phase_time
        
        # 添加索引
        indexes_time = 0
        if create_indexes:
            phase_time = time.time()
            add_indexes(conn, cursor)
            indexes_time = time.time() - phase_time
        
        # 完成
        total_elapsed_time = time.time() - total_start_time
        print("\n========== 数据生成完成 ==========")
        print(f"产品数据: {PRODUCTS_COUNT:,}条 - 耗时: {products_time:.2f}秒")
        print(f"用户数据: {USERS_COUNT:,}条 - 耗时: {users_time:.2f}秒")
        print(f"订单数据: {ORDERS_COUNT:,}条 - 耗时: {orders_time:.2f}秒")
        if create_indexes:
            print(f"创建索引 - 耗时: {indexes_time:.2f}秒")
        print(f"总记录数: {USERS_COUNT + PRODUCTS_COUNT + ORDERS_COUNT:,}条")
        print(f"总耗时: {total_elapsed_time:.2f}秒")
        
    except Exception as e:
        print(f"生成数据时出错: {e}")
    finally:
        # 关闭连接
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("数据库连接已关闭")

if __name__ == "__main__":
    main() 
import sys
import importlib.util

# 检查必要库是否已安装
required_libraries = [
    'mysql.connector',
    'pandas',
    'numpy',
    'matplotlib',
    'sqlparse',
    'pymysql',
    'faker'
]

print("Python版本:", sys.version)
print("\n检查必要的库:")

missing_libraries = []
for lib in required_libraries:
    try:
        if '.' in lib:
            # 处理子模块导入，如mysql.connector
            main_lib = lib.split('.')[0]
            spec = importlib.util.find_spec(main_lib)
        else:
            spec = importlib.util.find_spec(lib)
        
        if spec is None:
            print(f"- {lib} - 未安装")
            missing_libraries.append(lib)
        else:
            print(f"+ {lib} - 已安装")
    except ImportError:
        print(f"- {lib} - 未安装")
        missing_libraries.append(lib)

if missing_libraries:
    print("\n缺少以下库，请安装:")
    for lib in missing_libraries:
        print(f"pip install {lib}")
else:
    print("\n所有必要的库都已安装！")

# 尝试连接MySQL
print("\n尝试连接MySQL:")
try:
    import mysql.connector
    # 替换为您的MySQL连接信息
    conn = mysql.connector.connect(
        host="localhost",
        user="root",  # 使用root用户
        password="123456",  # root用户密码
        # database=""  # 如果需要连接特定数据库，请取消注释并填写
    )
    
    if conn.is_connected():
        db_info = conn.get_server_info()
        print(f"+ 成功连接到MySQL服务器（版本: {db_info}）")
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        record = cursor.fetchone()
        print(f"数据库版本: {record[0]}")
        cursor.close()
        conn.close()
        print("MySQL连接已关闭")
except Exception as e:
    print(f"- 连接MySQL时出错: {e}")
    print("请确保MySQL服务正在运行，并检查连接信息是否正确") 
import re
import os
import sys
import json
from datetime import datetime

class SimpleSlowQueryLogParser:
    """简单的慢查询日志解析器，不需要连接MySQL"""
    
    def __init__(self, log_file=None):
        """初始化解析器"""
        self.log_file = log_file
        self.queries = []
        
    def parse_log_file(self, log_file=None):
        """解析慢查询日志文件"""
        if log_file:
            self.log_file = log_file
            
        if not self.log_file:
            raise ValueError("未指定慢查询日志文件")
            
        print(f"开始解析慢查询日志文件: {self.log_file}")
        
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
                match = re.search(r"# Time: (\S+)", line)
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
    
    def save_to_json(self, output_file):
        """保存查询信息到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.queries, f, ensure_ascii=False, indent=2)
        print(f"查询信息已保存到: {output_file}")
    
    def get_simple_analysis(self):
        """获取简单分析结果"""
        if not self.queries:
            return None
            
        # 按查询时间排序
        sorted_queries = sorted(self.queries, key=lambda x: x.get('query_time', 0), reverse=True)
        
        # 计算平均查询时间
        avg_query_time = sum(q.get('query_time', 0) for q in self.queries) / len(self.queries)
        
        # 计算平均锁定时间
        avg_lock_time = sum(q.get('lock_time', 0) for q in self.queries) / len(self.queries)
        
        # 计算总检查行数
        total_rows_examined = sum(q.get('rows_examined', 0) for q in self.queries)
        
        # 计算总返回行数
        total_rows_sent = sum(q.get('rows_sent', 0) for q in self.queries)
        
        # 分析
        analysis = {
            "总查询数": len(self.queries),
            "平均查询时间(秒)": avg_query_time,
            "平均锁定时间(秒)": avg_lock_time,
            "总检查行数": total_rows_examined,
            "总返回行数": total_rows_sent,
            "最慢的5个查询": [{
                "查询时间(秒)": q.get('query_time'),
                "检查行数": q.get('rows_examined'),
                "返回行数": q.get('rows_sent'),
                "效率比(返回/检查)": round(q.get('rows_sent', 0) / q.get('rows_examined', 1), 4),
                "查询": q.get('query')[:100] + '...' if len(q.get('query', '')) > 100 else q.get('query')
            } for q in sorted_queries[:5]]
        }
        
        return analysis

def main():
    """主函数"""
    print("========== MySQL慢查询日志简单解析器 ==========")
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python parse_slow_log.py <慢查询日志文件路径>")
        print("示例: python parse_slow_log.py example-slow-query.log")
        sys.exit(1)
        
    log_file = sys.argv[1]
    if not os.path.isfile(log_file):
        print(f"错误: 找不到慢查询日志文件: {log_file}")
        sys.exit(1)
        
    # 解析慢查询日志
    try:
        parser = SimpleSlowQueryLogParser(log_file)
        queries = parser.parse_log_file()
        
        # 输出查询信息到JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"slow_queries_{timestamp}.json"
        parser.save_to_json(output_file)
        
        # 简单分析
        analysis = parser.get_simple_analysis()
        if analysis:
            print("\n== 简单分析结果 ==")
            for key, value in analysis.items():
                if key != "最慢的5个查询":
                    print(f"{key}: {value}")
            
            print("\n== 最慢的5个查询 ==")
            for i, query in enumerate(analysis["最慢的5个查询"]):
                print(f"\n{i+1}. 查询时间: {query['查询时间(秒)']}秒")
                print(f"   检查行数: {query['检查行数']}, 返回行数: {query['返回行数']}")
                print(f"   效率比(返回/检查): {query['效率比(返回/检查)']}")
                print(f"   查询: {query['查询']}")
        
        print("\n解析完成！结果已保存到文件: " + output_file)
        
    except Exception as e:
        print(f"解析时出错: {e}")

if __name__ == "__main__":
    main() 
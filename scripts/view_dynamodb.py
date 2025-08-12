#!/usr/bin/env python3
"""
DynamoDB 資料檢視工具
"""
import boto3
import json
from boto3.dynamodb.conditions import Key

def view_papers_table():
    """檢視論文表格資料"""
    # 初始化 DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('arxiv-intelligence-dev-papers')
    
    try:
        # 掃描表格
        response = table.scan(Limit=10)
        items = response.get('Items', [])
        
        print(f"=== 論文表格資料 (前10筆) ===")
        print(f"總共找到 {len(items)} 筆資料")
        
        for i, item in enumerate(items, 1):
            print(f"\n第 {i} 筆論文:")
            print(f"  ArXiv ID: {item.get('arxiv_id', 'N/A')}")
            print(f"  標題: {item.get('title', 'N/A')[:100]}...")
            print(f"  分類: {item.get('categories', [])}")
            print(f"  發布日期: {item.get('published_date', 'N/A')}")
            
    except Exception as e:
        print(f"讀取資料時發生錯誤: {e}")

def view_authors_table():
    """檢視作者表格資料"""
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    table = dynamodb.Table('arxiv-intelligence-dev-authors')
    
    try:
        response = table.scan(Limit=5)
        items = response.get('Items', [])
        
        print(f"\n=== 作者表格資料 (前5筆) ===")
        print(f"總共找到 {len(items)} 筆資料")
        
        for i, item in enumerate(items, 1):
            print(f"\n第 {i} 位作者:")
            print(f"  作者 ID: {item.get('author_id', 'N/A')}")
            print(f"  姓名: {item.get('name', 'N/A')}")
            
    except Exception as e:
        print(f"讀取作者資料時發生錯誤: {e}")

def main():
    print("正在檢視 DynamoDB 資料...")
    view_papers_table()
    view_authors_table()
    
    print(f"\n=== 表格統計 ===")
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    
    tables = [
        'arxiv-intelligence-dev-papers',
        'arxiv-intelligence-dev-authors', 
        'arxiv-intelligence-dev-institutions'
    ]
    
    for table_name in tables:
        try:
            table = dynamodb.Table(table_name)
            response = table.scan(Select='COUNT')
            count = response.get('Count', 0)
            print(f"{table_name}: {count} 筆資料")
        except Exception as e:
            print(f"{table_name}: 無法取得統計 ({e})")

if __name__ == "__main__":
    main()
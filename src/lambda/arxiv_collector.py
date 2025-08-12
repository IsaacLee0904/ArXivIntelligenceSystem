import json
import boto3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
from urllib.parse import quote

def lambda_handler(event, context):
    """
    ArXiv Data Collector Lambda Function - 修正版本
    
    收集 ArXiv 論文資料並儲存到 S3
    """
    
    # 環境變數
    data_lake_bucket = os.environ.get('DATA_LAKE_BUCKET')
    papers_table = os.environ.get('PAPERS_TABLE')
    authors_table = os.environ.get('AUTHORS_TABLE')
    
    print(f"Starting ArXiv data collection...")
    print(f"Data Lake Bucket: {data_lake_bucket}")
    print(f"Papers Table: {papers_table}")
    
    # 初始化 AWS 客戶端
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    
    try:
        # 獲取昨天的論文（因為是凌晨 2 點執行）
        yesterday = datetime.now() - timedelta(days=1)
        search_date = yesterday.strftime('%Y%m%d')
        
        print(f"Searching for papers submitted on: {search_date}")
        
        # 搜尋多個熱門領域
        categories = [
            'cs.AI',      # Artificial Intelligence
            'cs.LG',      # Machine Learning  
            'cs.CL',      # Computation and Language
            'cs.CV',      # Computer Vision
            'stat.ML',    # Machine Learning (Statistics)
        ]
        
        all_papers = []
        
        for category in categories:
            print(f"Fetching papers for category: {category}")
            papers = fetch_arxiv_papers(category, search_date)
            all_papers.extend(papers)
            print(f"Found {len(papers)} papers in {category}")
            
        print(f"Total papers collected: {len(all_papers)}")
        
        if all_papers:
            # 儲存原始資料到 S3
            s3_key = f"raw-data/{search_date}/arxiv_papers_{search_date}.json"
            
            # 準備資料
            data_to_store = {
                'collection_date': search_date,
                'collection_timestamp': datetime.now().isoformat(),
                'total_papers': len(all_papers),
                'categories': categories,
                'papers': all_papers
            }
            
            # 上傳到 S3
            s3_client.put_object(
                Bucket=data_lake_bucket,
                Key=s3_key,
                Body=json.dumps(data_to_store, indent=2, ensure_ascii=False),
                ContentType='application/json'
            )
            
            print(f"Successfully uploaded {len(all_papers)} papers to S3: {s3_key}")
            
            # 儲存到 DynamoDB
            papers_table_ref = dynamodb.Table(papers_table)
            authors_table_ref = dynamodb.Table(authors_table)
            
            saved_papers = 0
            saved_authors = 0
            
            for paper in all_papers:
                try:
                    # 儲存論文資料到 papers table
                    paper_item = {
                        'arxiv_id': paper['arxiv_id'],
                        'title': paper['title'],
                        'summary': paper['summary'],
                        'categories': paper['categories'],
                        'published_date': paper['published_date'],
                        'updated_date': paper['updated_date'],
                        'doi': paper.get('doi'),
                        'journal_ref': paper.get('journal_ref'),
                        'pdf_url': paper['pdf_url'],
                        'abs_url': paper['abs_url'],
                        'collection_timestamp': paper['collection_timestamp'],
                        'submit_date': paper['published_date'][:10].replace('-', '')  # YYYYMMDD format for GSI
                    }
                    
                    # 如果有多個分類，使用第一個主要分類
                    if paper['categories']:
                        paper_item['category'] = paper['categories'][0]
                    
                    papers_table_ref.put_item(Item=paper_item)
                    saved_papers += 1
                    
                    # 儲存作者資料到 authors table
                    for author_name in paper['authors']:
                        # 使用作者名稱作為 ID（可能需要更複雜的邏輯來處理重複名稱）
                        author_id = author_name.lower().replace(' ', '_').replace('.', '')
                        
                        try:
                            authors_table_ref.put_item(
                                Item={
                                    'author_id': author_id,
                                    'name': author_name,
                                    'papers': [paper['arxiv_id']],  # 可以擴展為論文列表
                                    'last_updated': datetime.now().isoformat()
                                },
                                ConditionExpression='attribute_not_exists(author_id)'  # 只在不存在時插入
                            )
                            saved_authors += 1
                        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                            # 作者已存在，可以選擇更新或跳過
                            pass
                            
                except Exception as e:
                    print(f"Error saving paper {paper.get('arxiv_id', 'unknown')}: {e}")
                    continue
            
            print(f"Successfully saved {saved_papers} papers and {saved_authors} authors to DynamoDB")
            
        # 如果沒找到昨天的論文，則獲取最近的論文作為備選
        if len(all_papers) == 0:
            print("No papers found for yesterday, fetching recent papers...")
            recent_papers = fetch_recent_papers()
            all_papers.extend(recent_papers)
            
            if recent_papers:
                s3_key = f"raw-data/{search_date}/arxiv_recent_papers_{search_date}.json"
                data_to_store = {
                    'collection_date': search_date,
                    'collection_timestamp': datetime.now().isoformat(),
                    'total_papers': len(recent_papers),
                    'note': 'Recent papers (not date-specific)',
                    'categories': categories,
                    'papers': recent_papers
                }
                
                s3_client.put_object(
                    Bucket=data_lake_bucket,
                    Key=s3_key,
                    Body=json.dumps(data_to_store, indent=2, ensure_ascii=False),
                    ContentType='application/json'
                )
                
                print(f"Uploaded {len(recent_papers)} recent papers to S3: {s3_key}")
                
                # 儲存 recent papers 到 DynamoDB
                papers_table_ref = dynamodb.Table(papers_table)
                authors_table_ref = dynamodb.Table(authors_table)
                
                saved_papers = 0
                saved_authors = 0
                
                for paper in recent_papers:
                    try:
                        # 儲存論文資料到 papers table
                        paper_item = {
                            'arxiv_id': paper['arxiv_id'],
                            'title': paper['title'],
                            'summary': paper['summary'],
                            'categories': paper['categories'],
                            'published_date': paper['published_date'],
                            'updated_date': paper['updated_date'],
                            'doi': paper.get('doi'),
                            'journal_ref': paper.get('journal_ref'),
                            'pdf_url': paper['pdf_url'],
                            'abs_url': paper['abs_url'],
                            'collection_timestamp': paper['collection_timestamp'],
                            'submit_date': paper['published_date'][:10].replace('-', '')  # YYYYMMDD format for GSI
                        }
                        
                        # 如果有多個分類，使用第一個主要分類
                        if paper['categories']:
                            paper_item['category'] = paper['categories'][0]
                        
                        papers_table_ref.put_item(Item=paper_item)
                        saved_papers += 1
                        
                        # 儲存作者資料到 authors table
                        for author_name in paper['authors']:
                            author_id = author_name.lower().replace(' ', '_').replace('.', '')
                            
                            try:
                                authors_table_ref.put_item(
                                    Item={
                                        'author_id': author_id,
                                        'name': author_name,
                                        'papers': [paper['arxiv_id']],
                                        'last_updated': datetime.now().isoformat()
                                    },
                                    ConditionExpression='attribute_not_exists(author_id)'
                                )
                                saved_authors += 1
                            except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                                pass
                                
                    except Exception as e:
                        print(f"Error saving recent paper {paper.get('arxiv_id', 'unknown')}: {e}")
                        continue
                
                print(f"Successfully saved {saved_papers} recent papers and {saved_authors} authors to DynamoDB")
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully collected {len(all_papers)} papers',
                'collection_date': search_date,
                'categories': categories,
                's3_location': f"s3://{data_lake_bucket}/raw-data/{search_date}/",
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in ArXiv collection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def fetch_arxiv_papers(category, date_str, max_results=50):
    """
    從 ArXiv API 獲取指定分類和日期的論文
    使用正確的 ArXiv API 日期格式
    """
    base_url = "http://export.arxiv.org/api/query"
    
    # ArXiv 正確的日期格式: YYYYMMDDTTTT+TO+YYYYMMDDTTTT
    # 搜尋當天 00:00 到 23:59 的論文
    start_time = f"{date_str}0000"  # 00:00
    end_time = f"{date_str}2359"    # 23:59
    
    # 構建搜尋查詢 - 使用正確的格式
    search_query = f"cat:{category} AND submittedDate:[{start_time}+TO+{end_time}]"
    
    params = {
        'search_query': search_query,
        'start': 0,
        'max_results': max_results,
        'sortBy': 'submittedDate',
        'sortOrder': 'descending'
    }
    
    print(f"API Query: {search_query}")
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        
        # 解析 XML 回應
        root = ET.fromstring(response.content)
        
        # ArXiv API 使用 Atom namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        entries = root.findall('atom:entry', ns)
        
        print(f"Found {len(entries)} entries for category {category} on {date_str}")
        
        for entry in entries:
            try:
                paper = parse_arxiv_entry(entry, ns)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"Error parsing entry: {e}")
                continue
                
        return papers
        
    except Exception as e:
        print(f"Error fetching ArXiv papers for {category}: {e}")
        return []

def fetch_recent_papers(max_results=20):
    """
    獲取最近的論文（不限日期）作為備選
    """
    base_url = "http://export.arxiv.org/api/query"
    
    categories = ['cs.AI', 'cs.LG', 'cs.CV']
    all_papers = []
    
    for category in categories:
        params = {
            'search_query': f'cat:{category}',
            'start': 0,
            'max_results': max_results // len(categories),
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                try:
                    paper = parse_arxiv_entry(entry, ns)
                    if paper:
                        all_papers.append(paper)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error fetching recent papers for {category}: {e}")
            continue
    
    return all_papers

def parse_arxiv_entry(entry, ns):
    """
    解析單個 ArXiv 論文條目
    """
    try:
        # 基本資訊
        arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
        title = entry.find('atom:title', ns).text.strip()
        summary = entry.find('atom:summary', ns).text.strip()
        
        # 日期
        published = entry.find('atom:published', ns).text
        updated = entry.find('atom:updated', ns).text
        
        # 作者
        authors = []
        author_elements = entry.findall('atom:author', ns)
        for author in author_elements:
            name_elem = author.find('atom:name', ns)
            if name_elem is not None:
                authors.append(name_elem.text.strip())
        
        # 分類
        categories = []
        category_elements = entry.findall('atom:category', ns)
        for category in category_elements:
            term = category.get('term')
            if term:
                categories.append(term)
        
        # DOI (如果有)
        doi = None
        for link in entry.findall('atom:link', ns):
            if link.get('title') == 'doi':
                doi = link.get('href')
                break
        
        # Journal reference (如果有)
        journal_ref = None
        comment_elem = entry.find('atom:comment', ns)
        if comment_elem is not None:
            journal_ref = comment_elem.text.strip()
        
        paper = {
            'arxiv_id': arxiv_id,
            'title': title,
            'summary': summary,
            'authors': authors,
            'categories': categories,
            'published_date': published,
            'updated_date': updated,
            'doi': doi,
            'journal_ref': journal_ref,
            'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            'abs_url': f"https://arxiv.org/abs/{arxiv_id}",
            'collection_timestamp': datetime.now().isoformat()
        }
        
        return paper
        
    except Exception as e:
        print(f"Error parsing paper entry: {e}")
        return None
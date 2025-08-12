# ArXiv Intelligence System

## 📁 專案結構

```
ArXivIntelligenceSystem/
├── 📋 CLAUDE.md              # 專案指令和設定
├── 📖 README.md              # 專案說明文件
├── ⚙️ setup.sh               # 環境設定腳本
├── 📚 docs/                  # 文件目錄
│   ├── Requirements.md       # 需求文件
│   └── project_architecture.md
├── 🐍 src/                   # 原始碼目錄
│   └── lambda/               # Lambda 函數程式碼
│       ├── arxiv_collector.py    # ArXiv 資料收集器
│       ├── data_processor.py     # 資料處理器
│       ├── lambda_function.py    # 主要 Lambda 函數
│       └── requirements.txt      # Python 依賴套件
├── 🔧 scripts/               # 工具腳本
│   ├── package_lambda.sh     # Lambda 打包腳本
│   └── view_dynamodb.py      # DynamoDB 查看工具
└── 🏗️ terraform/             # 基礎架構即程式碼
    ├── infrastructure.tf     # Terraform 配置
    ├── arxiv_collector.zip   # Lambda 部署包
    └── data_processor.zip    # 資料處理器部署包
```

## 🚀 快速開始

### 1. 打包 Lambda 函數
```bash
./scripts/package_lambda.sh
```

### 2. 部署基礎架構
```bash
cd terraform
terraform init
terraform apply
```

### 3. 檢視 DynamoDB 資料
```bash
python3 scripts/view_dynamodb.py
```
📊 資料處理流程：

  1️⃣ 自動觸發階段 (每日凌晨2點 UTC)

  EventBridge Rule → Lambda Collector
  - EventBridge 規則每天凌晨 2 點自動觸發
  - 觸發 arxiv-intelligence-dev-arxiv-collector Lambda 函數

  2️⃣ 資料收集階段

  Lambda Collector → ArXiv API → S3 (原始資料)
  - Lambda 函數呼叫 ArXiv API 獲取最新論文
  - 原始 JSON 資料儲存到 S3 data-lake bucket
  - 這是原始資料湖的概念

  3️⃣ 資料處理階段

  S3 原始資料 → Lambda Processor → S3 處理後資料 + DynamoDB
  - data-processor Lambda 讀取 S3 的原始資料
  - 進行資料清理、轉換、NLP 處理
  - 處理後的資料存到 S3 processed-data bucket
  - 結構化元數據存到 DynamoDB 表格

  4️⃣ 儲存架構

  - S3 Data Lake: 原始 ArXiv 資料 (JSON/Parquet)
  - S3 Processed: 清理後的資料、向量化結果
  - DynamoDB Papers: 論文元數據 (快速查詢)
  - DynamoDB Authors: 作者資訊
  - DynamoDB Institutions: 機構資料

  🔄 完整流程圖：

  每日 2AM UTC
       ↓
  EventBridge → Lambda Collector → ArXiv API
                      ↓
                  S3 Data Lake (原始資料)
                      ↓
              Lambda Processor (可手動或自動觸發)
                      ↓
           ┌─────────────────────┐
           ↓                     ↓
  S3 Processed Data         DynamoDB Tables
   (清理後資料)              (快速查詢用)
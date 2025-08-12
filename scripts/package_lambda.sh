#!/bin/bash

echo "Packaging ArXiv Collector Lambda function..."

# 進入專案根目錄
cd "$(dirname "$0")/.."

# 創建臨時目錄
mkdir -p terraform/lambda_package
cd terraform/lambda_package

# 安裝 Python 依賴
python3 -m pip install -r ../../src/lambda/requirements.txt --target .

# 複製 Lambda 函數
cp ../../src/lambda/lambda_function.py .

# 創建 ZIP 檔案
zip -r ../arxiv_collector.zip .

# 清理
cd ..
rm -rf lambda_package

echo "Lambda package created: arxiv_collector.zip"
echo "File size: $(ls -lh arxiv_collector.zip | awk '{print $5}')"
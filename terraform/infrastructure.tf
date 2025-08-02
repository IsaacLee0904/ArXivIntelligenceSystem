# ArXiv Intelligence System - 簡化架構
# Lambda-based batch processing without VPC complexity

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "4.67.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "arxiv-intelligence"
}

# Random suffix for unique naming
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Buckets for Data Storage
# 1. 原始數據湖 (Raw Data Lake)
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-${random_string.suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-data-lake"
    Environment = var.environment
    Purpose     = "DataLake"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 自動化生命週期管理 (節省成本)
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "cost_optimization"
    status = "Enabled"

    transition {
      days          = 30   # 30天後移到較便宜的儲存
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90   # 90天後移到 Glacier
      storage_class = "GLACIER"
    }
  }
}

# 2. 處理後數據 (Processed Data)
resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.project_name}-${var.environment}-processed-${random_string.suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-processed-data"
    Environment = var.environment
    Purpose     = "ProcessedData"
  }
}

resource "aws_s3_bucket_versioning" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 3. ML 模型儲存 (ML Models)
resource "aws_s3_bucket" "ml_models" {
  bucket = "${var.project_name}-${var.environment}-models-${random_string.suffix.result}"

  tags = {
    Name        = "${var.project_name}-${var.environment}-ml-models"
    Environment = var.environment
    Purpose     = "MLModels"
  }
}

resource "aws_s3_bucket_versioning" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ml_models" {
  bucket = aws_s3_bucket.ml_models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB Tables - NoSQL 資料庫
# 1. 論文元數據表
resource "aws_dynamodb_table" "papers_metadata" {
  name         = "${var.project_name}-${var.environment}-papers"
  billing_mode = "PAY_PER_REQUEST"  # 按需付費，適合開發環境
  hash_key     = "arxiv_id"

  attribute {
    name = "arxiv_id"
    type = "S"
  }

  attribute {
    name = "category"
    type = "S"
  }

  attribute {
    name = "submit_date"
    type = "S"
  }

  # 全域二級索引 - 按學科和日期查詢
  global_secondary_index {
    name            = "CategoryIndex"
    hash_key        = "category"
    range_key       = "submit_date"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true  # 啟用時間點恢復
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-papers"
    Environment = var.environment
  }
}

# 2. 作者資料表
resource "aws_dynamodb_table" "authors" {
  name         = "${var.project_name}-${var.environment}-authors"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "author_id"

  attribute {
    name = "author_id"
    type = "S"
  }

  attribute {
    name = "name"
    type = "S"
  }

  global_secondary_index {
    name            = "NameIndex"
    hash_key        = "name"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-authors"
    Environment = var.environment
  }
}

# 3. 機構資料表
resource "aws_dynamodb_table" "institutions" {
  name         = "${var.project_name}-${var.environment}-institutions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "institution_id"

  attribute {
    name = "institution_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-institutions"
    Environment = var.environment
  }
}

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

}

# 附加基本執行權限
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Functions for Data Processing Pipeline

# 1. ArXiv Data Collection Lambda
resource "aws_lambda_function" "arxiv_collector" {
  filename         = "arxiv_collector.zip"
  function_name    = "${var.project_name}-${var.environment}-arxiv-collector"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      DATA_LAKE_BUCKET = aws_s3_bucket.data_lake.bucket
      PAPERS_TABLE     = aws_dynamodb_table.papers_metadata.name
      AUTHORS_TABLE    = aws_dynamodb_table.authors.name
    }
  }

}

# 2. Data Processing Lambda
resource "aws_lambda_function" "data_processor" {
  filename         = "data_processor.zip"
  function_name    = "${var.project_name}-${var.environment}-data-processor"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 1024

  environment {
    variables = {
      DATA_LAKE_BUCKET     = aws_s3_bucket.data_lake.bucket
      PROCESSED_DATA_BUCKET = aws_s3_bucket.processed_data.bucket
      PAPERS_TABLE         = aws_dynamodb_table.papers_metadata.name
    }
  }

}

# EventBridge Rules for Scheduled Data Collection
resource "aws_cloudwatch_event_rule" "daily_collection" {
  name                = "${var.project_name}-${var.environment}-daily-collection"
  description         = "Trigger ArXiv data collection daily"
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_collection.name
  target_id = "ArxivCollectorTarget"
  arn       = aws_lambda_function.arxiv_collector.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.arxiv_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_collection.arn
}


# 自定義權限策略
resource "aws_iam_role_policy" "lambda_custom" {
  name = "${var.project_name}-${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*",
          aws_s3_bucket.processed_data.arn,
          "${aws_s3_bucket.processed_data.arn}/*",
          aws_s3_bucket.ml_models.arn,
          "${aws_s3_bucket.ml_models.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.papers_metadata.arn,
          "${aws_dynamodb_table.papers_metadata.arn}/index/*",
          aws_dynamodb_table.authors.arn,
          "${aws_dynamodb_table.authors.arn}/index/*",
          aws_dynamodb_table.institutions.arn,
          "${aws_dynamodb_table.institutions.arn}/index/*"
        ]
      }
    ]
  })
}

# Outputs - 部署完成後顯示的重要資訊
output "deployment_info" {
  description = "Basic deployment information"
  value = {
    region      = var.aws_region
    environment = var.environment
    project     = var.project_name
  }
}


output "storage" {
  description = "Storage resources"
  value = {
    data_lake_bucket     = aws_s3_bucket.data_lake.bucket
    processed_data_bucket = aws_s3_bucket.processed_data.bucket
    ml_models_bucket     = aws_s3_bucket.ml_models.bucket
    papers_table         = aws_dynamodb_table.papers_metadata.name
    authors_table        = aws_dynamodb_table.authors.name
    institutions_table   = aws_dynamodb_table.institutions.name
  }
}

output "lambda_functions" {
  description = "Lambda function resources"
  value = {
    arxiv_collector_arn = aws_lambda_function.arxiv_collector.arn
    data_processor_arn  = aws_lambda_function.data_processor.arn
    collector_name      = aws_lambda_function.arxiv_collector.function_name
    processor_name      = aws_lambda_function.data_processor.function_name
  }
}

output "iam_resources" {
  description = "IAM resources"
  value = {
    lambda_role_arn = aws_iam_role.lambda_execution.arn
    lambda_role_name = aws_iam_role.lambda_execution.name
  }
}

output "schedule" {
  description = "Scheduled execution"
  value = {
    daily_collection_rule = aws_cloudwatch_event_rule.daily_collection.name
    schedule_expression   = aws_cloudwatch_event_rule.daily_collection.schedule_expression
  }
}

output "cost_estimate" {
  description = "Monthly cost estimate (USD) - Simplified Architecture"
  value = "Development: ~$2-8/month, Production: ~$15-50/month (much lower without VPC)"
}
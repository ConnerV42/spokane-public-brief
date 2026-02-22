# Spokane Public Brief — Serverless Infrastructure
# Designed to dogfood Lambdaform's Terraform parsing

terraform {
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.region
}

# --- Variables ---

variable "stage" {
  description = "Deployment stage"
  type        = string
  default     = "dev"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for Claude"
  type        = string
  default     = "anthropic.claude-3-5-sonnet-20241022-v2:0"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

# --- DynamoDB Tables ---

resource "aws_dynamodb_table" "meetings" {
  name         = "spokane-public-brief-meetings-${var.stage}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "meeting_id"

  attribute {
    name = "meeting_id"
    type = "S"
  }

  attribute {
    name = "body_name"
    type = "S"
  }

  attribute {
    name = "meeting_date"
    type = "S"
  }

  attribute {
    name = "_type"
    type = "S"
  }

  global_secondary_index {
    name            = "body-date-index"
    hash_key        = "body_name"
    range_key       = "meeting_date"
    projection_type = "ALL"
  }

  # Enables listing all meetings sorted by date without a scan.
  # All meetings share _type="meeting" as a fixed partition key.
  global_secondary_index {
    name            = "type-date-index"
    hash_key        = "_type"
    range_key       = "meeting_date"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "agenda_items" {
  name         = "spokane-public-brief-agenda-items-${var.stage}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "item_id"

  attribute {
    name = "item_id"
    type = "S"
  }

  attribute {
    name = "meeting_id"
    type = "S"
  }

  attribute {
    name = "_type"
    type = "S"
  }

  attribute {
    name = "meeting_date"
    type = "S"
  }

  attribute {
    name = "topic"
    type = "S"
  }

  global_secondary_index {
    name            = "meeting-index"
    hash_key        = "meeting_id"
    projection_type = "ALL"
  }

  # Enables listing all items sorted by date without a scan.
  # All items share _type="agenda_item" as a fixed partition key.
  global_secondary_index {
    name            = "type-date-index"
    hash_key        = "_type"
    range_key       = "meeting_date"
    projection_type = "ALL"
  }

  # Enables querying items by topic sorted by date.
  global_secondary_index {
    name            = "topic-date-index"
    hash_key        = "topic"
    range_key       = "meeting_date"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "documents" {
  name         = "spokane-public-brief-documents-${var.stage}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "document_id"

  attribute {
    name = "document_id"
    type = "S"
  }
}

# --- SQS Queue (for async ingest jobs) ---

resource "aws_sqs_queue" "ingest_queue" {
  name                       = "spokane-public-brief-ingest-${var.stage}"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
}

resource "aws_sqs_queue" "analysis_queue" {
  name                       = "spokane-public-brief-analysis-${var.stage}"
  visibility_timeout_seconds = 600
  message_retention_seconds  = 86400
}

# --- IAM Role for Lambdas ---

resource "aws_iam_role" "lambda_role" {
  name = "spokane-public-brief-lambda-${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  inline_policy {
    name = "bedrock-invoke"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = ["arn:aws:bedrock:${var.region}::foundation-model/${var.bedrock_model_id}"]
      }]
    })
  }

  inline_policy {
    name = "dynamodb-access"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:DeleteItem"]
        Resource = [
          aws_dynamodb_table.meetings.arn,
          "${aws_dynamodb_table.meetings.arn}/index/*",
          aws_dynamodb_table.agenda_items.arn,
          "${aws_dynamodb_table.agenda_items.arn}/index/*",
          aws_dynamodb_table.documents.arn,
        ]
      }]
    })
  }

  inline_policy {
    name = "sqs-access"
    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.ingest_queue.arn,
          aws_sqs_queue.analysis_queue.arn,
        ]
      }]
    })
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda Functions ---

resource "aws_lambda_function" "api" {
  function_name = "spokane-public-brief-api-${var.stage}"
  runtime       = "python3.12"
  handler       = "lambda_handler.handler"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 30
  memory_size   = 512

  filename = "../dist/api.zip"

  environment {
    variables = {
      STAGE             = var.stage
      BEDROCK_MODEL_ID  = var.bedrock_model_id
      MEETINGS_TABLE    = aws_dynamodb_table.meetings.name
      AGENDA_TABLE      = aws_dynamodb_table.agenda_items.name
      DOCUMENTS_TABLE   = aws_dynamodb_table.documents.name
    }
  }
}

resource "aws_lambda_function" "ingestor" {
  function_name = "spokane-public-brief-ingestor-${var.stage}"
  runtime       = "python3.12"
  handler       = "ingestor_handler.handler"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 300
  memory_size   = 256

  filename = "../dist/ingestor.zip"

  environment {
    variables = {
      STAGE              = var.stage
      MEETINGS_TABLE     = aws_dynamodb_table.meetings.name
      AGENDA_TABLE       = aws_dynamodb_table.agenda_items.name
      DOCUMENTS_TABLE    = aws_dynamodb_table.documents.name
      INGEST_QUEUE_URL   = aws_sqs_queue.ingest_queue.id
      ANALYSIS_QUEUE_URL = aws_sqs_queue.analysis_queue.id
    }
  }
}

resource "aws_lambda_function" "analyzer" {
  function_name = "spokane-public-brief-analyzer-${var.stage}"
  runtime       = "python3.12"
  handler       = "analyzer_handler.handler"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 600
  memory_size   = 512

  filename = "../dist/analyzer.zip"

  environment {
    variables = {
      STAGE            = var.stage
      BEDROCK_MODEL_ID = var.bedrock_model_id
      MEETINGS_TABLE   = aws_dynamodb_table.meetings.name
      AGENDA_TABLE     = aws_dynamodb_table.agenda_items.name
      DOCUMENTS_TABLE  = aws_dynamodb_table.documents.name
    }
  }
}

# --- SQS -> Lambda triggers ---

resource "aws_lambda_event_source_mapping" "analysis_trigger" {
  event_source_arn = aws_sqs_queue.analysis_queue.arn
  function_name    = aws_lambda_function.analyzer.arn
  batch_size       = 1
}

resource "aws_lambda_event_source_mapping" "ingest_trigger" {
  event_source_arn = aws_sqs_queue.ingest_queue.arn
  function_name    = aws_lambda_function.ingestor.arn
  batch_size       = 1
}

# --- Lambda Permissions ---

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}

# --- API Gateway v2 (HTTP API) ---

resource "aws_apigatewayv2_api" "http_api" {
  name          = "spokane-public-brief-${var.stage}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = var.stage
  auto_deploy = true
}

# --- Outputs ---

output "api_url" {
  value = "${aws_apigatewayv2_api.http_api.api_endpoint}/${var.stage}"
}

output "ingest_queue_url" {
  value = aws_sqs_queue.ingest_queue.id
}

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  name        = var.project_name
  account_id  = data.aws_caller_identity.current.account_id
  partition   = data.aws_partition.current.partition
  package     = "${path.module}/../dist/cloudscope-lambda.zip"
  bucket_name = "${local.name}-${local.account_id}-${var.aws_region}-reports"
}

resource "aws_s3_bucket" "reports" {
  bucket        = local.bucket_name
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "reports" {
  bucket                  = aws_s3_bucket.reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "reports" {
  bucket = aws_s3_bucket.reports.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket     = aws_s3_bucket.reports.id
  depends_on = [aws_s3_bucket_versioning.reports]
  rule {
    id     = "expire-reports"
    status = "Enabled"
    filter {
      prefix = "reports/"
    }
    expiration {
      days = 30
    }
    noncurrent_version_expiration {
      noncurrent_days = 7
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
  rule {
    id     = "remove-expired-delete-markers"
    status = "Enabled"
    filter {
      prefix = "reports/"
    }
    expiration {
      expired_object_delete_marker = true
    }
  }
}

resource "aws_s3_bucket_policy" "reports" {
  bucket = aws_s3_bucket.reports.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource  = [aws_s3_bucket.reports.arn, "${aws_s3_bucket.reports.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

resource "aws_sns_topic" "alerts" {
  name = "${local.name}-alerts"
}

resource "aws_sns_topic_policy" "alerts" {
  arn = aws_sns_topic.alerts.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AccountOwner"
        Effect    = "Allow"
        Principal = { AWS = "arn:${local.partition}:iam::${local.account_id}:root" }
        Action    = "sns:*"
        Resource  = aws_sns_topic.alerts.arn
      },
      {
        Sid       = "CloudWatchAlarms"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alerts.arn
        Condition = {
          StringEquals = { "aws:SourceAccount" = local.account_id }
          ArnLike      = { "aws:SourceArn" = "arn:${local.partition}:cloudwatch:${var.aws_region}:${local.account_id}:alarm:${local.name}-*" }
        }
      }
    ]
  })
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sqs_queue" "failures" {
  name                      = "${local.name}-failures"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled    = true
}

resource "aws_iam_role" "scanner" {
  name = "${local.name}-scanner"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "scanner" {
  name              = "/aws/lambda/${local.name}-scanner"
  retention_in_days = 14
}

resource "aws_iam_role_policy" "scanner" {
  name = "${local.name}-scanner"
  role = aws_iam_role.scanner.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadInventory"
        Effect   = "Allow"
        Action   = ["ec2:DescribeInstances", "ec2:DescribeVolumes", "ec2:DescribeAddresses", "ec2:DescribeSecurityGroups"]
        Resource = "*"
        Condition = {
          StringEquals = { "aws:RequestedRegion" = var.scan_regions }
        }
      },
      {
        Sid      = "WriteReports"
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.reports.arn}/reports/*"
      },
      {
        Sid      = "WriteLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.scanner.arn}:*"
      },
      {
        Sid      = "PublishAlerts"
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Sid      = "RecordFailedInvocations"
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.failures.arn
      }
    ]
  })
}

resource "aws_lambda_function" "scanner" {
  function_name    = "${local.name}-scanner"
  role             = aws_iam_role.scanner.arn
  handler          = "cloudscope.handler.handler"
  runtime          = "python3.12"
  architectures    = ["x86_64"]
  filename         = local.package
  source_code_hash = filebase64sha256(local.package)
  timeout          = 300
  memory_size      = 256
  environment {
    variables = {
      REPORT_BUCKET   = aws_s3_bucket.reports.id
      SCAN_REGIONS    = join(",", var.scan_regions)
      REQUIRED_TAGS   = join(",", var.required_tags)
      ALERT_TOPIC_ARN = aws_sns_topic.alerts.arn
    }
  }
  dead_letter_config {
    target_arn = aws_sqs_queue.failures.arn
  }
  depends_on = [aws_iam_role_policy.scanner, aws_s3_bucket_public_access_block.reports,
    aws_s3_bucket_server_side_encryption_configuration.reports, aws_s3_bucket_policy.reports]
}

resource "aws_lambda_function_event_invoke_config" "scanner" {
  function_name                = aws_lambda_function.scanner.function_name
  maximum_event_age_in_seconds  = 3600
  maximum_retry_attempts        = 1
}

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "${local.name}-daily"
  description         = "Scheduled read-only AWS audit"
  schedule_expression = var.schedule_expression
  state               = var.schedule_enabled ? "ENABLED" : "DISABLED"
}

resource "aws_sqs_queue_policy" "events" {
  queue_url = aws_sqs_queue.failures.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.failures.arn
      Condition = {
        ArnEquals    = { "aws:SourceArn" = aws_cloudwatch_event_rule.daily.arn }
        StringEquals = { "aws:SourceAccount" = local.account_id }
      }
    }]
  })
}

resource "aws_lambda_permission" "schedule" {
  statement_id   = "AllowScheduledAudit"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.scanner.function_name
  principal      = "events.amazonaws.com"
  source_arn     = aws_cloudwatch_event_rule.daily.arn
  source_account = local.account_id
}

resource "aws_cloudwatch_event_target" "scanner" {
  rule      = aws_cloudwatch_event_rule.daily.name
  target_id = "scanner"
  arn       = aws_lambda_function.scanner.arn
  dead_letter_config {
    arn = aws_sqs_queue.failures.arn
  }
  retry_policy {
    maximum_event_age_in_seconds = 3600
    maximum_retry_attempts       = 2
  }
  depends_on = [aws_lambda_permission.schedule, aws_sqs_queue_policy.events]
}

resource "aws_cloudwatch_metric_alarm" "errors" {
  alarm_name          = "${local.name}-lambda-errors"
  alarm_description   = "A scheduled or manual invocation failed. Inspect CloudWatch logs and the failure queue."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions          = { FunctionName = aws_lambda_function.scanner.function_name }
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "queued_failures" {
  alarm_name          = "${local.name}-queued-failures"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  dimensions          = { QueueName = aws_sqs_queue.failures.name }
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

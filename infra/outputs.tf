output "report_bucket" {
  value = aws_s3_bucket.reports.id
}

output "function_name" {
  value = aws_lambda_function.scanner.function_name
}

output "failure_queue_url" {
  value = aws_sqs_queue.failures.url
}

output "log_group" {
  value = aws_cloudwatch_log_group.scanner.name
}

output "schedule_enabled" {
  value = var.schedule_enabled
}

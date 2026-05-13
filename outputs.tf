output "lambda_arn" {
  value = aws_lambda_function.daily_notifier.arn
}

output "cloudwatch_rule" {
  value = aws_cloudwatch_event_rule.daily_trigger.name
}

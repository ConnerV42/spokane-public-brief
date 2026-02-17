# EventBridge schedule to trigger ingestor Lambda periodically

variable "ingestor_schedule" {
  description = "EventBridge schedule expression for the ingestor Lambda"
  type        = string
  default     = "rate(6 hours)"
}

resource "aws_cloudwatch_event_rule" "ingestor_schedule" {
  name                = "spokane-public-brief-ingestor-${var.stage}"
  description         = "Triggers the ingestor Lambda on a recurring schedule"
  schedule_expression = var.ingestor_schedule
}

resource "aws_cloudwatch_event_target" "ingestor" {
  rule = aws_cloudwatch_event_rule.ingestor_schedule.name
  arn  = aws_lambda_function.ingestor.arn
}

resource "aws_lambda_permission" "eventbridge_invoke_ingestor" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ingestor_schedule.arn
}

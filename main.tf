resource "aws_lambda_function" "daily_notifier" {
  function_name = "DailyNotifierApp"
  handler = "notifier.lambda_handler"
  runtime = "python3.12"
  role = aws_iam_role.lambda_exec.arn
  timeout = 25
  filename = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")

  environment {
    variables = {
      LOG_TABLE = aws_dynamodb_table.daily_notifier_logs.name

      SES_EMAIL_FROM = var.ses_email_from
      SES_EMAIL_TO = var.ses_email_to

        QUOTE_API_URL = "https://zenquotes.io/api/random"
        # QUOTE_API_URL = "https://dummyjson.com/quotes/random"

    WEATHER_API_URL  = "https://api.open-meteo.com/v1/forecast?latitude=37.77&longitude=-122.42&daily=temperature_2m_max&daily=windspeed_10m_max&timezone=America/Los_Angeles&daily=temperature_2m_min&temperature_unit=fahrenheit"
    
    }
  }
}


resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "daily_notifier_cron"
  schedule_expression = "cron(0 12 * * ? *)" # 12:00 UTC daily
}

resource "aws_cloudwatch_event_target" "daily_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "DailyNotifierLambda"
  arn       = aws_lambda_function.daily_notifier.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.daily_notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}


resource "aws_iam_role" "lambda_exec" {
  name = "daily_notifier_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ses_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}


resource "aws_ses_email_identity" "sender" {
  email = var.ses_email_from
}

resource "aws_dynamodb_table" "daily_notifier_logs" {
  name         = "DailyNotifierLogs"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    App = "DailyNotifier"
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb_access" {
  name = "lambda_dynamodb_access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.daily_notifier_logs.arn
      }
    ]
  })
}

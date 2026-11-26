# Alarm declarations (a deployment that sets one off is rolled back by ECS)
# 5xx answers of the server tasks, counted over the whole load balancer, since either target group may be the live one
resource "aws_cloudwatch_metric_alarm" "target_5xx" {
  alarm_name          = "${local.app_name}-5xx"
  alarm_description   = "The server tasks answered with ${var.alarm_5xx_threshold} or more errors a minute, twice in a row"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 2
  threshold           = var.alarm_5xx_threshold
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.this.arn_suffix
  }
}

# Tasks the load balancer finds unhealthy, one alarm per target group
resource "aws_cloudwatch_metric_alarm" "unhealthy_hosts" {
  for_each = aws_lb_target_group.this

  alarm_name          = "${local.app_name}-${each.key}-unhealthy"
  alarm_description   = "A server task in the ${each.key} target group failed its health check for three minutes"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.this.arn_suffix
    TargetGroup  = each.value.arn_suffix
  }
}

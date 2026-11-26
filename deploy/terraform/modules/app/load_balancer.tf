# Load balancer declaration (internet-facing, lives in the public subnets)
resource "aws_lb" "this" {
  name                       = var.name
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.load_balancer.id]
  subnets                    = var.public_subnet_ids
  enable_deletion_protection = var.load_balancer_deletion_protection
  idle_timeout               = var.load_balancer_idle_timeout
  drop_invalid_header_fields = true

  #checkov:skip=CKV_AWS_91:Access logs need a bucket with a delivery policy, CloudWatch has the request metrics
  #checkov:skip=CKV2_AWS_28:A WAF is billed per rule and request, the server authenticates every request itself
  #checkov:skip=CKV_AWS_150:Deletion protection is a variable, on in staging and prod
}

# Target group declarations (blue and green, the server tasks by the address of their own interface)
# A rolling deployment only ever uses blue; a canary deployment starts the new tasks in the group that serves no traffic
resource "aws_lb_target_group" "this" {
  for_each = toset(["blue", "green"])

  name                 = "${var.name}-${each.key}"
  port                 = var.container_port
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = var.load_balancer_deregistration_delay

  #checkov:skip=CKV_AWS_378:TLS ends at the load balancer, the tasks are reachable only from its security group

  health_check {
    path                = var.load_balancer_health_check_path
    matcher             = "200"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# Listener declarations
# HTTP only redirects, the session cookie is Secure on AWS and a browser sends it over HTTPS only
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS ends at the load balancer. What reaches it is forwarded by the rule below, anything else is answered with 404
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.load_balancer_ssl_policy
  certificate_arn   = aws_acm_certificate_validation.this.certificate_arn

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Not found"
      status_code  = "404"
    }
  }
}

# The production rule forwards everything to both target groups, all of it to blue at first
# A canary deployment moves the weights from one group to the other, so they belong to ECS from then on
resource "aws_lb_listener_rule" "app" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.this["blue"].arn
        weight = 1
      }

      target_group {
        arn    = aws_lb_target_group.this["green"].arn
        weight = 0
      }
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }

  lifecycle {
    ignore_changes = [action]
  }
}

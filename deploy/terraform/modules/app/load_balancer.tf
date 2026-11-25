# Load balancer declaration (internet-facing, lives in the public subnets)
resource "aws_lb" "this" {
  name                       = var.name
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.load_balancer.id]
  subnets                    = var.public_subnet_ids
  enable_deletion_protection = var.load_balancer_deletion_protection
  idle_timeout               = var.load_balancer_idle_timeout
}

# Target group declaration (the server tasks which receive the traffic, by the address of their own interface)
resource "aws_lb_target_group" "this" {
  name                 = local.app_name
  port                 = var.container_port
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = var.vpc_id
  deregistration_delay = var.load_balancer_deregistration_delay

  health_check {
    path = var.load_balancer_health_check_path
  }
}

# Listener declarations
# HTTP only redirects, the session cookie is Secure in production and a browser sends it over HTTPS only
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

# HTTPS ends at the load balancer and forwards the incoming traffic to the target group
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = var.load_balancer_ssl_policy
  certificate_arn   = aws_acm_certificate_validation.this.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

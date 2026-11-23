# Load balancer instance declaration (lives in the public subnets)
resource "aws_lb" "load_balancer" {
  name                       = var.load_balancer_name
  load_balancer_type         = var.load_balancer_type
  security_groups            = [aws_security_group.lb_sg.id]
  subnets                    = aws_subnet.public[*].id
  internal                   = var.load_balancer_internal
  enable_deletion_protection = var.load_balancer_deletion_protection
  idle_timeout               = var.load_balancer_idle_timeout
  tags                       = local.common_tags

  # The internet gateway can only be detached once no public address is left in the VPC, so the load balancer goes first
  depends_on = [aws_internet_gateway.main]
}

# Target group declaration (the server tasks which receive the traffic, by the address of their own interface)
resource "aws_lb_target_group" "web" {
  name                 = var.load_balancer_target_group_name
  port                 = var.app_container_port
  protocol             = var.load_balancer_target_group_protocol
  target_type          = "ip"
  vpc_id               = aws_vpc.main.id
  deregistration_delay = 30

  health_check {
    path = var.load_balancer_health_check_path
  }
}

# Listener declarations
# HTTP only redirects, the session cookie is Secure in production and a browser sends it over HTTPS only
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.load_balancer.arn
  port              = var.load_balancer_listener_port
  protocol          = var.load_balancer_listener_protocol

  default_action {
    type = "redirect"

    redirect {
      port        = tostring(var.load_balancer_https_listener_port)
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS ends at the load balancer and forwards the incoming traffic to the target group
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.load_balancer.arn
  port              = var.load_balancer_https_listener_port
  protocol          = "HTTPS"
  ssl_policy        = var.load_balancer_ssl_policy
  certificate_arn   = aws_acm_certificate_validation.app.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

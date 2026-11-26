output "scheduler_schedule_names" {
  description = "Names of the stop and start schedules"
  value       = [for current in aws_scheduler_schedule.this : current.name]
}

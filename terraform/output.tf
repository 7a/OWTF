output "owtf_url" {
  value       = aws_instance.ec2.public_ip
  description = "This provides Public DNS of the Instance"
}
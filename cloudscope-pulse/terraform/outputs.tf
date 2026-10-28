output "aws_region" {
  value = var.aws_region
}

output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "github_actions_role_arn" {
  value = aws_iam_role.github.arn
}

output "cluster_api_endpoint" {
  value = aws_eks_cluster.this.endpoint
}

output "private_subnets" {
  value = aws_subnet.private[*].id
}

output "operational_warning" {
  value = "BUDGETS ARE ALERT-ONLY. EKS, NAT, EC2, ECR and logs bill until destroyed."
}

variable "project" {
  description = "Short lowercase resource prefix."
  type        = string
  default     = "cloudscope-pulse"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,30}$", var.project))
    error_message = "Use 3-31 lowercase alphanumeric/hyphen characters, starting with a letter."
  }
}

variable "environment" {
  type    = string
  default = "demo"
}

variable "aws_region" {
  description = "EKS-supported region; region affects pricing and capacity."
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.80.0.0/16"
}

variable "eks_version" {
  description = "Keep this version in EKS standard support; see AWS release calendar."
  type        = string
  default     = "1.36"
}

variable "instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "desired_nodes" {
  description = "2 nodes for resilience; 1 can save money for short demos (not HA)."
  type        = number
  default     = 2
  validation {
    condition     = var.desired_nodes >= 1 && var.desired_nodes <= 3
    error_message = "This portfolio intentionally limits desired_nodes to 1-3."
  }
}

variable "public_api_access_cidrs" {
  description = "Explicit trusted public IPv4 /32 or small CIDR ranges for cluster API. Never use 0.0.0.0/0."
  type        = list(string)
  validation {
    condition     = length(var.public_api_access_cidrs) >= 1 && alltrue([for c in var.public_api_access_cidrs : can(cidrhost(c, 0)) && can(regex("/32$", c))])
    error_message = "Supply at least one valid trusted CIDR, and require /32 for each public endpoint CIDR."
  }
}

variable "admin_principal_arn" {
  description = "Persistent IAM user or role ARN granted cluster admin via an EKS access entry; not an STS assumed-role ARN."
  type        = string
  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:(role|user)/", var.admin_principal_arn))
    error_message = "Supply an IAM role/user ARN from this account, not an assumed-role session ARN."
  }
}

variable "github_repository" {
  description = "Exact GitHub owner/repository allowed to push to ECR and update the cloudscope namespace."
  type        = string
  default     = "gargi0806/cloudscope"
  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "Use exact owner/repository format."
  }
}

variable "budget_email" {
  description = "Email to receive account-wide AWS Budget notifications."
  type        = string
  validation {
    condition     = can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.budget_email))
    error_message = "Provide an email address for AWS Budget alerts."
  }
}

variable "monthly_budget_usd" {
  description = "AWS budget is alert-only, not a spending cap."
  type        = number
  default     = 35
  validation {
    condition     = var.monthly_budget_usd >= 5
    error_message = "Enter a budget of at least USD 5."
  }
}

variable "aws_region" {
  description = "Region for Lambda, S3, alerts and the schedule."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "cloudscope"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,19}$", var.project_name))
    error_message = "Use 3–20 lowercase letters, digits or hyphens, starting with a letter."
  }
}

variable "owner" {
  description = "Owner tag for resources created by this project."
  type        = string
  default     = "gargi-verma"
}

variable "scan_regions" {
  description = "One to three enabled AWS regions in the same account; small-account portfolio scope."
  type        = list(string)
  default     = ["ap-south-1"]
  validation {
    condition     = length(var.scan_regions) >= 1 && length(var.scan_regions) <= 3 && alltrue([for r in var.scan_regions : can(regex("^[a-z]{2}-[a-z]+-[0-9]$", r))])
    error_message = "Set one to three standard AWS region identifiers (for example ap-south-1)."
  }
}

variable "required_tags" {
  type    = list(string)
  default = ["Owner", "Environment", "Project"]
  validation {
    condition     = length(var.required_tags) > 0 && alltrue([for t in var.required_tags : length(trimspace(t)) > 0 && !strcontains(t, ",")])
    error_message = "Provide non-empty, comma-free tag names."
  }
}

variable "alert_email" {
  description = "Optional email subscription. Confirm the SNS email before expecting delivery."
  type        = string
  default     = ""
}

variable "schedule_enabled" {
  description = "Enable after a successful manual scan. Disabled by default."
  type        = bool
  default     = false
}

variable "schedule_expression" {
  type    = string
  default = "rate(1 day)"
}

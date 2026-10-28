terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0, < 7.0"
    }
  }
  # Demo defaults to local state. Before any shared/production usage, configure
  # versioned, encrypted, locked remote state (S3 with native locking).
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = local.common_tags
  }
}

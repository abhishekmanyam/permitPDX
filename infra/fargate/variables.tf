variable "region" {
  default = "us-west-2"
}

variable "profile" {
  default = "cd"
}

variable "name" {
  default = "permitpdx"
}

variable "agent_runtime_arn" {
  description = "AgentCore Runtime ARN the backend invokes"
  type        = string
}

# Secrets — set in terraform.tfvars (gitignored).
variable "mapbox_token" {
  type      = string
  sensitive = true
}

variable "liveavatar_api_key" {
  type      = string
  sensitive = true
}

variable "liveavatar_context_id" {
  type    = string
  default = ""
}

variable "liveavatar_llm_config_id" {
  type    = string
  default = ""
}

variable "liveavatar_sandbox_avatar" {
  type    = string
  default = ""
}

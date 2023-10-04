variable "env_name" {
  type = string
  default = "prod"
}

variable "account_number" {
  type = number
}

variable "auth_tokens_table_arn" {
  type = string
}

variable "metrics_table_arn" {
  type = string
}

variable "egg_detector_cache_table_arn" {
  type = string
}

variable "image_uri" {
  type = string
}

variable "enable_functions" {
  type = bool
  default = true
}

variable "enable_monitoring" {
  type = bool
  default = true
}

variable "alarms_email" {
  type = string
}

variable "scraper_configs" {
  type    = map(string)
  default = {
    ecowitt = "rate(5 minutes)"
    yolink = "rate(5 minutes)"
    flume = "cron(30 * * * ? *)"
    enphase = "cron(30 * * * ? *)"
  }
}

variable "s3_bucket_name" {
  type = string
}
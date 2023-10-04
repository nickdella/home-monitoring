variable "timestream_magnetic_retention_days" {
  type    = number
  default = 3650
}

variable "timestream_memory_retention_hours" {
  type    = number
  default = 6
}

variable "enable_delete_protection" {
  type    = bool
  default = true
}

variable "s3_bucket_name" {
  type    = string
}

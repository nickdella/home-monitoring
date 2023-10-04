variable "env_name" {
  type = string
  default = "prod"
}

variable "image_uri" {
  type = string
}

variable "s3_assets_bucket_name" {
  type = string
}

variable "vpc_main_id" {
  type = string
}

variable "public_subnet_id" {
  type = string
}

terraform {
  backend "s3" {
    profile = "default"
    region  = "us-west-2"
    bucket  = "terraform-state-0da3eec8"
    key     = "home-monitoring"
  }
}

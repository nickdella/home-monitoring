terraform {
  backend "s3" {
    profile = "home-monitoring-prod"
    region  = "us-west-2"
    bucket  = "terraform-state-d0de12955ca178d4"
    key     = "home-monitoring"
  }
}

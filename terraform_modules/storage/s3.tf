resource "aws_s3_bucket" "home_monitoring" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_versioning" "home_monitoring" {
  bucket = aws_s3_bucket.home_monitoring.id
  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket_ownership_controls" "home_monitoring" {
  bucket = aws_s3_bucket.home_monitoring.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "home_monitoring" {
  bucket = aws_s3_bucket.home_monitoring.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "acl" {
  depends_on = [aws_s3_bucket_ownership_controls.home_monitoring]
  bucket = aws_s3_bucket.home_monitoring.id
  acl    = "private"
}

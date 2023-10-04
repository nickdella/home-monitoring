data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions    = ["sts:AssumeRole"]
    effect     = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "grafana_role" {
  name               = "grafana_role"
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

data "aws_iam_policy_document" "timestream_readonly" {
  statement {
    effect    = "Allow"
    actions   = [
      "timestream:DescribeDatabase",
      "timestream:ListMeasures",
      "timestream:DescribeEndpoints",
      "timestream:ListTables",
      "timestream:ListDatabases",
      "timestream:DescribeScheduledQuery",
      "timestream:Select",
      "timestream:ListTagsForResource",
      "timestream:PrepareQuery",
      "timestream:DescribeTable",
      "timestream:ListScheduledQueries",
      "timestream:SelectValues"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "timestream:DescribeEndpoints",
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.s3_assets_bucket_name}"
    ]
  }
  statement {
    effect    = "Allow"
    actions   = [
      "s3:GetObject*",
    ]
    resources = [
      "arn:aws:s3:::${var.s3_assets_bucket_name}/assets/*"
    ]
  }
}

resource "aws_iam_policy" "grafana_policy" {
  name        = "grafana_policy"
  policy      = data.aws_iam_policy_document.timestream_readonly.json
}

resource "aws_iam_role_policy_attachment" "grafana_role_policy_attachment" {
  role = aws_iam_role.grafana_role.name
  policy_arn = aws_iam_policy.grafana_policy.arn
}

resource "aws_iam_instance_profile" "grafana_profile" {
  name = "grafana_profile"
  role = aws_iam_role.grafana_role.name
}

resource "aws_s3_object" "dashboards" {
  for_each = fileset("../../../dashboards/", "*")
  bucket = var.s3_assets_bucket_name
  key = "assets/dashboards/${each.value}"
  source = "../../../dashboards/${each.value}"
  etag = filemd5("../../../dashboards/${each.value}")
}

resource "aws_s3_object" "conf" {
  bucket = var.s3_assets_bucket_name
  key = "assets/conf/grafana.ini"
  source = "../../../etc/grafana.ini"
  etag = filemd5("../../../etc/grafana.ini")
}

resource "aws_security_group" "web_server" {
  name        = "web_server"
  description = "Allow inbound HTTP(S) traffic and SSH"
  vpc_id      = var.vpc_main_id

  ingress {
    description      = "TLS from VPC"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "HTTP from VPC"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "HTTP from VPC"
    from_port        = 3000
    to_port          = 3000
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

resource "aws_launch_template" "grafana_launch_template" {
  name          = "grafana_launch_template"
  # ubuntu 22 server, ARM
  image_id      = "ami-0c79a55dda52434da"
  instance_type = "t4g.micro"
  update_default_version = true
  iam_instance_profile {
    arn = aws_iam_instance_profile.grafana_profile.arn
  }
  key_name = "grafana"

  user_data = base64encode(
    templatefile(
      "${path.module}/install_grafana.sh.tftpl",
      {
        s3_assets_bucket_name = var.s3_assets_bucket_name
        grafana_admin_password = var.grafana_admin_password
      }
    )
  )

  network_interfaces {
    device_index    = 0
    associate_public_ip_address = true
    security_groups = [aws_security_group.web_server.id]
  }
  tag_specifications {
    resource_type = "instance"

    tags = {
      Name = "grafana"
    }
  }
}

resource "aws_autoscaling_group" "grafana_asg" {
  name = "grafana_asg"
  desired_capacity    = 0
  max_size            = 1
  min_size            = 0
  vpc_zone_identifier = [var.public_subnet_id]

  launch_template {
    id      = aws_launch_template.grafana_launch_template.id
    version = aws_launch_template.grafana_launch_template.latest_version
  }

  # we're manage the ASG size through automation
  lifecycle {
    ignore_changes = [desired_capacity]
  }
}

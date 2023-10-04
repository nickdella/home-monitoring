resource "aws_iam_group" "console_group" {
  name = "console"
}

resource "aws_iam_group" "admin_group" {
  name = "admins"
}

resource "aws_iam_group_policy_attachment" "admin_group_policy" {
  group      = aws_iam_group.admin_group.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_account_password_policy" "password_policy" {
  minimum_password_length        = 16
  require_lowercase_characters   = true
  require_numbers                = true
  require_uppercase_characters   = true
  require_symbols                = true
  allow_users_to_change_password = true
}

locals {
  users = [
    {
      name : var.user_name,
      groups : [aws_iam_group.console_group.name, aws_iam_group.admin_group.name]
    }
  ]
}

resource "aws_iam_user" "user" {
  for_each = { for user in local.users : user.name => user }
  name     = each.value.name
}

resource "aws_iam_user_group_membership" "user_group_membership" {
  for_each = { for user in local.users : user.name => user }
  user     = each.value.name
  groups   = each.value.groups
  depends_on = [
    aws_iam_user.user
  ]
}

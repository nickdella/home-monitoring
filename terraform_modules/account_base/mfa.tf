data "aws_caller_identity" "current" {}

module "enforce_mfa" {
  source                          = "terraform-module/enforce-mfa/aws"
  version                         = "1.1.1"
  policy_name                     = "managed-mfa-enforce"
  account_id                      = data.aws_caller_identity.current.id
  groups                          = [aws_iam_group.console_group.name]
  manage_own_signing_certificates = true
  manage_own_ssh_public_keys      = true
  manage_own_git_credentials      = true
}

## account_base module
Bootstraps base resources in a new account. See instructions below on manual account
creation steps required before running terraform.

## Manual account setup steps:

- Create a new AWS account under the organization (be sure to use a unique '+' style email address)
- Log into the console with the new account email address and reset the root account password
- Set up MFA for root account (top-right account menu->Security Credentials)
- Go to IAM and set up 'terraform' IAM user (no console access), w/administrator policy,  generate access key
- Go to EC2 and create a new key pair, download PEM file and move to ~/.ssh w/permissions 600
- Add terraform user credentials to ~/.aws/credentials. The dev account credentials 
  should be under the `[default]` section, whereas prod credentials fall under `[home-monitoring-prod]`
- Run create_backend.sh to create Terraform S3 bucket
- Copy generated bucket name to backend.tf under account root module (e.g. `terraform/environments/dev/backend.tf`)
- Import this module `account_base` into account root module, configuring the `user_name` variable
- Run Terraform:
  - `terraform init`
  - `terraform plan -out tflane`
  - `terraform apply tfplan`
- Log into console as IAM admin user, setup MFA

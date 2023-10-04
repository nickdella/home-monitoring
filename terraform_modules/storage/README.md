# Copying/restoring timestream backups across accounts

The original production metrics table was created in the organization root account. When 
we moved to separate dev/prod accounts, we needed to export (backup) the table and import it
into production. We list the steps taken below for posterity:

- Perform a backup of the table in the organization root account ([docs](https://docs.aws.amazon.com/aws-backup/latest/devguide/timestream-backup.html))
- Copy the backup to the prod account. This cross-account backup copying was non-trivial from an IAM standpoint, but we shouldn't have to do it again ([docs](https://docs.aws.amazon.com/aws-backup/latest/devguide/create-cross-account-backup.html))
- Temporarily rename the `metrics` table in terraform to `metrics_tmp` and run `terraform apply`. This "makes room" for the restored `metrics` table without breaking other references to the table
- Restore the backup into the prod account. Name the restored table `metrics`
- Create the `aws_timestreamwrites_table.metrics` by copying the `metrics_tmp` resource block. Run `terraform plan` to verify configuration.
- Run `terraform import` to import the resource. Note the [ID format documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/timestreamwrite_table#import)
````terraform import module.storage.aws_timestreamwrite_table.metrics metrics:home_monitoring````
- Delete the `metrics_tmp` resource definition. Run `terraform plan` and `terraform apply`

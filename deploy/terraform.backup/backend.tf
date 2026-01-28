# Terraform Backend Configuration
# Store state in S3 with DynamoDB locking

# Note: This backend block should be uncommented after creating the S3 bucket and DynamoDB table
# Run these commands first:
#   aws s3api create-bucket --bucket knowledgeweaver-terraform-state-<YOUR-ACCOUNT-ID> --region ap-southeast-2 --create-bucket-configuration LocationConstraint=ap-southeast-2
#   aws s3api put-bucket-versioning --bucket knowledgeweaver-terraform-state-<YOUR-ACCOUNT-ID> --versioning-configuration Status=Enabled
#   aws dynamodb create-table --table-name knowledgeweaver-terraform-locks --attribute-definitions AttributeName=LockID,AttributeType=S --key-schema AttributeName=LockID,KeyType=HASH --billing-mode PAY_PER_REQUEST --region ap-southeast-2

# terraform {
#   backend "s3" {
#     bucket         = "knowledgeweaver-terraform-state-<YOUR-ACCOUNT-ID>"
#     key            = "production/terraform.tfstate"
#     region         = "ap-southeast-2"
#     encrypt        = true
#     dynamodb_table = "knowledgeweaver-terraform-locks"
#   }
# }

# For initial setup, use local backend (default)
# After infrastructure is stable, uncomment above and run: terraform init -migrate-state

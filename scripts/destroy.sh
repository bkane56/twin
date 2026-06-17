#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "Error: Environment parameter is required."
  echo "Usage: $0 <dev|test|prod>"
  exit 1
fi

ENVIRONMENT=$1
PROJECT_NAME=${2:-twin}
AWS_REGION=${DEFAULT_AWS_REGION:-us-east-1}

if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
  echo "Error: Environment must be one of: dev, test, prod"
  exit 1
fi

cd "$(dirname "$0")/../terraform"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Preparing to destroy ${PROJECT_NAME}-${ENVIRONMENT} infrastructure."
echo "The custom domain brianekane.com is not managed by this repo and must not be destroyed here."

echo "Initializing Terraform remote state."
terraform init -input=false \
  -backend-config="bucket=twin-terraform-state-${AWS_ACCOUNT_ID}" \
  -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=twin-terraform-locks" \
  -backend-config="encrypt=true"

if ! terraform workspace list | sed 's/*//g' | awk '{$1=$1};1' | grep -qx "$ENVIRONMENT"; then
  echo "Error: Workspace '$ENVIRONMENT' does not exist."
  echo "Available workspaces:"
  terraform workspace list
  exit 1
fi

terraform workspace select "$ENVIRONMENT"

FRONTEND_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-frontend-${AWS_ACCOUNT_ID}"
MEMORY_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-memory-${AWS_ACCOUNT_ID}"

if aws s3 ls "s3://$FRONTEND_BUCKET" >/dev/null 2>&1; then
  echo "Emptying $FRONTEND_BUCKET."
  aws s3 rm "s3://$FRONTEND_BUCKET" --recursive
else
  echo "Frontend bucket not found or already empty."
fi

if aws s3 ls "s3://$MEMORY_BUCKET" >/dev/null 2>&1; then
  echo "Emptying $MEMORY_BUCKET."
  aws s3 rm "s3://$MEMORY_BUCKET" --recursive
else
  echo "Memory bucket not found or already empty."
fi

if [ ! -f "../backend/lambda-deployment.zip" ]; then
  echo "Creating dummy lambda package for destroy operation."
  echo "dummy" | zip ../backend/lambda-deployment.zip -
fi

echo "Running Terraform destroy."
if [ "$ENVIRONMENT" = "prod" ] && [ -f "prod.tfvars" ]; then
  terraform destroy \
    -var-file=prod.tfvars \
    -var="project_name=$PROJECT_NAME" \
    -var="environment=$ENVIRONMENT" \
    -var="use_custom_domain=false" \
    -var="root_domain=" \
    -auto-approve
else
  terraform destroy \
    -var="project_name=$PROJECT_NAME" \
    -var="environment=$ENVIRONMENT" \
    -var="use_custom_domain=false" \
    -var="root_domain=" \
    -auto-approve
fi

echo "Infrastructure for ${ENVIRONMENT} has been destroyed."
echo "Optional cleanup after verifying state:"
echo "  terraform workspace select default"
echo "  terraform workspace delete $ENVIRONMENT"

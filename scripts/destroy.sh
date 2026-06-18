#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-}"
PROJECT_NAME="${2:-twin}"

if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
  echo "Invalid or missing environment: ${ENVIRONMENT:-<empty>}"
  echo "Allowed values: dev, test, prod"
  exit 1
fi

echo "Destroying ${PROJECT_NAME} ${ENVIRONMENT}."

cd "$(dirname "$0")/.."
cd terraform

AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
AWS_REGION="${DEFAULT_AWS_REGION:-us-east-1}"

terraform init -input=false \
  -backend-config="bucket=twin-terraform-state-${AWS_ACCOUNT_ID}" \
  -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=twin-terraform-locks" \
  -backend-config="encrypt=true"

if terraform workspace list | sed 's/*//g' | awk '{$1=$1};1' | grep -qx "$ENVIRONMENT"; then
  terraform workspace select "$ENVIRONMENT"
else
  echo "Terraform workspace does not exist: $ENVIRONMENT"
  exit 1
fi

TF_DESTROY_CMD=(
  terraform destroy
  -var="project_name=${PROJECT_NAME}"
  -var="environment=${ENVIRONMENT}"
  -auto-approve
)

if [ "$ENVIRONMENT" = "prod" ]; then
  TF_DESTROY_CMD+=(
    -var-file=prod.tfvars
    -var="use_custom_domain=false"
    -var="root_domain="
  )
fi

echo "Running Terraform destroy."
"${TF_DESTROY_CMD[@]}"

echo "Destroy complete for ${ENVIRONMENT}."

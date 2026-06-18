#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
PROJECT_NAME="${2:-twin}"

if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
  echo "Invalid environment: $ENVIRONMENT"
  echo "Allowed values: dev, test, prod"
  exit 1
fi

echo "Deploying ${PROJECT_NAME} to ${ENVIRONMENT}."

cd "$(dirname "$0")/.."

echo "Building Lambda package."
(
  cd backend
  uv run deploy.py
)

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
  terraform workspace new "$ENVIRONMENT"
fi

TF_APPLY_CMD=(
  terraform apply
  -var="project_name=${PROJECT_NAME}"
  -var="environment=${ENVIRONMENT}"
  -auto-approve
)

if [ "$ENVIRONMENT" = "prod" ]; then
  TF_APPLY_CMD+=(
    -var-file=prod.tfvars
    -var="use_custom_domain=false"
    -var="root_domain="
  )
fi

echo "Applying Terraform."
"${TF_APPLY_CMD[@]}"

API_URL="$(terraform output -raw api_gateway_url)"
FRONTEND_BUCKET="$(terraform output -raw s3_frontend_bucket)"
CUSTOM_URL="$(terraform output -raw custom_domain_url 2>/dev/null || true)"
CLOUDFRONT_URL="$(terraform output -raw cloudfront_url)"

cd ../frontend

echo "Setting frontend API URL."
echo "NEXT_PUBLIC_API_URL=${API_URL}" > .env.production

npm install
npm run build

aws s3 sync ./out "s3://${FRONTEND_BUCKET}/" --delete

cd ..

echo ""
echo "Deployment complete."
echo "CloudFront URL: ${CLOUDFRONT_URL}"
if [ -n "$CUSTOM_URL" ]; then
  echo "Custom domain: ${CUSTOM_URL}"
else
  echo "Custom domain: disabled"
fi
echo "API Gateway: ${API_URL}"

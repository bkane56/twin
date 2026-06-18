#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT=${1:-dev}
PROJECT_NAME=${2:-twin}
AWS_REGION=${DEFAULT_AWS_REGION:-us-east-2}

if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod|prod2)$ ]]; then
  echo "Error: Environment must be one of: dev, test, prod, prod2"
  exit 1
fi

cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' is not installed or not on PATH."
    exit 1
  fi
}

require_command aws
require_command terraform
require_command uv
require_command yarn

echo "Deploying ${PROJECT_NAME} to ${ENVIRONMENT}."
echo "Custom domain deployment is intentionally disabled in this repo."
echo "brianekane.com is reserved for the personal website and must not be managed by Digital Twin Terraform."

echo "Building Lambda package."
(cd backend && uv run deploy.py)

echo "Initializing Terraform remote state."
cd "$REPO_ROOT/terraform"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

terraform init -input=false -reconfigure \
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

echo "Applying Terraform."
if [ "$ENVIRONMENT" = "prod" ] && [ -f "prod.tfvars" ]; then
  terraform apply \
    -var-file=prod.tfvars \
    -var="project_name=$PROJECT_NAME" \
    -var="environment=$ENVIRONMENT" \
    -var="use_custom_domain=false" \
    -var="root_domain=" \
    -auto-approve
else
  terraform apply \
    -var="project_name=$PROJECT_NAME" \
    -var="environment=$ENVIRONMENT" \
    -var="use_custom_domain=false" \
    -var="root_domain=" \
    -auto-approve
fi

API_URL=$(terraform output -raw api_gateway_url)
FRONTEND_BUCKET=$(terraform output -raw s3_frontend_bucket)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)
CLOUDFRONT_DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)

cd "$REPO_ROOT/frontend"

echo "Writing frontend production API configuration."
echo "NEXT_PUBLIC_API_URL=${API_URL}" > .env.production

echo "Installing frontend dependencies with Yarn."
yarn install --frozen-lockfile

echo "Building static frontend export."
yarn build

if [ ! -f "out/index.html" ]; then
  echo "Error: frontend build did not produce out/index.html."
  echo "Check frontend/next.config.ts and confirm Next.js static export is enabled."
  exit 1
fi

echo "Syncing frontend static export to S3 bucket: ${FRONTEND_BUCKET}."
aws s3 sync "out/" "s3://${FRONTEND_BUCKET}/" --delete

echo "Invalidating CloudFront distribution: ${CLOUDFRONT_DISTRIBUTION_ID}."
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
  --paths "/*"

cd "$REPO_ROOT"

echo ""
echo "Deployment complete."
echo "CloudFront URL: ${CLOUDFRONT_URL}"
echo "API Gateway: ${API_URL}"
echo "Frontend Bucket: ${FRONTEND_BUCKET}"
echo "CloudFront Distribution ID: ${CLOUDFRONT_DISTRIBUTION_ID}"
echo "Custom domain: not configured. Do not point brianekane.com at this deployment."

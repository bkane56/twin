# These are for a work in progress, and are not yet ready for production use.  Please do not use these values in production.
environment  = "prod2"
project_name = "twin"
aws_region   = "us-east-2"

bedrock_model_id = "us.amazon.nova-pro-v1:0"

lambda_timeout           = 60
api_throttle_burst_limit = 20
api_throttle_rate_limit  = 10

use_custom_domain = false
root_domain       = ""

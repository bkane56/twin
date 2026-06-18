project_name = "twin"
environment  = "prod"

bedrock_model_id = "amazon.nova-pro-v1:0"

lambda_timeout            = 60
api_throttle_burst_limit  = 20
api_throttle_rate_limit   = 10

# IMPORTANT:
# brianekane.com is now reserved for the personal website hosted through AWS and Vercel.
# The Digital Twin production deployment must not create, change, or destroy Route 53,
# ACM, or CloudFront alias resources for brianekane.com.
use_custom_domain = false
root_domain       = ""

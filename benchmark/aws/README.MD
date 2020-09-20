# Stress Tests on AWS


#### Cloudformation

Creates `Cloudformation` stack on AWS (Following can be customized)
- EC2 instance
  - Instance Type
  - AMI
  - Availability Zone
- Volume
  - Volume Size
  - Volume Type
- Elastic IP
  


#### SSM Document

Creates `SSM Document` (Way to run long running commands on ec2)
- Mounts Volume on ec2
- Compiles `jina` from pip or git (any remote branch)
- Clones `jina-ai/stress-test` from any remote branch
- Runs stress-test on ec2
- Gets results pushed to public `S3` bucket


##### Pending
- Remove aws-tokens from code, read them from env
- Push cloudwatch metrics/dashboard to get CPU, Disk utilization metrics
- Push other result objects to S3

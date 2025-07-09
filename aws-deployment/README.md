# AWS Deployment README

## Quick Deployment to AWS

### Prerequisites
1. **AWS CLI installed and configured**
   ```bash
   aws configure
   ```
2. **Docker installed**
3. **Git Bash or Linux/Mac terminal** (for shell scripts)

### Option 1: Complete Automated Deployment (Recommended)

Run the complete deployment script:
```bash
chmod +x aws-deployment/deploy-complete.sh
./aws-deployment/deploy-complete.sh
```

This script will:
- ✅ Create complete AWS infrastructure (VPC, RDS, Redis, ECS, ALB)
- ✅ Build and push Docker image to ECR
- ✅ Deploy application to ECS Fargate
- ✅ Set up load balancer and security groups
- ✅ Configure secrets management

### Option 2: Step-by-Step Deployment

#### Step 1: Deploy Infrastructure
```bash
aws cloudformation deploy \
    --template-file aws-deployment/infrastructure.yaml \
    --stack-name health-monitoring-stack \
    --parameter-overrides DatabasePassword=YourSecurePassword123! \
    --capabilities CAPABILITY_IAM \
    --region us-east-1
```

#### Step 2: Build and Push Docker Image
```bash
# Get ECR repository URI from CloudFormation output
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name health-monitoring-stack \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepository`].OutputValue' \
    --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI

# Build and push
docker build -f Dockerfile.production -t health-monitoring:latest .
docker tag health-monitoring:latest $ECR_URI:latest
docker push $ECR_URI:latest
```

#### Step 3: Create ECS Service
```bash
# Update task definition with your values and register
aws ecs register-task-definition --cli-input-json file://aws-deployment/ecs-task-definition.json

# Create service
aws ecs create-service \
    --cluster health-monitoring-cluster \
    --service-name health-monitoring-service \
    --task-definition health-monitoring-task \
    --desired-count 1 \
    --launch-type FARGATE
```

### Option 3: Manual AWS Console Deployment

1. **Create infrastructure using CloudFormation**
   - Upload `infrastructure.yaml` template
   - Set parameters (database password, etc.)

2. **Build and push to ECR**
   - Create ECR repository
   - Push Docker image

3. **Create ECS service**
   - Use task definition from `ecs-task-definition.json`
   - Configure networking and load balancer

## AWS Services Used

### Core Services
- **ECS Fargate**: Serverless container hosting
- **ECR**: Container registry
- **RDS PostgreSQL**: Database
- **ElastiCache Redis**: Caching
- **Application Load Balancer**: Traffic distribution
- **VPC**: Network isolation

### Security & Management
- **Secrets Manager**: Secure credential storage
- **CloudWatch**: Logging and monitoring
- **IAM**: Access control

## Cost Estimation (us-east-1)

### Monthly Costs (Approximate)
- **ECS Fargate (1 task)**: ~$15-25
- **RDS PostgreSQL (t3.micro)**: ~$15-20
- **ElastiCache Redis (t3.micro)**: ~$15-20
- **Application Load Balancer**: ~$18-22
- **Data Transfer**: ~$5-15
- **ECR Storage**: ~$1-5

**Total: ~$70-110/month**

### Cost Optimization Tips
- Use Reserved Instances for RDS
- Enable ECS Service Auto Scaling
- Set up CloudWatch billing alerts
- Use Spot Instances for non-production

## Monitoring & Management

### View Application Logs
```bash
aws logs tail /ecs/health-monitoring --follow --region us-east-1
```

### Update Application
```bash
# Push new image
docker build -f Dockerfile.production -t health-monitoring:latest .
docker tag health-monitoring:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Force new deployment
aws ecs update-service \
    --cluster health-monitoring-cluster \
    --service health-monitoring-service \
    --force-new-deployment
```

### Scale Application
```bash
aws ecs update-service \
    --cluster health-monitoring-cluster \
    --service health-monitoring-service \
    --desired-count 2
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   - Check CloudWatch logs: `/ecs/health-monitoring`
   - Verify environment variables and secrets

2. **Database connection issues**
   - Check security group rules
   - Verify database endpoint and credentials

3. **Load balancer health checks failing**
   - Check application is running on port 5000
   - Verify health check path is accessible

### Debug Commands
```bash
# Check service status
aws ecs describe-services \
    --cluster health-monitoring-cluster \
    --services health-monitoring-service

# Check task status
aws ecs list-tasks \
    --cluster health-monitoring-cluster \
    --service-name health-monitoring-service

# Get task details
aws ecs describe-tasks \
    --cluster health-monitoring-cluster \
    --tasks TASK_ARN
```

## Security Best Practices

✅ **Implemented**:
- VPC with private subnets for database
- Security groups with minimal required access
- Secrets stored in AWS Secrets Manager
- Non-root user in Docker container
- IAM roles with least privilege

🔧 **Additional Recommendations**:
- Enable AWS WAF for the load balancer
- Set up AWS Config for compliance monitoring
- Enable VPC Flow Logs
- Use AWS Certificate Manager for SSL/TLS
- Set up AWS GuardDuty for threat detection

## Cleanup

To delete all AWS resources:
```bash
aws cloudformation delete-stack --stack-name health-monitoring-stack --region us-east-1
```

⚠️ **Warning**: This will delete all data including the database!

## Support

For deployment issues:
1. Check CloudWatch logs
2. Review AWS CloudFormation events
3. Verify IAM permissions
4. Check security group configurations

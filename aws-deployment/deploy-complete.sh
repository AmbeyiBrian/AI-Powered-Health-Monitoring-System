#!/bin/bash

# Complete AWS Deployment Script for Health Monitoring System
# This script deploys the complete infrastructure and application

set -e

# Configuration
AWS_REGION="us-east-1"  # Change this to your preferred region
STACK_NAME="health-monitoring-stack"
DB_PASSWORD="HealthMonitor123!"  # Change this to a secure password

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Complete AWS Deployment for Health Monitoring System${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    echo -e "${YELLOW}📋 Installation: https://aws.amazon.com/cli/${NC}"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
echo -e "${GREEN}✅ AWS Region: ${AWS_REGION}${NC}"

# Step 1: Deploy Infrastructure using CloudFormation
echo -e "\n${YELLOW}📋 Step 1: Deploying Infrastructure with CloudFormation...${NC}"
aws cloudformation deploy \
    --template-file aws-deployment/infrastructure.yaml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides DatabasePassword=${DB_PASSWORD} \
    --capabilities CAPABILITY_IAM \
    --region ${AWS_REGION}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Infrastructure deployed successfully!${NC}"
else
    echo -e "${RED}❌ Infrastructure deployment failed!${NC}"
    exit 1
fi

# Step 2: Get stack outputs
echo -e "\n${YELLOW}📋 Step 2: Getting stack outputs...${NC}"
ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepository`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

ECS_CLUSTER=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

DB_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

REDIS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

LOAD_BALANCER_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

TASK_EXECUTION_ROLE=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskExecutionRoleArn`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

TASK_ROLE=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSTaskRoleArn`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

TARGET_GROUP_ARN=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`TargetGroupArn`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

SECURITY_GROUP_ID=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSSecurityGroupId`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

SUBNET_1=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnet1Id`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

SUBNET_2=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`PublicSubnet2Id`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

echo -e "${GREEN}✅ Stack outputs retrieved successfully!${NC}"

# Step 3: Create secrets in AWS Secrets Manager
echo -e "\n${YELLOW}📋 Step 3: Creating secrets in AWS Secrets Manager...${NC}"

# Create Flask secret key
FLASK_SECRET_KEY=$(openssl rand -base64 32)
aws secretsmanager create-secret \
    --name "health-monitoring/flask-secret-key" \
    --description "Flask secret key for Health Monitoring System" \
    --secret-string "${FLASK_SECRET_KEY}" \
    --region ${AWS_REGION} 2>/dev/null || \
aws secretsmanager put-secret-value \
    --secret-id "health-monitoring/flask-secret-key" \
    --secret-string "${FLASK_SECRET_KEY}" \
    --region ${AWS_REGION}

# Create database password secret
aws secretsmanager create-secret \
    --name "health-monitoring/db-password" \
    --description "Database password for Health Monitoring System" \
    --secret-string "${DB_PASSWORD}" \
    --region ${AWS_REGION} 2>/dev/null || \
aws secretsmanager put-secret-value \
    --secret-id "health-monitoring/db-password" \
    --secret-string "${DB_PASSWORD}" \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ Secrets created successfully!${NC}"

# Step 4: Build and push Docker image
echo -e "\n${YELLOW}📋 Step 4: Building and pushing Docker image...${NC}"

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build Docker image
docker build -t health-monitoring:latest .

# Tag and push image
docker tag health-monitoring:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

echo -e "${GREEN}✅ Docker image pushed successfully!${NC}"

# Step 5: Create ECS task definition
echo -e "\n${YELLOW}📋 Step 5: Creating ECS task definition...${NC}"

cat > aws-deployment/ecs-task-definition-production.json << EOF
{
  "family": "health-monitoring-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "${TASK_EXECUTION_ROLE}",
  "taskRoleArn": "${TASK_ROLE}",
  "containerDefinitions": [
    {
      "name": "health-monitoring-web",
      "image": "${ECR_URI}:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://health_user:${DB_PASSWORD}@${DB_ENDPOINT}:5432/health_monitoring"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://${REDIS_ENDPOINT}:6379"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:health-monitoring/flask-secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/health-monitoring",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# Create CloudWatch Log Group
aws logs create-log-group \
    --log-group-name "/ecs/health-monitoring" \
    --region ${AWS_REGION} 2>/dev/null || echo "Log group already exists"

# Register task definition
aws ecs register-task-definition \
    --cli-input-json file://aws-deployment/ecs-task-definition-production.json \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ ECS task definition registered successfully!${NC}"

# Step 6: Create ECS service
echo -e "\n${YELLOW}📋 Step 6: Creating ECS service...${NC}"

aws ecs create-service \
    --cluster ${ECS_CLUSTER} \
    --service-name health-monitoring-service \
    --task-definition health-monitoring-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${SECURITY_GROUP_ID}],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=${TARGET_GROUP_ARN},containerName=health-monitoring-web,containerPort=5000" \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ ECS service created successfully!${NC}"

# Step 7: Wait for service to be stable
echo -e "\n${YELLOW}📋 Step 7: Waiting for service to be stable...${NC}"
echo -e "${BLUE}⏳ This may take a few minutes...${NC}"

aws ecs wait services-stable \
    --cluster ${ECS_CLUSTER} \
    --services health-monitoring-service \
    --region ${AWS_REGION}

echo -e "${GREEN}✅ Service is stable and running!${NC}"

# Step 8: Display deployment summary
echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo -e "   • Stack Name: ${STACK_NAME}"
echo -e "   • Region: ${AWS_REGION}"
echo -e "   • ECS Cluster: ${ECS_CLUSTER}"
echo -e "   • ECR Repository: ${ECR_URI}"
echo -e "   • Database Endpoint: ${DB_ENDPOINT}"
echo -e "   • Redis Endpoint: ${REDIS_ENDPOINT}"
echo -e "   • Load Balancer URL: ${LOAD_BALANCER_URL}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

echo -e "\n${GREEN}🌐 Your Health Monitoring System is now available at:${NC}"
echo -e "${BLUE}${LOAD_BALANCER_URL}${NC}"

echo -e "\n${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Wait 2-3 minutes for the application to fully start"
echo -e "   2. Access your application at: ${LOAD_BALANCER_URL}"
echo -e "   3. Set up a custom domain with Route 53 (optional)"
echo -e "   4. Configure SSL certificate with ACM (optional)"
echo -e "   5. Set up monitoring with CloudWatch (optional)"

echo -e "\n${YELLOW}🔧 Management Commands:${NC}"
echo -e "   • View logs: aws logs tail /ecs/health-monitoring --follow --region ${AWS_REGION}"
echo -e "   • Update service: aws ecs update-service --cluster ${ECS_CLUSTER} --service health-monitoring-service --force-new-deployment --region ${AWS_REGION}"
echo -e "   • Delete stack: aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${AWS_REGION}"

echo -e "\n${GREEN}✅ Deployment complete!${NC}"

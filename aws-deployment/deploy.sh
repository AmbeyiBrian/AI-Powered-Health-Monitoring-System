#!/bin/bash

# AWS ECS Deployment Script for Health Monitoring System
# Make sure you have AWS CLI configured: aws configure

set -e

# Configuration
AWS_REGION="us-east-1"  # Change to your preferred region
CLUSTER_NAME="health-monitoring-cluster"
SERVICE_NAME="health-monitoring-service"
REPOSITORY_NAME="health-monitoring"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AWS ECS Deployment for Health Monitoring System${NC}"

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${YELLOW}📋 AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"

# 1. Create ECR Repository
echo -e "${YELLOW}📦 Creating ECR Repository...${NC}"
aws ecr create-repository \
    --repository-name ${REPOSITORY_NAME} \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true || echo "Repository might already exist"

# 2. Get ECR login token
echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# 3. Build and tag Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t ${REPOSITORY_NAME}:${IMAGE_TAG} .

# 4. Tag image for ECR
docker tag ${REPOSITORY_NAME}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}

# 5. Push image to ECR
echo -e "${YELLOW}📤 Pushing image to ECR...${NC}"
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}:${IMAGE_TAG}

# 6. Create ECS Cluster
echo -e "${YELLOW}🏗️ Creating ECS Cluster...${NC}"
aws ecs create-cluster \
    --cluster-name ${CLUSTER_NAME} \
    --capacity-providers FARGATE \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --region ${AWS_REGION} || echo "Cluster might already exist"

# 7. Create VPC and Subnets (if needed)
echo -e "${YELLOW}🌐 Setting up VPC...${NC}"
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --query 'Vpc.VpcId' \
    --output text \
    --region ${AWS_REGION} 2>/dev/null || echo "")

if [ ! -z "$VPC_ID" ]; then
    echo -e "${GREEN}✅ Created VPC: ${VPC_ID}${NC}"
    
    # Create Internet Gateway
    IGW_ID=$(aws ec2 create-internet-gateway \
        --query 'InternetGateway.InternetGatewayId' \
        --output text \
        --region ${AWS_REGION})
    
    aws ec2 attach-internet-gateway \
        --vpc-id ${VPC_ID} \
        --internet-gateway-id ${IGW_ID} \
        --region ${AWS_REGION}
    
    # Create Subnets
    SUBNET_1=$(aws ec2 create-subnet \
        --vpc-id ${VPC_ID} \
        --cidr-block 10.0.1.0/24 \
        --availability-zone ${AWS_REGION}a \
        --query 'Subnet.SubnetId' \
        --output text \
        --region ${AWS_REGION})
    
    SUBNET_2=$(aws ec2 create-subnet \
        --vpc-id ${VPC_ID} \
        --cidr-block 10.0.2.0/24 \
        --availability-zone ${AWS_REGION}b \
        --query 'Subnet.SubnetId' \
        --output text \
        --region ${AWS_REGION})
    
    echo -e "${GREEN}✅ Created Subnets: ${SUBNET_1}, ${SUBNET_2}${NC}"
else
    echo -e "${YELLOW}⚠️ Using existing VPC${NC}"
    # Get default VPC
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters "Name=isDefault,Values=true" \
        --query 'Vpcs[0].VpcId' \
        --output text \
        --region ${AWS_REGION})
    
    # Get default subnets
    SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=${VPC_ID}" \
        --query 'Subnets[].SubnetId' \
        --output text \
        --region ${AWS_REGION})
    SUBNET_1=$(echo $SUBNETS | cut -d' ' -f1)
    SUBNET_2=$(echo $SUBNETS | cut -d' ' -f2)
fi

# 8. Create Security Group
echo -e "${YELLOW}🔒 Creating Security Group...${NC}"
SG_ID=$(aws ec2 create-security-group \
    --group-name health-monitoring-sg \
    --description "Security group for Health Monitoring System" \
    --vpc-id ${VPC_ID} \
    --query 'GroupId' \
    --output text \
    --region ${AWS_REGION} 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=health-monitoring-sg" \
        --query 'SecurityGroups[0].GroupId' \
        --output text \
        --region ${AWS_REGION})

# Add inbound rules
aws ec2 authorize-security-group-ingress \
    --group-id ${SG_ID} \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0 \
    --region ${AWS_REGION} 2>/dev/null || echo "Security group rule might already exist"

aws ec2 authorize-security-group-ingress \
    --group-id ${SG_ID} \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region ${AWS_REGION} 2>/dev/null || echo "Security group rule might already exist"

echo -e "${GREEN}✅ Security Group: ${SG_ID}${NC}"

# 9. Update task definition with actual values
echo -e "${YELLOW}📝 Updating task definition...${NC}"
sed -i "s/YOUR_ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" aws-deployment/ecs-task-definition.json
sed -i "s/YOUR_REGION/${AWS_REGION}/g" aws-deployment/ecs-task-definition.json

# 10. Register task definition
echo -e "${YELLOW}📋 Registering ECS Task Definition...${NC}"
aws ecs register-task-definition \
    --cli-input-json file://aws-deployment/ecs-task-definition.json \
    --region ${AWS_REGION}

# 11. Create ECS Service
echo -e "${YELLOW}🚀 Creating ECS Service...${NC}"
aws ecs create-service \
    --cluster ${CLUSTER_NAME} \
    --service-name ${SERVICE_NAME} \
    --task-definition health-monitoring-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
    --region ${AWS_REGION}

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${YELLOW}📋 Resources created:${NC}"
echo -e "   • ECR Repository: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPOSITORY_NAME}"
echo -e "   • ECS Cluster: ${CLUSTER_NAME}"
echo -e "   • ECS Service: ${SERVICE_NAME}"
echo -e "   • VPC: ${VPC_ID}"
echo -e "   • Security Group: ${SG_ID}"

echo -e "${YELLOW}🔍 To get the public IP of your service:${NC}"
echo "aws ecs describe-tasks --cluster ${CLUSTER_NAME} --tasks \$(aws ecs list-tasks --cluster ${CLUSTER_NAME} --service-name ${SERVICE_NAME} --query 'taskArns[0]' --output text) --query 'tasks[0].attachments[0].details[?name==\`networkInterfaceId\`].value' --output text | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --query 'NetworkInterfaces[0].Association.PublicIp' --output text"

echo -e "${RED}⚠️ Important:${NC}"
echo -e "   • Set up RDS PostgreSQL database"
echo -e "   • Set up ElastiCache Redis"
echo -e "   • Configure AWS Secrets Manager for sensitive data"
echo -e "   • Set up Application Load Balancer for production"
echo -e "   • Configure Route 53 for custom domain"

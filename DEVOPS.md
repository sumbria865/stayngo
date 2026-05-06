# 🚀 StayNGo DevOps & Infrastructure Documentation

This document outlines the complete DevOps architecture, tools, and deployment pipeline used in StayNGo.

---

## 📋 Table of Contents

1. [Technology Stack](#technology-stack)
2. [CI/CD Pipeline](#cicd-pipeline)
3. [Infrastructure Architecture](#infrastructure-architecture)
4. [Deployment Process](#deployment-process)
5. [Monitoring & Code Quality](#monitoring--code-quality)
6. [Security & Networking](#security--networking)
7. [Troubleshooting](#troubleshooting)

---

## 🛠️ Technology Stack

### **Core DevOps Technologies**

| Technology                    | Purpose                                  | Version             |
| ----------------------------- | ---------------------------------------- | ------------------- |
| **Jenkins**                   | CI/CD Automation & Build Orchestration   | Latest              |
| **SonarQube**                 | Code Quality & Static Analysis           | Latest              |
| **Docker**                    | Containerization                         | Latest              |
| **Docker Compose V2**         | Multi-container Orchestration (Dev/Prod) | V2                  |
| **Kubernetes (k3s/minikube)** | Container Orchestration (Optional)       | Latest              |
| **Terraform**                 | Infrastructure as Code (IaC)             | ~> 5.0              |
| **Ansible**                   | Configuration Management & Deployment    | Latest              |
| **AWS EC2**                   | Cloud Compute Infrastructure             | Ubuntu (Latest LTS) |
| **GitHub**                    | Version Control & Webhook Integration    | -                   |
| **Docker Hub**                | Container Registry                       | Public              |

### **Infrastructure Components**

- **Cloud Provider**: AWS
- **Compute**: EC2 (Ubuntu)
- **Storage**: EC2 EBS (20GB gp3)
- **Networking**: Default VPC, Security Groups
- **Load Balancing**: Kubernetes Service (LoadBalancer type)

---

## 🔄 CI/CD Pipeline

### **Pipeline Flow**

```
GitHub Push
    ↓
Jenkins Webhook Trigger
    ↓
Checkout Code
    ↓
Run SonarQube Scanner (Quality Gates)
    ↓
Build Docker Images (--no-cache)
    ↓
Inject Environment Variables (.env.production)
    ↓
Push Images to Docker Hub
    ↓
SSH to EC2 Instance
    ↓
Deploy via Docker Compose / Kubernetes
    ↓
Health Checks & Verification
```

### **Key Pipeline Stages**

#### **1. Source Control Integration**

- **Trigger**: GitHub Webhook on push
- **Repository**: GitHub (main branch monitored)
- **Authentication**: SSH keys or GitHub tokens

#### **2. Code Quality Gate**

- **Tool**: SonarQube
- **Type**: Remote analysis with token authorization
- **Scope**: Backend (Python), Frontend (TypeScript/React)
- **Enforced**: Must pass quality gates before build proceeds

#### **3. Build Stage**

```bash
# Backend
docker build --no-cache -t mayankc1533262/stayngo-backend:latest ./backend

# Frontend
docker build --no-cache -t mayankc1533262/stayngo-frontend:latest ./frontend
```

- **No Cache**: Forces fresh layer invalidation for latest dependencies
- **Build Args**: Environment variables injected via `.env.production`

#### **4. Push Stage**

- **Registry**: Docker Hub (Public)
- **Authentication**: Docker Hub credentials stored in Jenkins secrets
- **Images**:
  - `mayankc1533262/stayngo-backend:latest`
  - `mayankc1533262/stayngo-frontend:latest`

#### **5. Deploy Stage**

```bash
# SSH to EC2
ssh -i ~/.ssh/stayngo-deployer-key ubuntu@65.0.117.219

# Pull latest images and deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🏗️ Infrastructure Architecture

### **AWS Infrastructure (Terraform)**

#### **Compute Resources**

```hcl
# EC2 Instance
- Instance Type: Configurable (default: t3.medium)
- AMI: Ubuntu 22.04 LTS
- Storage: 20GB gp3 EBS volume
- Public IP: Elastic IP (65.0.117.219)
- SSH Key: stayngo-deployer-key
```

#### **Security Group Rules**

```
Ingress Rules:
  - Port 22 (SSH): 0.0.0.0/0 (Administration)
  - Port 80 (HTTP): 0.0.0.0/0 (Kubernetes LoadBalancer)
  - Port 3000 (Frontend): 0.0.0.0/0 (Next.js App)
  - Port 5001 (Backend): 0.0.0.0/0 (Flask API)
  - Port 8080 (Jenkins): 0.0.0.0/0 (CI/CD Dashboard)
  - Port 9000 (SonarQube): 0.0.0.0/0 (Code Quality Dashboard)

Egress Rules:
  - All traffic allowed (0.0.0.0/0)
```

### **Deployed Services Architecture**

#### **Docker Compose Production Setup**

```yaml
Services:
  ├── Frontend (Next.js)
  │   ├── Image: mayankc1533262/stayngo-frontend:latest
  │   ├── Port: 3000
  │   ├── Restart: Always
  │   └── Env: .env (build-time variables)
  │
  └── Backend (Flask + Gunicorn)
      ├── Image: mayankc1533262/stayngo-backend:latest
      ├── Port: 5001
      ├── Restart: Always
      ├── Workers: 3
      ├── Threads: 4
      └── Env: .env (runtime variables)
```

#### **Kubernetes Deployment (Optional)**

```yaml
Frontend:
  - Replicas: 2
  - Service Type: LoadBalancer
  - Port Mapping: 80 → 3000
  - ConfigMap: stayngo-config

Backend:
  - Replicas: Configurable
  - Service Type: ClusterIP
  - Port: 5001
```

---

## 🚀 Deployment Process

### **Local Development**

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python app.py

# 2. Frontend (in another terminal)
cd frontend
npm install
npm run dev

# 3. Access
# Frontend: http://localhost:3000
# Backend: http://localhost:5001
```

### **Production Deployment**

#### **Prerequisites**

- Jenkins server running
- Docker Hub credentials configured
- Terraform state file management
- SSH key pair configured (`~/.ssh/id_rsa.pub`)
- AWS credentials configured locally or via IAM roles

#### **Step 1: Provision Infrastructure**

```bash
cd terraform
terraform init
terraform plan -var-file="variables.tfvars"
terraform apply
# Outputs EC2 public IP: 65.0.117.219
```

#### **Step 2: Configure EC2 Instance (Ansible)**

```bash
cd ansible
ansible-playbook setup.yml -i inventory.ini
# Installs: Docker, Docker Compose, kubectl, Docker credentials
```

#### **Step 3: Trigger Jenkins Build**

- Push code to GitHub
- Jenkins webhook triggers automatically
- Pipeline executes (SonarQube → Build → Push → Deploy)

#### **Step 4: Verify Deployment**

```bash
# SSH into EC2
ssh -i ~/.ssh/stayngo-deployer-key ubuntu@65.0.117.219

# Check running containers
docker ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify services
curl http://localhost:3000  # Frontend
curl http://localhost:5001/api  # Backend
```

---

## 📊 Monitoring & Code Quality

### **SonarQube Integration**

**Configuration**:

- **Server**: Hosted on EC2 (Port 9000)
- **Access**: `http://65.0.117.219:9000`
- **Analysis**: Remote token-based authorization
- **Scope**: Entire codebase (Backend + Frontend)
- **Quality Gates**: Enforced before Docker build

**Key Metrics Tracked**:

- Code coverage
- Bugs & vulnerabilities
- Code smells
- Duplication percentage
- Technical debt ratio

### **Jenkins Monitoring**

**Dashboard**: `http://65.0.117.219:8080`

**Tracked Metrics**:

- Build success/failure rates
- Build duration trends
- Deployment frequency
- Pipeline execution logs

### **Application Performance**

**Backend (Gunicorn Configuration)**:

```bash
# Multi-threaded workers prevent slow-client DDoS
gunicorn \
  --workers 3 \
  --threads 4 \
  --bind 0.0.0.0:5001 \
  --timeout 120 \
  app:app
```

**Frontend (Next.js Optimization)**:

- Static generation for maximum performance
- API proxy through `next.config.ts`
- Environment variable injection at build time

---

## 🔒 Security & Networking

### **Network Security**

1. **Security Groups**: Restrict inbound traffic to necessary ports only
2. **SSH Keys**: Private key authentication (no password login)
3. **Firewall**: AWS security groups act as stateful firewall

### **Secrets Management**

**Environment Variables**:

- `.env` files stored locally on EC2 (not in Git)
- Jenkins secrets store for Docker Hub credentials
- Supabase credentials injected at build/runtime

**Best Practices**:

- Never commit `.env` to Git
- Use `.env.example` for reference
- Rotate secrets periodically
- Limit EC2 security group access to known IPs (optional)

### **Data Protection**

- **Database**: Supabase PostgreSQL (encrypted at rest)
- **Authentication**: Supabase Auth (OAuth support)
- **Storage**: Supabase Storage (image uploads with policies)
- **API Communication**: HTTP (upgrade to HTTPS with CDN/Load Balancer for production)

---

## 🔧 Infrastructure as Code Files

### **Terraform**

- **File**: [terraform/main.tf](terraform/main.tf)
- **File**: [terraform/variables.tf](terraform/variables.tf)
- **Purpose**: Defines AWS resources (EC2, Security Groups, Key Pairs)

### **Ansible**

- **File**: [ansible/setup.yml](ansible/setup.yml)
- **File**: [ansible/inventory.ini](ansible/inventory.ini)
- **Purpose**: Configures EC2 instance with required software

### **Docker**

- **File**: [frontend/Dockerfile](frontend/Dockerfile)
- **File**: [backend/Dockerfile](backend/Dockerfile)
- **Purpose**: Container images for both services

### **Docker Compose**

- **File**: [docker-compose.prod.yml](docker-compose.prod.yml)
- **Purpose**: Production deployment configuration

### **Kubernetes**

- **File**: [k8s/frontend.yaml](k8s/frontend.yaml)
- **File**: [k8s/backend.yaml](k8s/backend.yaml)
- **File**: [k8s/configmap.yaml](k8s/configmap.yaml)
- **Purpose**: Kubernetes deployment manifests (optional alternative to Docker Compose)

---

## 📈 Troubleshooting

### **Common Issues**

#### **1. Supabase Keys Not Available at Build Time**

**Problem**: `Error: Your project's URL and Key are required`

**Solution**:

- Ensure `NEXT_PUBLIC_` variables are in `.env.production` before build
- Jenkins builds with `--no-cache` to force fresh builds
- Variables must be available during `npm run build`

```bash
# Verify build-time variables
echo $NEXT_PUBLIC_SUPABASE_URL
echo $NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```

#### **2. Backend Connection Refused**

**Problem**: `ECONNREFUSED 127.0.0.1:5001`

**Solution**:

- Frontend cannot reach backend if hardcoded to `localhost` in Docker
- Use `next.config.ts` to dynamically evaluate `NEXT_PUBLIC_API_URL`
- Set environment variable: `NEXT_PUBLIC_API_URL=http://65.0.117.219:5001/api`

```bash
# Verify connectivity
curl http://65.0.117.219:5001/api/health
```

#### **3. Gunicorn Worker Timeout**

**Problem**: Backend freezes with `WORKER TIMEOUT`

**Solution**:

- Raw TCP scanners open empty sockets without HTTP data
- Use multi-threaded workers: `--workers 3 --threads 4`
- Configure timeout appropriately: `--timeout 120`

#### **4. Docker Image Not Pulling**

**Problem**: `Failed to pull image from Docker Hub`

**Solution**:

- Verify Docker Hub credentials in Jenkins
- Check internet connectivity on EC2
- Ensure image exists in Docker Hub repository

```bash
# Verify image availability
docker pull mayankc1533262/stayngo-frontend:latest
```

#### **5. Terraform State Conflicts**

**Problem**: State lock or divergence

**Solution**:

```bash
# Refresh state
terraform refresh

# Unlock state (if needed)
terraform force-unlock <LOCK_ID>

# Plan before apply
terraform plan -out=tfplan
```

---

## 📞 Access Points

### **Production Deployment**

| Service     | URL                                        | Purpose                  |
| ----------- | ------------------------------------------ | ------------------------ |
| Frontend    | `http://65.0.117.219:3000`                 | StayNGo Web Application  |
| Backend API | `http://65.0.117.219:5001/api`             | REST API                 |
| Jenkins     | `http://65.0.117.219:8080`                 | CI/CD Pipeline Dashboard |
| SonarQube   | `http://65.0.117.219:9000`                 | Code Quality Dashboard   |
| Supabase    | `https://tbfhvivcykjymejpdjlm.supabase.co` | Database & Auth          |

---

## 🔮 Future Enhancements

1. **HTTPS/SSL**: Add AWS Certificate Manager + CloudFront CDN
2. **Auto-Scaling**: Implement AWS Auto Scaling Groups
3. **RDS**: Migrate from Supabase to Amazon RDS for cost optimization
4. **CloudWatch**: Add AWS CloudWatch monitoring
5. **Secrets Manager**: Use AWS Secrets Manager instead of `.env` files
6. **Backup Strategy**: Implement automated database backups
7. **Blue-Green Deployment**: Implement zero-downtime deployments
8. **Disaster Recovery**: Cross-region replication strategy

---

**Last Updated**: May 2026  
**Maintained By**: StayNGo DevOps Team

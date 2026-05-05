# 🏨 StayNGo — Complete Presentation Guide (Super Easy Language)

> **This guide explains EVERYTHING about your project in the simplest possible language. Read this and you'll be able to present confidently.**

---

## 📌 Part 1: What is StayNGo? (Project Ka Idea)

### One Line Answer:
**StayNGo is a website where patients and their families can find cheap rooms to stay near hospitals.**

### The Problem It Solves:
Imagine a person from a village goes to Tata Memorial Hospital in Mumbai for cancer treatment. The doctor says — "Come back after 5 days for your next appointment." Now this person needs a place to stay for 5 days. Hotels are too expensive. Dharamshala might be full. What does he do?

**StayNGo solves this problem.** It's like **OYO Rooms, but specifically for hospital patients who need cheap stays.**

### What Can Users Do On This Website?
- 🔍 **Search for rooms** near a specific hospital
- 💰 **Filter by budget** (only show rooms under ₹500/night)
- 📖 **Read reviews** from other patients
- 📅 **Book a room** and pay online
- 🏠 **Property owners** can list their rooms (like being a landlord on the website)

---

## 📌 Part 2: What Technologies Are Used? (Sabse Important for DevOps)

Think of building a website like building a house. You need different materials for different parts:

### The Website Itself (Application)

| Part | Technology | Simple Explanation |
|------|-----------|-------------------|
| **Front of the house** (what users see) | **Next.js** (React) | This is the pretty part — buttons, images, forms that the user clicks on. Think of it as the **paint and tiles** of a house. |
| **Back of the house** (brain/logic) | **Flask** (Python) | This is the engine. When someone clicks "Book Room", this part does the actual work — checks availability, calculates price. Think of it as the **electrical wiring and plumbing** — users don't see it, but nothing works without it. |
| **Storage room** (database) | **Supabase** (PostgreSQL) | This is where all data is stored — user accounts, room details, bookings, payments. Think of it as a **giant diary/register** where everything is written down. |

### The DevOps Part (How We Deliver & Manage The Website)

| Technology | Simple Explanation |
|-----------|-------------------|
| **Docker** 🍱 | Imagine packing your lunch in a tiffin box. No matter where you take it — office, picnic, train — the food stays the same. Docker does this for our website code. It **packs the website into a box** so it runs the same everywhere — your laptop, server, cloud. |
| **Jenkins** 🤖 | Think of Jenkins as a **robot worker** in a factory. Every time we make a change to the website code, this robot automatically: tests it, packs it, and delivers it to the server. We don't have to do anything manually. |
| **SonarQube** 🔍 | Think of this as a **spelling checker for code**. Before our code goes live, SonarQube reads it and says — "Yeh line galat hai, yeh security risk hai, yeh code duplicate hai." It catches mistakes before users see them. |
| **Terraform** 🏗️ | Imagine you want to buy a computer on Amazon. You write down what you want — "16GB RAM, 500GB storage" — and click order. Terraform does the same thing but for **cloud servers**. We write what server we need, and Terraform **automatically creates it on AWS** (Amazon's cloud). |
| **Ansible** 🔧 | After Terraform creates the server (like getting a new empty computer), Ansible is the person who **sets it up** — installs Docker, installs required software, sets passwords. Think of it as the **IT guy who sets up your new laptop on the first day of work**. |
| **AWS EC2** ☁️ | This is a **computer on rent from Amazon**. Instead of buying a physical server and keeping it in an office, we rent a computer that runs 24/7 somewhere in Amazon's data center. Our website runs on this rented computer. |
| **Docker Hub** 📦 | This is like **Google Drive but for Docker boxes**. After Jenkins packs our code into Docker boxes, it uploads them to Docker Hub. Then the AWS server downloads from Docker Hub. It's a **storage for our packed code**. |
| **Kubernetes** 👨‍💼 | Think of this as a **manager** of Docker containers. If one container crashes, Kubernetes automatically restarts it. If too many users come, it creates more containers. It's like a manager who makes sure everything runs smoothly. *(We have this as an optional setup)* |
| **GitHub** 📝 | This is where our code lives. Think of it as **Google Docs for code** — multiple people can work on it, and every change is saved with history. |

---

## 📌 Part 3: How Does The DevOps Pipeline Work? (THE MOST IMPORTANT PART)

> **This is what your presentation is really about. Understand this section thoroughly.**

### What is a CI/CD Pipeline?

CI/CD stands for:
- **CI = Continuous Integration** → Every time someone writes new code, it automatically gets checked and merged
- **CD = Continuous Deployment** → After checking, the code automatically goes live on the website

**Simple analogy:** Think of a **pizza delivery system**:
1. Customer orders pizza (Developer writes code)
2. Kitchen checks the order (SonarQube checks code quality)  
3. Chef makes the pizza (Docker builds the application)
4. Pizza is packed in a box (Docker image is created)
5. Delivery boy picks it up (Image pushed to Docker Hub)
6. Delivery boy delivers to customer's house (Code deployed to AWS server)
7. Customer eats pizza (Users see the updated website)

**All of this happens AUTOMATICALLY. That's the beauty of DevOps.**

### Step-by-Step: What Happens When We Change Code

#### Step 1: Developer Pushes Code to GitHub 📤
- Developer writes some new code (maybe adds a new feature)
- They "push" (upload) it to GitHub
- GitHub has a **webhook** (basically an alarm) that tells Jenkins — "Hey! New code came!"

#### Step 2: Jenkins Wakes Up 🤖
- Jenkins is always watching. The moment GitHub sends the alarm, Jenkins starts working
- It downloads the latest code from GitHub

#### Step 3: SonarQube Checks Code Quality 🔍
- Before doing anything, Jenkins sends the code to SonarQube
- SonarQube reads every line and checks:
  - ❌ Are there any bugs (mistakes)?
  - ❌ Are there any security problems?
  - ❌ Is any code copy-pasted (duplicated)?
  - ❌ Is the code messy or hard to read?
- If SonarQube says **"Code is bad"** → Pipeline STOPS. Nothing gets deployed.
- If SonarQube says **"Code is good"** → Pipeline continues.

#### Step 4: Docker Builds the Application 🍱
- Jenkins tells Docker: "Pack this code into containers"
- Docker creates **two boxes (images)**:
  - 📦 **Frontend box** — contains the website's look and feel (Next.js)
  - 📦 **Backend box** — contains the website's brain/logic (Flask)
- `--no-cache` flag means "make a completely fresh box, don't use any old leftovers"
- Environment variables (secret keys, database passwords) are injected during this step

#### Step 5: Push to Docker Hub 📤
- These two boxes (Docker images) are uploaded to **Docker Hub**
- Docker Hub is a public warehouse where anyone (or our server) can download them
- Image names: `mayankc1533262/stayngo-frontend` and `mayankc1533262/stayngo-backend`

#### Step 6: Deploy to AWS Server 🚀
- Jenkins connects to our AWS EC2 server using **SSH** (a secure remote connection, like TeamViewer but for servers)
- It tells the server: "Download the new boxes from Docker Hub and start running them"
- The server runs: `docker-compose up` which starts both frontend and backend

#### Step 7: Website is Live! ✅
- Frontend is available at port 3000 (the website users see)
- Backend is available at port 5001 (the API that does the work)
- The website is updated with the new code!

---

## 📌 Part 4: Infrastructure — How We Set Up The Server

### Terraform — Creating the Server (Infrastructure as Code)

**Normal way:** Log into AWS website → click "Create Server" → choose settings → click buttons

**Our way (DevOps way):** Write a file that says what server we want → run one command → server is created automatically

```
We wrote in Terraform:
"I want an Ubuntu computer on AWS,
 with 20GB storage,
 type t3.medium (medium power),
 open ports 22, 80, 3000, 5001, 8080, 9000"

One command: terraform apply
Result: Server created at IP 65.0.117.219
```

**Why is this better?**
- If the server crashes, we can recreate it in **2 minutes** with the same command
- Everything is documented in code (no "I forgot which button I clicked")
- We can create 100 servers with the same command

### Ansible — Setting Up the Server

After Terraform creates a **blank server** (like a new empty laptop), we need to install stuff on it.

**Ansible does this automatically:**
1. ✅ Install Docker
2. ✅ Install Docker Compose
3. ✅ Set up SSH keys
4. ✅ Configure Docker Hub login
5. ✅ Install kubectl (for Kubernetes)

**One command:** `ansible-playbook setup.yml` — and everything gets installed!

---

## 📌 Part 5: Docker — Containers Explained Simply

### What is Docker?

**Problem without Docker:**
- "It works on my laptop but not on the server" 😤
- Different laptops have different software versions
- Setting up a new server means installing everything from scratch

**Solution — Docker:**
- Pack your entire application + all its requirements into a **container (box)**
- This box runs the same everywhere — your laptop, your friend's laptop, AWS server
- It's like a **portable room** — wherever you put it, everything inside stays the same

### What is Docker Compose?

We have **2 containers** (frontend box + backend box). Docker Compose is a file that says:
- "Start both boxes together"
- "Frontend runs on port 3000, Backend runs on port 5001"
- "If any box crashes, restart it automatically"

It's like a **to-do list for Docker**: "Start this, then this, connect them like this."

### What is a Dockerfile?

This is a **recipe card** for making a Docker container. It says:
- Start with Ubuntu
- Install Python
- Copy my code
- Run this command

Each service (frontend and backend) has its own Dockerfile (its own recipe).

---

## 📌 Part 6: Security — How We Keep Things Safe

### 1. Security Groups (AWS Firewall)
- We only open the doors (ports) that are needed
- Port 3000 → for website
- Port 5001 → for backend API
- Port 8080 → for Jenkins dashboard
- Port 9000 → for SonarQube dashboard
- Port 22 → for SSH (remote access to server)
- All other ports are **closed** (no one can enter)

### 2. Secret Management
- Passwords and API keys are stored in **`.env` files** (not in the code)
- These files are **never uploaded to GitHub** (they stay only on the server)
- Jenkins stores Docker Hub password in its own **secret vault**
- It's like keeping your ATM PIN in your head, not written on the card

### 3. SSH Key Authentication
- We don't use passwords to log into the server
- We use **SSH keys** (a special digital key pair)
- It's like having a **unique fingerprint lock** — only our fingerprint can open the server

### 4. Database Security
- Supabase (our database) encrypts all data (even if someone steals the hard drive, they can't read it)
- Login system uses **Supabase Auth** — handles passwords, sessions, security automatically

---

## 📌 Part 7: Monitoring — How We Keep an Eye on Things

### Jenkins Dashboard (http://65.0.117.219:8080)
- Shows if the last deployment was **successful ✅ or failed ❌**
- Shows how long each deployment took
- Shows history of all past deployments
- Like a **factory monitor showing production status**

### SonarQube Dashboard (http://65.0.117.219:9000)
- Shows code health — bugs, vulnerabilities, code smells
- Like a **health checkup report for your code**
- Gives a grade: A, B, C, D, E

### Gunicorn (Backend Performance)
- Our backend runs with **3 workers and 4 threads**
- This means it can handle **multiple requests at the same time**
- Like having **3 cooks in a kitchen, each with 4 hands** — they can serve many customers simultaneously
- This also protects against attacks where someone sends fake requests to crash the server

---

## 📌 Part 8: Kubernetes (Optional Setup) — Explained Simply

We have Kubernetes as an **optional alternative** to Docker Compose.

### What Does Kubernetes Do?

Think of Docker Compose as a **small shop owner** — they manage 2-3 things themselves.

Kubernetes is like a **mall manager** — they handle hundreds of shops automatically:
- If a shop (container) closes, Kubernetes opens a new one immediately
- If too many customers come, Kubernetes opens more shops
- It distributes customers evenly across all shops (load balancing)

### Our Kubernetes Setup:
- **Frontend**: 2 copies running (if one dies, the other serves users)
- **Backend**: Configurable copies
- **Load Balancer**: Distributes traffic on port 80

---

## 📌 Part 9: The Big Picture (Everything Together)

```
Developer writes code
        ↓
   Pushes to GitHub
        ↓
GitHub tells Jenkins (webhook)
        ↓
Jenkins downloads code
        ↓
SonarQube checks quality ──→ ❌ Bad? → STOP!
        ↓ ✅ Good?
Docker builds 2 containers
        ↓
Uploads to Docker Hub
        ↓
Jenkins SSHs into AWS EC2
        ↓
EC2 downloads new containers
        ↓
Docker Compose starts everything
        ↓
🎉 Website is LIVE & updated!
```

**Infrastructure was already set up using:**
- **Terraform** → Created the AWS server
- **Ansible** → Installed Docker and tools on the server

---

## 📌 Part 10: Likely Viva/Presentation Questions & Answers

### Q1: "What is your project about?"
> "StayNGo is a website that helps patients find affordable rooms to stay near hospitals. It's like OYO but specifically for hospital patients who need cheap temporary accommodation during treatment."

### Q2: "Why did you use Docker?"
> "Docker solves the problem of 'it works on my laptop but not on the server.' It packs our application with all its requirements into a portable container that runs the same everywhere. This makes deployment consistent and reliable."

### Q3: "What is Jenkins doing in your project?"
> "Jenkins is our automation tool. Every time we push new code to GitHub, Jenkins automatically tests it with SonarQube, builds Docker containers, uploads them to Docker Hub, and deploys them to our AWS server. We don't have to do anything manually — it's fully automated."

### Q4: "What is the CI/CD pipeline?"
> "CI means Continuous Integration — code is automatically checked and merged. CD means Continuous Deployment — after checks pass, code is automatically deployed to the live server. Together, they mean that from the moment a developer writes code to the moment users see it on the website, everything happens automatically without human intervention."

### Q5: "Why Terraform?"
> "Instead of manually clicking buttons on the AWS website to create a server, we wrote a code file that describes exactly what server we need. With one command, Terraform creates it. If the server dies, we can recreate it in minutes. It's called Infrastructure as Code."

### Q6: "What is Ansible's role?"
> "After Terraform creates a blank server, Ansible installs all the required software on it — Docker, Docker Compose, and configures security settings. It's like an IT guy setting up a new laptop automatically."

### Q7: "How does SonarQube help?"
> "SonarQube is a code quality tool. It scans our code for bugs, security vulnerabilities, duplicate code, and bad practices. If the code doesn't meet quality standards, the deployment pipeline stops. This ensures only good, clean code reaches the live website."

### Q8: "What is Docker Compose?"
> "We have two Docker containers — one for frontend (the website) and one for backend (the logic). Docker Compose is a configuration file that starts both containers together, connects them to each other, and restarts them if they crash."

### Q9: "What is Kubernetes and why do you have it?"
> "Kubernetes is a container orchestration tool. It manages Docker containers at scale — automatically restarts crashed containers, scales up during high traffic, and balances load. We have it as an optional setup for when the project needs to handle more users."

### Q10: "How do you handle security?"
> "We handle security at multiple levels:
> 1. AWS Security Groups act as a firewall — only necessary ports are open
> 2. SSH key authentication — no passwords for server access
> 3. Secrets (passwords, API keys) are stored in .env files, never in code
> 4. Supabase provides encrypted database and secure authentication
> 5. SonarQube catches security vulnerabilities in code before deployment"

### Q11: "What happens if the server crashes?"
> "Since we use Infrastructure as Code (Terraform + Ansible), we can recreate the entire server from scratch in minutes. Docker images are stored on Docker Hub, so we just pull them and start. Nothing is lost because our database is on Supabase (separate cloud service) and code is on GitHub."

### Q12: "What is the difference between Docker and Kubernetes?"
> "Docker is about creating and running individual containers (boxes). Kubernetes is about managing many containers — it decides how many copies to run, restarts crashed ones, and distributes traffic. Docker is the box, Kubernetes is the warehouse manager."

### Q13: "What AWS services are you using?"
> "We use EC2 (a virtual computer in the cloud) with Ubuntu operating system, EBS (20GB storage attached to EC2), Elastic IP (a fixed public IP address), and Security Groups (firewall rules). Everything is created using Terraform."

### Q14: "What is a webhook?"
> "A webhook is like a notification system. We tell GitHub: 'Whenever someone pushes new code, send a message to Jenkins.' So Jenkins doesn't have to keep checking GitHub — GitHub tells Jenkins automatically. It's like a doorbell instead of repeatedly checking if someone is at the door."

### Q15: "What would you improve in the future?"
> "We plan to add HTTPS/SSL for secure connections, auto-scaling so the server grows automatically with more users, AWS CloudWatch for advanced monitoring, and blue-green deployment for zero-downtime updates."

---

## 📌 Quick Cheat Sheet for Presentation

| When Ma'am Asks About... | Say This... |
|--------------------------|-------------|
| Project idea | "Affordable rooms near hospitals for patients" |
| Docker | "Packs code in portable boxes that run same everywhere" |
| Jenkins | "Robot that automatically tests, builds, and deploys code" |
| SonarQube | "Code quality checker — like spell check for code" |
| Terraform | "Creates cloud servers using code, not clicking buttons" |
| Ansible | "Sets up software on server automatically — like IT guy" |
| CI/CD | "Code goes from developer to live website automatically" |
| AWS EC2 | "A computer rented from Amazon that runs 24/7 in cloud" |
| Docker Hub | "Cloud storage where Docker images are uploaded/downloaded" |
| Kubernetes | "Manager that handles many containers, auto-restarts, scales" |
| Security | "Firewall, SSH keys, encrypted DB, secrets not in code" |
| Webhook | "GitHub doorbell that rings Jenkins when code changes" |

---

> [!TIP]
> **Pro Tip for Presentation:** Speak confidently. If Ma'am asks something you don't know, say: *"That's a great question. In our current implementation, we focused on [whatever you know], and that's something we can explore in future iterations."* — This sounds professional and buys you time! 😄

> [!IMPORTANT]
> **Remember the key DevOps principle to mention:** *"The goal of DevOps is to make the process of developing, testing, and deploying software faster, more reliable, and fully automated. Instead of doing things manually, we use tools to automate every step."*

---

**Good luck with your presentation! 🚀 You've got this! 💪**

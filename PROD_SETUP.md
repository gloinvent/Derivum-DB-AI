# Production Setup Guide

## Problem
The app fails on production with:
```
DB error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed
```

This means **environment variables are NOT set** on your production server.

---

## Solution: Set Environment Variables on EC2

### **Step 1: SSH into your production server**
```bash
ssh -i your-key.pem ubuntu@your-prod-server.com
```

### **Step 2: Create environment file** (choose ONE method below)

#### **Method A: Create `/opt/fetcherio/.env` (RECOMMENDED)**
```bash
sudo mkdir -p /opt/fetcherio
sudo nano /opt/fetcherio/.env
```

Paste these (fill in ACTUAL values):
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
LLM_MODEL=gpt-4o
HOST=trinity-prod.c3maq4i02brk.ap-south-1.rds.amazonaws.com
PORT=5432
DATABASE=deri_data_prod
USER=gloify_sid
PASSWORD=your-actual-db-password
V1_API_KEY=your-random-key-here
V1_PLAN_TIER=pro
```

Set permissions:
```bash
sudo chmod 600 /opt/fetcherio/.env
sudo chown ubuntu:ubuntu /opt/fetcherio/.env
```

---

#### **Method B: Using systemd environment file**
```bash
sudo nano /etc/systemd/system/fetcherio.env
```

Add:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
HOST=trinity-prod.c3maq4i02brk.ap-south-1.rds.amazonaws.com
PORT=5432
DATABASE=deri_data_prod
USER=gloify_sid
PASSWORD=your-actual-db-password
LLM_MODEL=gpt-4o
V1_API_KEY=your-random-key-here
```

---

#### **Method C: Using AWS Systems Manager Parameter Store (MOST SECURE)**
```bash
# Store each secret
aws ssm put-parameter --name /fetcherio/openai-api-key --value "sk-proj-..." --type SecureString
aws ssm put-parameter --name /fetcherio/db-password --value "your-password" --type SecureString
```

Then in your systemd service, load from Parameter Store using a startup script.

---

### **Step 3: Create/Update systemd service**

```bash
sudo nano /etc/systemd/system/fetcherio.service
```

**Method A or B (using .env file):**
```ini
[Unit]
Description=Fetcherio FastAPI App
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/fetcherio
EnvironmentFile=/opt/fetcherio/.env

ExecStart=/home/ubuntu/fetcherio/venv/bin/python run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Method C (using Parameter Store):**
Create `/home/ubuntu/fetcherio/load-secrets.sh`:
```bash
#!/bin/bash
export OPENAI_API_KEY=$(aws ssm get-parameter --name /fetcherio/openai-api-key --query 'Parameter.Value' --output text)
export HOST=trinity-prod.c3maq4i02brk.ap-south-1.rds.amazonaws.com
export PORT=5432
export DATABASE=deri_data_prod
export USER=gloify_sid
export PASSWORD=$(aws ssm get-parameter --name /fetcherio/db-password --query 'Parameter.Value' --output text)
export LLM_MODEL=gpt-4o
/home/ubuntu/fetcherio/venv/bin/python run.py
```

Then update service:
```ini
ExecStart=/home/ubuntu/fetcherio/load-secrets.sh
```

---

### **Step 4: Enable and start the service**

```bash
sudo systemctl daemon-reload
sudo systemctl enable fetcherio
sudo systemctl start fetcherio
```

### **Step 5: Verify it's running**

```bash
sudo systemctl status fetcherio
sudo journalctl -u fetcherio -f  # View logs
```

Should see:
```
listening on 0.0.0.0:8000
Config loaded
DB: trinity-prod.c3maq4i02brk.ap-south-1.rds.amazonaws.com:5432/deri_data_prod
```

---

## Troubleshooting

**Still getting socket error?**
```bash
# Check if env vars are loaded
systemctl show-environment | grep OPENAI_API_KEY

# Check service logs
sudo journalctl -u fetcherio -n 50
```

**Port 8000 already in use?**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**DB connection still timing out?**
1. Check AWS Security Group allows port 5432 from your EC2 instance
2. Verify credentials are correct: `echo $PASSWORD`
3. Test connection: `psql -h $HOST -U $USER -d $DATABASE`

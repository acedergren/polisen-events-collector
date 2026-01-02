# DevOps Quick Start Guide
**Immediate Actions for Week 1 Implementation**

---

## Overview
This guide provides step-by-step instructions for implementing the most critical DevOps improvements in the first week. Focus on high-impact, low-risk changes that unlock downstream improvements.

---

## Phase 1: Add Testing Framework (2 hours)

### Step 1: Create test directory structure
```bash
cd /home/alex/projects/polisen-events-collector
mkdir -p tests
touch tests/__init__.py
touch tests/test_collect_events.py
touch tests/test_secrets_manager.py
```

### Step 2: Update requirements.txt
```bash
# Add to requirements.txt
requests>=2.31.0
oci>=2.119.0
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
```

### Step 3: Create test_collect_events.py
```python
# tests/test_collect_events.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from collect_events import PolisenCollector

@pytest.fixture
def mock_oci_config():
    """Mock OCI configuration"""
    return {
        "region": "eu-stockholm-1",
        "user": "test_user",
        "tenancy": "test_tenancy"
    }

@pytest.fixture
def mock_oci_client(mock_oci_config):
    """Mock OCI Object Storage client"""
    client = MagicMock()
    return client

class TestPolisenCollector:
    """Test suite for PolisenCollector"""

    @patch('collect_events.get_oci_config_from_vault')
    @patch('collect_events.oci.object_storage.ObjectStorageClient')
    def test_init_with_vault(self, mock_client_class, mock_vault_config):
        """Test initialization with vault"""
        mock_vault_config.return_value = {"region": "eu-stockholm-1"}
        collector = PolisenCollector(use_vault=True)
        assert collector is not None
        mock_vault_config.assert_called_once()

    @patch('collect_events.get_oci_config_from_vault')
    @patch('collect_events.requests.get')
    def test_fetch_events_success(self, mock_get, mock_vault_config):
        """Test successful event fetching"""
        mock_vault_config.return_value = {"region": "eu-stockholm-1"}
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": 1, "name": "Test Event 1"},
            {"id": 2, "name": "Test Event 2"}
        ]
        mock_get.return_value = mock_response

        with patch('collect_events.oci.object_storage.ObjectStorageClient'):
            collector = PolisenCollector(use_vault=True)
            events = collector.fetch_events()
            assert len(events) == 2
            assert events[0]["id"] == 1

    @patch('collect_events.get_oci_config_from_vault')
    @patch('collect_events.requests.get')
    def test_fetch_events_http_error(self, mock_get, mock_vault_config):
        """Test HTTP error handling"""
        mock_vault_config.return_value = {"region": "eu-stockholm-1"}
        mock_get.side_effect = Exception("HTTP 429 - Too Many Requests")

        with patch('collect_events.oci.object_storage.ObjectStorageClient'):
            collector = PolisenCollector(use_vault=True)
            with pytest.raises(Exception):
                collector.fetch_events()

    @patch('collect_events.get_oci_config_from_vault')
    @patch('collect_events.oci.object_storage.ObjectStorageClient')
    def test_deduplicate_events(self, mock_client_class, mock_vault_config):
        """Test event deduplication logic"""
        mock_vault_config.return_value = {"region": "eu-stockholm-1"}
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        with patch('collect_events.oci.object_storage.ObjectStorageClient', return_value=mock_client):
            collector = PolisenCollector(use_vault=True)
            # Test deduplication
            last_seen = {1, 2, 3}
            new_events = [
                {"id": 2, "name": "Duplicate"},
                {"id": 4, "name": "New Event"}
            ]
            unique_events = [e for e in new_events if e["id"] not in last_seen]
            assert len(unique_events) == 1
            assert unique_events[0]["id"] == 4

class TestSecretsManager:
    """Test suite for SecretsManager"""

    @patch('secrets_manager.oci.auth.signers.InstancePrincipalsSecurityTokenSigner')
    def test_init_with_instance_principal(self, mock_signer):
        """Test initialization with instance principal"""
        from secrets_manager import SecretsManager
        with patch('secrets_manager.oci.secrets.SecretsClient'):
            sm = SecretsManager(use_instance_principal=True)
            assert sm is not None

    @patch('secrets_manager.oci.config.from_file')
    def test_init_with_config_file(self, mock_config):
        """Test initialization with config file"""
        from secrets_manager import SecretsManager
        mock_config.return_value = {"region": "eu-frankfurt-1"}
        with patch('secrets_manager.oci.secrets.SecretsClient'):
            with patch('secrets_manager.oci.vault.VaultsClient'):
                sm = SecretsManager(use_instance_principal=False)
                assert sm is not None
                mock_config.assert_called_once()
```

### Step 4: Update CI workflow with tests
```yaml
# .github/workflows/ci.yml - Add test job
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9.19'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ \
          --cov=collect_events \
          --cov=secrets_manager \
          --cov-report=xml \
          --cov-report=html \
          --cov-report=term \
          --cov-fail-under=80 \
          -v

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        fail_ci_if_error: true

    - name: Archive test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: htmlcov/
```

---

## Phase 2: Create Dockerfile (2 hours)

### Step 1: Create multi-stage Dockerfile
```dockerfile
# Dockerfile

# Stage 1: Builder
FROM python:3.9.19-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.9.19-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r collector && useradd -r -g collector collector

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/collector/.local
ENV PATH=/home/collector/.local/bin:$PATH

# Copy application code
COPY --chown=collector:collector collect_events.py .
COPY --chown=collector:collector secrets_manager.py .

# Create log directory
RUN mkdir -p logs && chown -R collector:collector logs

# Switch to non-root user
USER collector

# Health check - can be overridden
HEALTHCHECK --interval=5m --timeout=30s --start-period=1m --retries=3 \
    CMD python -c "import os; import sys; sys.exit(0 if os.path.exists('logs/polisen-collector.log') else 1)" || exit 1

# Set entrypoint
ENTRYPOINT ["python3"]
CMD ["collect_events.py"]

# Metadata
LABEL org.opencontainers.image.title="Polisen Events Collector"
LABEL org.opencontainers.image.description="Swedish Police events collection service"
LABEL org.opencontainers.image.authors="alex@example.com"
LABEL org.opencontainers.image.source="https://github.com/user/polisen-events-collector"
```

### Step 2: Create .dockerignore
```
# .dockerignore
.git
.github
.venv
venv
env
__pycache__
*.pyc
*.pyo
*.egg-info
.pytest_cache
.coverage
htmlcov
logs/*.log
.env
.env.*
.oci
*.pem
*.key
config
.serena
.idea
.vscode
*.swp
*.swo
*~
.DS_Store
*.md
tests/
```

### Step 3: Build and test locally
```bash
# Build image
docker build -t polisen-collector:latest .

# Test image
docker run --rm polisen-collector:latest --version

# Check image size
docker images | grep polisen-collector

# Expected: ~200-250MB (slim Python image)
```

### Step 4: Add Docker build to CI/CD
```yaml
# .github/workflows/ci.yml - Add docker job
  docker:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha
          type=ref,event=branch

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

---

## Phase 3: Fix Deployment Scripts (1.5 hours)

### Step 1: Create improved install-scheduler.sh
```bash
#!/bin/bash
# install-scheduler.sh - Enhanced version with validation

set -e

echo "=== Polisen Events Collector - Scheduler Installation ==="
echo

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="polisen-collector"
PYTHON_EXECUTABLE="$(which python3)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validation functions
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        return 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_info "Found Python: $PYTHON_VERSION"
    return 0
}

check_dependencies() {
    log_info "Checking Python dependencies..."
    python3 -c "import requests; import oci" 2>/dev/null || {
        log_error "Required packages not installed"
        log_info "Run: pip3 install -r requirements.txt"
        return 1
    }
    log_info "All dependencies installed"
    return 0
}

check_oci_config() {
    log_info "Checking OCI configuration..."
    python3 -c "from secrets_manager import SecretsManager; sm = SecretsManager()" 2>/dev/null || {
        log_error "OCI configuration invalid"
        log_info "Run: export OCI_PROFILE=DEFAULT"
        return 1
    }
    log_info "OCI configuration valid"
    return 0
}

validate_systemd_files() {
    log_info "Validating systemd files..."
    [ -f "$SCRIPT_DIR/polisen-collector.service" ] || {
        log_error "Service file not found"
        return 1
    }
    [ -f "$SCRIPT_DIR/polisen-collector.timer" ] || {
        log_error "Timer file not found"
        return 1
    }
    log_info "Systemd files found"
    return 0
}

install_systemd() {
    log_info "Installing systemd timer..."

    # Validate files first
    validate_systemd_files || return 1

    # Create a temporary copy with proper path substitution
    TEMP_SERVICE="/tmp/polisen-collector.service.tmp"
    TEMP_TIMER="/tmp/polisen-collector.timer.tmp"

    # Substitute actual paths
    sed "s|ExecStart=.*|ExecStart=$PYTHON_EXECUTABLE $SCRIPT_DIR/collect_events.py|" \
        "$SCRIPT_DIR/polisen-collector.service" > "$TEMP_SERVICE"

    cp "$SCRIPT_DIR/polisen-collector.timer" "$TEMP_TIMER"

    # Copy to systemd directory
    sudo cp "$TEMP_SERVICE" /etc/systemd/system/polisen-collector.service
    sudo cp "$TEMP_TIMER" /etc/systemd/system/polisen-collector.timer

    # Set proper permissions
    sudo chmod 644 /etc/systemd/system/polisen-collector.service
    sudo chmod 644 /etc/systemd/system/polisen-collector.timer

    # Clean up
    rm -f "$TEMP_SERVICE" "$TEMP_TIMER"

    # Reload systemd
    sudo systemctl daemon-reload

    # Verify installation
    if ! systemctl list-unit-files | grep -q "polisen-collector"; then
        log_error "Failed to install systemd files"
        return 1
    fi

    log_info "Systemd files installed"
    return 0
}

enable_and_start() {
    log_info "Enabling and starting timer..."

    sudo systemctl enable polisen-collector.timer || {
        log_error "Failed to enable timer"
        return 1
    }

    sudo systemctl start polisen-collector.timer || {
        log_error "Failed to start timer"
        return 1
    }

    # Wait for systemd to process
    sleep 2

    # Verify status
    if ! sudo systemctl is-active --quiet polisen-collector.timer; then
        log_error "Timer is not active"
        sudo systemctl status polisen-collector.timer
        return 1
    fi

    log_info "Timer enabled and started successfully"
    return 0
}

verify_installation() {
    log_info "Verifying installation..."

    # Check timer status
    TIMER_STATUS=$(sudo systemctl is-active polisen-collector.timer)
    if [ "$TIMER_STATUS" != "active" ]; then
        log_error "Timer is not active (status: $TIMER_STATUS)"
        return 1
    fi

    # Check next scheduled run
    NEXT_RUN=$(systemctl list-timers polisen-collector.timer 2>/dev/null | tail -1 | awk '{print $1}')
    log_info "Next scheduled run: $NEXT_RUN"

    log_info "Installation verified successfully"
    return 0
}

# Main execution
main() {
    log_info "Starting installation with pre-flight checks..."
    echo

    # Pre-flight checks
    check_python || exit 1
    check_dependencies || exit 1
    check_oci_config || exit 1
    echo

    # Detect and install
    if command -v systemctl &> /dev/null; then
        log_info "systemd detected - Installing systemd timer"
        install_systemd || exit 1
        enable_and_start || exit 1
        verify_installation || exit 1
    else
        log_error "systemd not found on this system"
        log_info "Cron installation not yet implemented in this version"
        exit 1
    fi

    echo
    log_info "Installation complete!"
    echo
    echo "Management commands:"
    echo "  Status:   sudo systemctl status polisen-collector.timer"
    echo "  Stop:     sudo systemctl stop polisen-collector.timer"
    echo "  Start:    sudo systemctl start polisen-collector.timer"
    echo "  Logs:     sudo journalctl -u polisen-collector.service -f"
    echo "  Manual:   sudo systemctl start polisen-collector.service"
    echo
    echo "Next run will occur within 30 minutes"
}

main "$@"
```

### Step 2: Fix polisen-collector.service with health checks
```ini
# polisen-collector.service - Enhanced version

[Unit]
Description=Polisen Events Collector
Documentation=https://polisen.se/om-polisen/om-webbplatsen/oppna-data/api-over-polisens-handelser/
After=network-online.target
Wants=network-online.target
PartOf=polisen-collector.timer

[Service]
Type=oneshot
User=alex
Group=alex
WorkingDirectory=/home/alex/projects/polisen-events-collector

# Use environment variable for flexibility
ExecStart=/usr/bin/python3 /home/alex/projects/polisen-events-collector/collect_events.py

# Logging with proper redirection
StandardOutput=append:/home/alex/projects/polisen-events-collector/logs/polisen-collector.log
StandardError=append:/home/alex/projects/polisen-events-collector/logs/polisen-collector.log

# Restart policy
Restart=on-failure
RestartSec=300
StartLimitIntervalSec=3600
StartLimitBurst=5

# Timeout after 5 minutes (API calls should not take this long)
TimeoutStartSec=300

# Security hardening
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Step 3: Create health check script
```bash
#!/bin/bash
# health-check.sh - Verify scheduler and application health

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/polisen-collector.log"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check functions
check_timer() {
    echo -n "Checking systemd timer... "
    if sudo systemctl is-active --quiet polisen-collector.timer; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        sudo systemctl status polisen-collector.timer
        return 1
    fi
}

check_logs() {
    echo -n "Checking log file... "
    if [ -f "$LOG_FILE" ]; then
        echo -e "${GREEN}OK${NC}"
        echo "Recent logs:"
        tail -5 "$LOG_FILE"
        return 0
    else
        echo -e "${YELLOW}NOT FOUND${NC}"
        return 1
    fi
}

check_last_run() {
    echo -n "Checking last successful run... "
    if grep -q "Stored.*events" "$LOG_FILE" 2>/dev/null; then
        LAST_RUN=$(grep "Stored.*events" "$LOG_FILE" | tail -1)
        echo -e "${GREEN}OK${NC}"
        echo "Last run: $LAST_RUN"
        return 0
    else
        echo -e "${YELLOW}NO SUCCESSFUL RUNS${NC}"
        return 1
    fi
}

check_python() {
    echo -n "Checking Python installation... "
    if python3 --version > /dev/null 2>&1; then
        VERSION=$(python3 --version)
        echo -e "${GREEN}OK${NC} ($VERSION)"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        return 1
    fi
}

check_dependencies() {
    echo -n "Checking Python dependencies... "
    if python3 -c "import requests; import oci" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo "Run: pip3 install -r requirements.txt"
        return 1
    fi
}

# Main
echo "=== Polisen Collector Health Check ==="
echo

check_timer || {
    echo -e "${RED}CRITICAL: Timer is not running${NC}"
}

check_python
check_dependencies
check_logs
check_last_run

echo
echo "=== Health Check Complete ==="
```

Make it executable:
```bash
chmod +x health-check.sh
```

---

## Phase 4: Update requirements.txt (30 min)

```bash
# requirements.txt - Updated with test dependencies
requests>=2.31.0
oci>=2.119.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-timeout>=2.1.0

# Code quality (used in CI)
flake8>=6.1.0
pylint>=3.0.0
black>=23.12.0

# Security scanning (used in CI)
bandit>=1.7.5
safety>=2.3.5
```

---

## Phase 5: Update CI/CD Workflow (1 hour)

Create complete updated workflow file:

```yaml
# .github/workflows/ci.yml - Complete updated version

name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run security scan daily at 2 AM UTC
    - cron: '0 2 * * *'

env:
  PYTHON_VERSION: '3.9.19'
  REGISTRY: ghcr.io

jobs:
  lint:
    runs-on: ubuntu-latest
    name: Lint & Code Quality
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pylint black
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

    - name: Check formatting with Black
      run: black --check --diff .

    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

    - name: Lint with pylint
      run: |
        pylint collect_events.py secrets_manager.py --exit-zero --disable=all \
          --enable=syntax-error,undefined-variable,unused-import

  test:
    runs-on: ubuntu-latest
    name: Unit Tests
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests with coverage
      run: |
        pytest tests/ \
          --cov=collect_events \
          --cov=secrets_manager \
          --cov-report=xml \
          --cov-report=html \
          --cov-report=term \
          --cov-fail-under=80 \
          -v --tb=short

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        fail_ci_if_error: true

    - name: Archive test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: coverage-report
        path: htmlcov/

  security:
    runs-on: ubuntu-latest
    name: Security Scanning
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

    - name: Security scan with bandit
      run: |
        bandit -r collect_events.py secrets_manager.py \
          -f json -o bandit-report.json || true
        bandit -r collect_events.py secrets_manager.py --exit-zero

    - name: Check dependencies for vulnerabilities
      run: |
        safety check --json --output json > safety-report.json || true
        safety check --exit-code 0

    - name: Upload security reports
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json

  docker:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    name: Build Docker Image
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ github.repository }}
        tags: |
          type=sha,format=short
          type=ref,event=branch
          type=semver,pattern={{version}},enable=${{ startsWith(github.ref, 'refs/tags/') }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  results:
    runs-on: ubuntu-latest
    name: Test Summary
    if: always()
    needs: [lint, test, security]
    steps:
    - name: Lint status
      run: echo "Lint: ${{ needs.lint.result }}"
    - name: Test status
      run: echo "Tests: ${{ needs.test.result }}"
    - name: Security status
      run: echo "Security: ${{ needs.security.result }}"
```

---

## Step-by-Step Execution Guide

### Day 1: Testing & Coverage
```bash
# 1. Create test directory
mkdir -p tests
touch tests/__init__.py

# 2. Create test files (copy from Phase 1 above)
# 3. Update requirements.txt
# 4. Run tests locally
pytest tests/ --cov=collect_events --cov=secrets_manager --cov-fail-under=80

# 5. Verify 80%+ coverage
# 6. Update CI workflow - add test job
```

### Day 2: Containerization
```bash
# 1. Create Dockerfile (copy from Phase 2)
# 2. Create .dockerignore
# 3. Build locally
docker build -t polisen-collector:test .

# 4. Test Docker image
docker run --rm polisen-collector:test --help

# 5. Check image size
docker images | grep polisen

# 6. Add Docker build job to CI
```

### Day 3: Deployment Scripts
```bash
# 1. Backup current scripts
cp install-scheduler.sh install-scheduler.sh.bak
cp polisen-collector.service polisen-collector.service.bak

# 2. Replace with improved versions (Phase 3)
# 3. Test locally
./install-scheduler.sh --dry-run  # (implement --dry-run flag)

# 4. Run health check
./health-check.sh

# 5. Verify no breaking changes
```

### Day 4-5: Testing & Refinement
```bash
# 1. Run full test suite
pytest tests/ -v --cov

# 2. Build Docker image
docker build -t polisen-collector:latest .

# 3. Test GitHub Actions
# Push to feature branch and verify workflow

# 4. Resolve any issues
# 5. Merge to main branch
```

---

## Validation Checklist

### Week 1 Completion Criteria
- [ ] Tests written (5+ test functions minimum)
- [ ] Code coverage >= 80%
- [ ] Dockerfile builds successfully
- [ ] Docker image runs without errors
- [ ] Deployment scripts validate input
- [ ] Health checks return accurate status
- [ ] CI pipeline passes all jobs
- [ ] No critical security issues in reports
- [ ] All changes documented in commit messages

### Success Metrics
- [ ] Test execution in CI/CD
- [ ] Code coverage reports generated
- [ ] Container image available in registry
- [ ] Deployment automation working
- [ ] Health checks functional
- [ ] Documentation updated

---

## Commands Reference

```bash
# Testing
pytest tests/ --cov --cov-fail-under=80 -v
pytest tests/test_collect_events.py::TestPolisenCollector::test_init_with_vault -v

# Docker
docker build -t polisen-collector:latest .
docker run --rm polisen-collector:latest
docker run --rm polisen-collector:latest --help
docker image inspect polisen-collector:latest

# GitHub Actions
# View logs: https://github.com/user/polisen-events-collector/actions
# Trigger workflow: Push to main branch
git push origin main

# Systemd (after installation)
sudo systemctl status polisen-collector.timer
sudo systemctl start polisen-collector.service
sudo journalctl -u polisen-collector.service -f
systemctl list-timers polisen-collector.timer

# Health check
./health-check.sh

# Installation
./install-scheduler.sh
```

---

## Troubleshooting

### Tests fail with import errors
```bash
# Solution: Ensure dependencies installed
pip install -r requirements.txt
pip install -e .  # Install package in development mode
```

### Docker build fails
```bash
# Solution: Check Python version and dependencies
docker build --progress=plain -t polisen-collector:test .
docker run --rm -it polisen-collector:test /bin/bash  # Interactive debugging
```

### CI workflow timeout
```bash
# Solution: Increase timeout or cache dependencies
# Docker build cache should speed up subsequent builds
# Ensure workflow doesn't run unnecessary jobs
```

### Systemd service fails to start
```bash
# Solution: Check logs
sudo journalctl -u polisen-collector.service -n 50
sudo systemctl status polisen-collector.service

# Verify permissions
ls -la /etc/systemd/system/polisen-collector.*
ls -la /home/alex/projects/polisen-events-collector/logs/
```

---

## Next Steps (Week 2-3)

After completing Week 1, proceed with:
1. Terraform modules for infrastructure automation
2. OCI monitoring integration
3. Semantic versioning implementation
4. Advanced deployment strategies

See `CI_CD_DEVOPS_ASSESSMENT.md` for detailed Week 2-3 roadmap.

---

**Estimated Completion Time:** 24-30 hours of implementation
**Risk Level:** LOW
**Impact:** HIGH - Unlocks all downstream DevOps improvements

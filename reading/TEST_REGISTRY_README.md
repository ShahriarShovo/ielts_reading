# Test Registry System - Complete Implementation

## 🎯 Overview

The **Test Registry System** is a comprehensive solution that solves the current test ID mismatch issues and provides a robust foundation for intelligent test management. It acts as a "phone book" for all reading tests, ensuring no orphaned test IDs and providing load balancing across available tests.

## 🚀 Key Benefits

### ✅ **Solves Current Problems**

- **No More Orphaned Test IDs**: Ensures all test IDs in exam sessions actually exist
- **Intelligent Test Selection**: Load balancing and rotation strategies
- **Automatic Validation**: Continuous monitoring and consistency checks
- **Performance Optimization**: Caching and efficient database queries

### ✅ **Future-Ready Features**

- **A/B Testing Support**: Different test selection strategies
- **Adaptive Difficulty**: Personalized test selection based on student level
- **Analytics & Monitoring**: Comprehensive health reports and usage statistics
- **Multi-Tenant Support**: Organization-specific test management
- **Premium Features**: Featured tests and advanced categorization

## 📁 File Structure

```
ielts_reading/core/reading/
├── models/
│   ├── test_registry.py              # TestRegistry model with full documentation
│   └── __init__.py                   # Updated to include TestRegistry
├── services/
│   ├── test_registry_service.py      # Service layer for business logic
│   └── __init__.py                   # Service package exports
├── management/
│   └── commands/
│       └── setup_test_registry.py    # Setup command with detailed logging
├── migrations/
│   └── 0002_create_test_registry.py  # Database migration with indexes
└── TEST_REGISTRY_README.md           # This documentation file
```

## 🛠️ Installation & Setup

### Step 1: Run Migration

```bash
# Navigate to the ielts_reading core directory
cd ielts_reading/core

# Run the migration to create the test_registry table
python manage.py migrate
```

### Step 2: Set Up Test Registry

```bash
# Run the setup command to register all existing tests
python manage.py setup_test_registry

# For detailed output with statistics
python manage.py setup_test_registry --verbose

# To force re-registration of all tests
python manage.py setup_test_registry --force

# To only validate consistency without registering
python manage.py setup_test_registry --validate-only
```

### Step 3: Verify Setup

```bash
# Check the health of the system
python manage.py setup_test_registry --health-report
```

## 🐳 Docker Setup (Recommended for Production)

### **Development Docker Setup**

#### **Simple Docker Compose**

Create `docker-compose.yml` in your project root:

```yaml
version: "3.8"

services:
  ielts_reading:
    build: .
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ielts_reading
      - DJANGO_SETTINGS_MODULE=core.settings
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "
        echo 'Waiting for database...' &&
        python manage.py check --database default &&
        echo 'Running migrations...' &&
        python manage.py migrate &&
        echo 'Setting up TestRegistry...' &&
        python manage.py setup_test_registry &&
        echo 'Checking health...' &&
        python manage.py setup_test_registry --health-report &&
        echo 'Starting server...' &&
        python manage.py runserver 0.0.0.0:8002
      "

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=ielts_reading
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d ielts_reading"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

**Run with Docker:**

```bash
# Build and start services
docker-compose up --build

# Check logs
docker-compose logs ielts_reading

# Manual setup (if needed)
docker-compose exec ielts_reading python manage.py setup_test_registry

# Check health
docker-compose exec ielts_reading python manage.py setup_test_registry --health-report
```

### **Production Docker Setup**

#### **Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Starting ielts_reading service..."\n\
echo "Waiting for database..."\n\
while ! python manage.py check --database default 2>&1; do\n\
  sleep 1\n\
done\n\
echo "Running migrations..."\n\
python manage.py migrate\n\
echo "Setting up TestRegistry..."\n\
python manage.py setup_test_registry\n\
echo "Checking health..."\n\
python manage.py setup_test_registry --health-report\n\
echo "Starting server..."\n\
python manage.py runserver 0.0.0.0:8002' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python manage.py setup_test_registry --health-report

# Expose port
EXPOSE 8002

# Start application
ENTRYPOINT ["/app/entrypoint.sh"]
```

#### **Production Docker Compose**

Create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  ielts_reading:
    build: .
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ielts_reading
      - DJANGO_SETTINGS_MODULE=core.settings
      - DEBUG=False
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=ielts_reading
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

**Run Production:**

```bash
# Start production services
docker-compose -f docker-compose.prod.yml up --build -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs ielts_reading
```

### **Advanced Docker Setup with Entrypoint Script**

#### **Entrypoint Script**

Create `entrypoint.sh`:

```bash
#!/bin/bash

echo "Starting ielts_reading service..."

# Wait for database to be ready
echo "Waiting for database..."
while ! python manage.py check --database default 2>&1; do
  sleep 1
done

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Setup TestRegistry
echo "Setting up TestRegistry..."
python manage.py setup_test_registry

# Check health
echo "Checking system health..."
python manage.py setup_test_registry --health-report

# Start the application
echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8002
```

#### **Updated Dockerfile with Entrypoint**

```dockerfile
FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y postgresql-client
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and entrypoint
COPY . .
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python manage.py setup_test_registry --health-report

EXPOSE 8002
ENTRYPOINT ["/app/entrypoint.sh"]
```

**Run with Entrypoint:**

```bash
# Build and run
docker-compose up --build

# The entrypoint script automatically handles:
# 1. Database connection check
# 2. Migration
# 3. TestRegistry setup
# 4. Health check
# 5. Server start
```

### **Docker Commands Summary**

#### **Development Commands**

```bash
# Start development environment
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs ielts_reading

# Access container shell
docker-compose exec ielts_reading bash

# Manual TestRegistry setup
docker-compose exec ielts_reading python manage.py setup_test_registry

# Check health
docker-compose exec ielts_reading python manage.py setup_test_registry --health-report
```

#### **Production Commands**

```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up --build -d

# Stop production services
docker-compose -f docker-compose.prod.yml down

# View production logs
docker-compose -f docker-compose.prod.yml logs ielts_reading

# Check production status
docker-compose -f docker-compose.prod.yml ps

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

#### **Troubleshooting Docker**

```bash
# Check container health
docker-compose ps

# View detailed logs
docker-compose logs --tail=100 ielts_reading

# Rebuild without cache
docker-compose build --no-cache

# Remove all containers and volumes
docker-compose down -v

# Check database connection
docker-compose exec ielts_reading python manage.py check --database default
```

### **Docker Environment Variables**

#### **Required Environment Variables**

```bash
# Database configuration
DATABASE_URL=postgresql://user:pass@db:5432/ielts_reading

# Django settings
DJANGO_SETTINGS_MODULE=core.settings

# Debug mode (set to False for production)
DEBUG=False
```

#### **Optional Environment Variables**

```bash
# Logging level
LOG_LEVEL=INFO

# Cache configuration
CACHE_URL=redis://cache:6379/0

# Static files
STATIC_URL=/static/
MEDIA_URL=/media/
```

### **Docker Benefits**

#### **✅ Automatic Setup**

- TestRegistry is automatically set up when container starts
- No manual intervention required
- Consistent setup across all environments

#### **✅ Health Monitoring**

- Built-in health checks ensure system is working
- Automatic restart on failure
- Easy monitoring and alerting

#### **✅ Scalability**

- Easy to deploy multiple instances
- Load balancing ready
- Container orchestration support

#### **✅ Environment Consistency**

- Same setup in development and production
- No "works on my machine" issues
- Reproducible deployments

## 🔧 How It Works

### 1. **TestRegistry Model** (`models/test_registry.py`)

```python
# Core fields for test management
test_id = models.UUIDField(primary_key=True)  # Links to ReadingTest.test_id
test_name = models.CharField(max_length=255)  # Human-readable name
organization_id = models.IntegerField()       # Multi-tenant support
is_active = models.BooleanField(default=True) # Availability control

# Usage tracking for load balancing
usage_count = models.IntegerField(default=0)  # How many times used
last_used = models.DateTimeField(auto_now=True) # When last used

# Future-ready fields
test_category = models.CharField(max_length=50, default='Academic')
difficulty_level = models.CharField(max_length=20, default='Medium')
target_band_score = models.CharField(max_length=10, default='7.0')
rotation_priority = models.IntegerField(default=0)
```

### 2. **TestRegistryService** (`services/test_registry_service.py`)

```python
# Intelligent test selection
test = TestRegistryService.get_best_test_for_organization(
    organization_id=1,
    strategy='balanced'  # 'balanced', 'round_robin', 'random'
)

# Automatic registration
TestRegistryService.register_new_test(reading_test)

# Health monitoring
health = TestRegistryService.get_registry_health_report()
```

### 3. **Integration with Random Questions** (`views/create_exam.py`)

```python
# Old random selection (problematic)
random_reading = random.sample(tests_with_passages, count)

# New intelligent selection (robust)
selected_tests = TestRegistryService.integrate_with_random_questions(
    organization_id=organization_id,
    count=count
)
```

## 📊 Monitoring & Health Checks

### Health Report Structure

```python
{
    'status': 'Excellent',           # Excellent/Good/Fair/Poor
    'health_score': 95,              # 0-100 score
    'timestamp': datetime.now(),
    'statistics': {
        'total_tests': 10,
        'active_tests': 8,
        'inactive_tests': 2,
        'featured_tests': 1,
        'avg_usage': 15.5
    },
    'consistency': {
        'orphaned_registry_entries': [],
        'unregistered_tests': [],
        'deactivated_count': 0
    },
    'recommendations': [
        "System is healthy and ready for use"
    ]
}
```

### Health Score Calculation

- **100 points**: Perfect system
- **-20 points**: Orphaned registry entries
- **-10 points**: Unregistered tests
- **-50 points**: No active tests (critical)
- **-20 points**: Less than 3 active tests (warning)

## 🔄 Test Selection Strategies

### 1. **Balanced Strategy** (Default)

```python
# Selects tests with lowest usage count first
# Ensures even distribution across all available tests
test = TestRegistry.get_available_test(organization_id, strategy='balanced')
```

### 2. **Round Robin Strategy**

```python
# Selects the oldest used test first
# Ensures all tests get used in rotation
test = TestRegistry.get_available_test(organization_id, strategy='round_robin')
```

### 3. **Random Strategy**

```python
# Selects any available test randomly
# Provides variety but may not balance load
test = TestRegistry.get_available_test(organization_id, strategy='random')
```

## 🚨 Error Handling & Recovery

### Automatic Recovery

```python
# If a test doesn't exist in ReadingTest table
if not ReadingTest.objects.filter(test_id=registry_entry.test_id).exists():
    registry_entry.deactivate("Test not found in ReadingTest table")
    # System automatically selects another test
```

### Graceful Degradation

```python
# If no tests are available in registry
if not selected_tests:
    return Response({
        'error': 'No reading tests available for this organization',
        'details': 'No active tests found in test registry'
    }, status=404)
```

## 🔧 Management Commands

### Setup Command Options

```bash
# Basic setup
python manage.py setup_test_registry

# Force re-registration
python manage.py setup_test_registry --force

# Validate only (no registration)
python manage.py setup_test_registry --validate-only

# Generate health report
python manage.py setup_test_registry --health-report

# Verbose output with statistics
python manage.py setup_test_registry --verbose
```

### Command Output Example

```
============================================================
TEST REGISTRY SETUP COMMAND
============================================================
Step 1: Validating database connection...
✓ Database connection successful
  Found 1 ReadingTest objects

Step 2: Checking TestRegistry table...
✓ TestRegistry table accessible
  Found 0 existing registry entries

Step 3: Validating registry consistency...
  Orphaned registry entries: 0
  Unregistered tests: 1
  Total registry entries: 0
  Total reading tests: 1

Step 4: Registering tests in TestRegistry...
✓ Registration complete
  Registered 1 tests

Step 5: Generating health report...
✓ Health report generated
  Status: Excellent
  Health Score: 100/100
  Active Tests: 1
  Total Tests: 1

Step 7: Final validation...
✓ Test selection working
  Selected test: Test 1 (ID: 5c7ba373-5ed1-4994-bbc0-49f1f47ae894)

============================================================
TEST REGISTRY SETUP COMPLETE
============================================================
Total registry entries: 1
Health status: Excellent (100/100)
✓ System is healthy and ready for use
```

## 🔮 Future Enhancements

### Planned Features

1. **Adaptive Difficulty Selection**

   ```python
   # Based on student performance history
   test = TestRegistryService.get_adaptive_test(student_profile)
   ```

2. **A/B Testing Support**

   ```python
   # Different test selection for experiment groups
   test = TestRegistryService.get_test_for_experiment(student_id, 'group_a')
   ```

3. **Premium Test Marketplace**

   ```python
   # Featured tests for premium users
   premium_tests = TestRegistry.objects.filter(is_featured=True)
   ```

4. **Advanced Analytics**
   ```python
   # Usage patterns and performance metrics
   analytics = TestRegistryService.get_advanced_analytics()
   ```

## 🐛 Troubleshooting

### Common Issues

#### 1. **"TestRegistry table not accessible"**

```bash
# Solution: Run migrations first
python manage.py migrate
```

#### 2. **"No tests available in TestRegistry"**

```bash
# Solution: Register existing tests
python manage.py setup_test_registry
```

#### 3. **"Orphaned registry entries found"**

```bash
# Solution: Clean up and re-register
python manage.py setup_test_registry --force
```

#### 4. **Low health score**

```bash
# Solution: Check health report for recommendations
python manage.py setup_test_registry --health-report
```

### Debug Commands

```bash
# Check database consistency
python manage.py setup_test_registry --validate-only --verbose

# Force complete reset
python manage.py setup_test_registry --force --verbose

# Monitor health over time
python manage.py setup_test_registry --health-report
```

### **🐳 Docker Troubleshooting**

#### **Common Docker Issues**

##### **1. "Database connection failed"**

```bash
# Check if database container is running
docker-compose ps

# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec ielts_reading python manage.py check --database default

# Solution: Wait for database to be ready or restart services
docker-compose restart
```

##### **2. "TestRegistry table not accessible"**

```bash
# Check if migrations ran
docker-compose exec ielts_reading python manage.py showmigrations

# Run migrations manually
docker-compose exec ielts_reading python manage.py migrate

# Check TestRegistry table
docker-compose exec ielts_reading python manage.py shell -c "from reading.models import TestRegistry; print(TestRegistry.objects.count())"
```

##### **3. "Container keeps restarting"**

```bash
# Check container logs
docker-compose logs --tail=50 ielts_reading

# Check health status
docker-compose ps

# Rebuild container
docker-compose build --no-cache ielts_reading

# Solution: Check logs for specific error and fix
```

##### **4. "Port already in use"**

```bash
# Check what's using the port
netstat -tulpn | grep 8002

# Stop conflicting services
sudo systemctl stop conflicting-service

# Or change port in docker-compose.yml
ports:
  - "8003:8002"  # Use different host port
```

#### **Docker Debug Commands**

```bash
# Check all containers
docker ps -a

# Check container resources
docker stats

# View container details
docker inspect ielts_reading_ielts_reading_1

# Access container shell
docker-compose exec ielts_reading bash

# Check container logs in real-time
docker-compose logs -f ielts_reading

# Test TestRegistry in container
docker-compose exec ielts_reading python manage.py setup_test_registry --health-report
```

#### **Docker Best Practices**

##### **1. Use Health Checks**

```yaml
# In docker-compose.yml
healthcheck:
  test: ["CMD", "python", "manage.py", "setup_test_registry", "--health-report"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

##### **2. Proper Environment Variables**

```bash
# Use .env file for sensitive data
DATABASE_URL=postgresql://user:pass@db:5432/ielts_reading
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
```

##### **3. Volume Management**

```yaml
# Persist database data
volumes:
  - postgres_data:/var/lib/postgresql/data

# Mount logs directory
volumes:
  - ./logs:/app/logs
```

##### **4. Resource Limits**

```yaml
# Prevent container from using too many resources
deploy:
  resources:
    limits:
      memory: 512M
      cpus: "0.5"
    reservations:
      memory: 256M
      cpus: "0.25"
```

## 📈 Performance Optimization

### Database Indexes

The migration creates optimized indexes for common queries:

- `test_registry_org_idx`: Fast organization filtering
- `test_registry_active_idx`: Fast active test filtering
- `test_registry_usage_idx`: Fast load balancing queries
- `test_registry_org_active_idx`: Fast organization + active filtering
- `test_registry_balancing_idx`: Fast load balancing with multiple criteria

### Caching Strategy

```python
# Cache test selections for 5 minutes
cache.set(cache_key, test_id, timeout=300)

# Clear cache when data changes
TestRegistryService.clear_cache()
```

## 🎉 Success Metrics

### Before TestRegistry

- ❌ Orphaned test IDs causing 404 errors
- ❌ Random test selection without load balancing
- ❌ No monitoring or health checks
- ❌ Manual test management required

### After TestRegistry

- ✅ Zero orphaned test IDs
- ✅ Intelligent load balancing
- ✅ Comprehensive monitoring and health reports
- ✅ Automatic test management and validation
- ✅ Future-ready architecture for advanced features

## 🔗 Integration Points

### Frontend Integration

The frontend already has robust error handling for test ID issues. The TestRegistry ensures these errors never occur by providing only valid, existing test IDs.

### Backend Integration

- **Random Questions Endpoint**: Now uses intelligent selection
- **Exam Start Process**: Gets validated test IDs
- **Test Answers Endpoint**: Works with guaranteed existing tests
- **Management Commands**: Easy setup and monitoring

## 📞 Support

If you encounter any issues with the TestRegistry system:

1. **Check the health report**: `python manage.py setup_test_registry --health-report`
2. **Validate consistency**: `python manage.py setup_test_registry --validate-only`
3. **Review logs**: Check Django logs for detailed error messages
4. **Force reset**: `python manage.py setup_test_registry --force` (if needed)

The TestRegistry system is designed to be self-healing and provides comprehensive logging for troubleshooting.

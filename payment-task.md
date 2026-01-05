# Payment Gateway System - Technical Assessment

**Duration:** 5 days

---

## 📋 Project Overview

You are expected to develop a payment gateway system that handles financial transactions asynchronously. This system will process deposit (money in) and withdrawal (money out) operations while managing bank callbacks and ensuring data consistency across distributed components.

### What You'll Build

A production-grade payment gateway that demonstrates:

- **Asynchronous Processing**: Handle long-running bank operations without blocking API responses
- **Financial Transaction Management**: Process deposits and withdrawals with proper state management
- **External System Integration**: Simulate and handle bank API interactions with proper error handling
- **Data Consistency**: Ensure balance accuracy even under concurrent operations
- **Reliability**: Implement retry mechanisms, idempotency, and failure recovery
- **API Design**: RESTful endpoints with proper HTTP semantics and response codes

### Real-World Context

This mirrors production payment systems where:
- Bank operations take 2-30 seconds to complete
- Network failures can cause duplicate requests
- Multiple users may perform transactions simultaneously
- External bank APIs may be temporarily unavailable
- Regulatory requirements demand audit trails and data consistency

### 🔄 System Flows

#### Deposit Flow
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ User Request │      │     API      │      │ Celery Task  │      │    Bank      │
│              │      │              │      │              │      │ (Simulated)  │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │                     │
       │  POST /deposits     │                     │                     │
       │────────────────────>│                     │                     │
       │                     │                     │                     │
       │                     │  Queue Task         │                     │
       │                     │────────────────────>│                     │
       │                     │                     │                     │
       │  202 Accepted       │                     │                     │
       │<────────────────────│                     │                     │
       │  (status: pending)  │                     │                     │
       │                     │                     │  Process Request    │
       │                     │                     │────────────────────>│
       │                     │                     │  (processing)       │
       │                     │                     │                     │
       │                     │                     │  Result             │
       │                     │                     │<────────────────────│
       │                     │                     │  (success/fail)     │
       │                     │                     │                     │
       │                     │  Update Status      │                     │
       │                     │<────────────────────│                     │
       │                     │  + Balance          │                     │
       │                     │                     │                     │
       ▼                     ▼                     ▼                     ▼
```

#### Bank Callback Flow
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│     Bank     │      │   Webhook    │      │ Celery Task  │      │   Database   │
│              │      │   Handler    │      │              │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │                     │
       │  POST /webhooks/    │                     │                     │
       │  bank-callback      │                     │                     │
       │────────────────────>│                     │                     │
       │                     │                     │                     │
       │                     │  Validate + Queue   │                     │
       │                     │────────────────────>│                     │
       │                     │                     │                     │
       │  200 OK             │                     │                     │
       │<────────────────────│                     │                     │
       │                     │                     │  Update Transaction │
       │                     │                     │────────────────────>│
       │                     │                     │  + Balance          │
       │                     │                     │                     │
       ▼                     ▼                     ▼                     ▼
```

### Bank API Simulation

You must implement a simulated bank API that mimics real-world behavior:

- **Processing Time**: Randomized delays (2-10 seconds) to simulate real bank processing
- **Success Rate**: Configurable success/failure ratio (suggested: 90% success rate)
- **Error Scenarios**: 
  - Timeout errors
  - Insufficient funds (for withdrawals)
  - Bank system unavailable (5xx errors)
  - Invalid request errors (4xx errors)
- **State Transitions**: Pending → Processing → Success/Failed

The simulation design (timing, error rates, scenarios) is up to you, but should demonstrate realistic behavior.

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Message Broker | RabbitMQ + Celery |
| Cache | Redis |
| Monitoring | Flower (Celery task monitoring) |
| Container | Docker + Docker Compose |
| Task Automation | Makefile |

---

## 📊 API Endpoints & Behavior

### Transaction Operations
```
POST   /api/v1/deposits              - Create a deposit
                                       (Idempotency-Key header required)
GET    /api/v1/deposits/{id}         - Get deposit details
GET    /api/v1/deposits              - List deposits (with pagination)

POST   /api/v1/withdrawals           - Create a withdrawal
                                       (Idempotency-Key header required)
GET    /api/v1/withdrawals/{id}      - Get withdrawal details
GET    /api/v1/withdrawals           - List withdrawals (with pagination)
```

**Idempotency Key Requirements:**
- `Idempotency-Key` header is mandatory for POST operations
- Repeated requests with the same key must return the same result
- Keys must be retained for at least 24 hours
- Response should include original status code and body from first request

### User & Balance
```
GET    /api/v1/users/{user_id}/balance       - Query user balance
GET    /api/v1/users/{user_id}/transactions  - Transaction history
                                                (pagination + filtering)
```

**Rate Limiting:**
- Balance endpoint: 10 requests/min per user
- Transaction list: 20 requests/min per user
- Global rate limit: 1000 requests/min

### Webhook & System
```
POST   /webhooks/bank-callback       - Bank callback handler
GET    /health                       - Health check endpoint
```

### Monitoring
```
Flower Dashboard                     - Celery task monitoring (port: 5555)
```

### Expected Response Headers
```
X-RateLimit-Limit: 100              - Maximum requests allowed in time window
X-RateLimit-Remaining: 95           - Remaining requests in current window
X-RateLimit-Reset: 1640000000       - Time when limit resets (unix timestamp)
X-Request-ID: uuid                  - Unique request identifier for tracing
```

**Rate Limit Exceeded Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```
HTTP Status: 429 Too Many Requests

### Expected Behaviors

- Deposit/Withdrawal operations must be processed asynchronously via Celery
- Withdrawals must validate sufficient balance before processing
- Transaction states must be trackable and queryable
- **Idempotency**: Duplicate requests must be handled gracefully (same response)
- **Rate Limiting**: API endpoints must enforce rate limits per user and globally
- Celery tasks must be monitorable through Flower dashboard
- A simple frontend interface for viewing transactions (can be basic)

---

## 🧠 Architectural Decisions

You are expected to make your own architectural decisions on the following topics and document them in your README with clear reasoning:

### Data Modeling
- What entities are required and how should they relate to each other?
- How should the transaction lifecycle be modeled?
- What fields are needed for audit trails and debugging?
- How to model idempotency keys?

### Security
- How will API access be controlled? (Authentication/Authorization)
- How will external webhook requests be validated? (Signature verification)
- How will sensitive data be protected? (Encryption, env variables)
- How to prevent unauthorized balance modifications?

### Rate Limiting
- How will rate limiting be implemented? (Redis? Middleware?)
- What should the user-based and global rate limiting strategy be?
- How to handle distributed rate limiting across multiple API instances?
- What response should be returned when rate limit is exceeded?

### Idempotency (Request Deduplication)
- What happens if the same transaction is triggered multiple times?
- Should idempotency keys be used? How should they be implemented?
- How to prevent duplicate transactions during network failures?
- How long should idempotency keys be stored?

### Data Consistency
- How to ensure data consistency during concurrent balance operations?
- How will race conditions be handled?
- What database transaction isolation level should be chosen and why?
- Should you use optimistic locking, pessimistic locking, or distributed locks?

### Error Handling & Resilience
- How should failed transactions be handled?
- How should retry mechanisms be implemented? (Exponential backoff strategy)
- What should happen when the bank API is down? (Circuit breaker pattern?)
- Should a dead letter queue be used for permanently failed tasks?
- How should error states be communicated to users?
- How to handle partial failures?

### Scalability
- How should large datasets be handled in list endpoints?
- What pagination strategy should be used? (Offset-based vs Cursor-based)
- How would the system scale horizontally?
- How to avoid N+1 queries?

---

## 🚀 Deliverables

### Required Outputs

1. **GitHub Repository (Public)**
   - Working, production-ready code
   - Must start with `docker-compose up` or `make up`
   - **Makefile Required**: Include a Makefile with common commands
   - README.md must include:
     - Setup instructions (how to run locally)
     - Available make commands and their purposes
     - Your architectural decisions and reasoning
     - Trade-offs made and alternative approaches considered
     - System architecture diagram (recommended)
     - Any known limitations or future improvements

**Expected Makefile Commands** (minimum):
```makefile
make up              # Start all services (docker-compose up)
make down            # Stop all services
make build           # Build docker images
make migrate         # Run database migrations
make test            # Run tests
make lint            # Run linters (black, isort, ruff)
make logs            # Show logs from all services
make shell           # Access application shell/container
```

2. **Postman Collection**
   - Complete API collection file (`*.postman_collection.json`)
   - Environment variables defined (base_url, user_id, etc.)
   - Example request bodies for each endpoint
   - Example workflow: Create user → Deposit → Check balance → Withdraw

3. **CREDENTIALS.md**
   - Information needed for testing
   - Sample user credentials
   - Test scenarios and expected outcomes
   - Any seed data or initialization steps

### ⭐ Bonus (Optional)

- **Live Deployment**
  - Any cloud platform (Render, Railway, Fly.io, AWS, etc.)
  - Accessible and testable publicly
  - Frontend deployment can also be included (optional)

- **Code Quality**
  - Pre-commit hooks (black, isort, ruff, etc.)
  - Linter configuration
  - Type hints throughout codebase with mypy validation

- **Test Coverage**
  - Unit tests for business logic
  - Integration tests for API endpoints
  - Test coverage 70%+ recommended
  - Tests for edge cases (race conditions, failures, etc.)

- **Logging & Observability**
  - Structured logging (JSON format)
  - Request/response logging with correlation IDs
  - Distributed tracing setup
  - Metrics collection (Prometheus format)

- **Advanced Features**
  - Circuit breaker pattern implementation
  - Distributed locking (Redis) to prevent race conditions
  - Webhook retry mechanism with exponential backoff
  - Admin panel (Django Admin style) for transaction management
  - GraphQL API alternative
  - Real-time notifications (WebSocket) for transaction updates

---

## 📌 Important Notes

- Code quality, readability, and maintainability are crucial
- Think **production-ready**: error handling, logging, monitoring
- Your decisions' rationale is as important as the implementation itself
- Consider edge cases and error scenarios (network failures, concurrent requests, etc.)
- Document any incomplete parts with your intended approach in README

### 🎯 Evaluation Criteria

1. **Technical Depth**
   - Architectural decisions and their justifications
   - Implementation of idempotency, rate limiting, and concurrency control
   - Error handling and system resilience
   - Understanding of distributed systems challenges

2. **Code Quality**
   - Clean code principles (SOLID, DRY, KISS)
   - Proper error handling and logging
   - Code organization and project structure
   - Type safety and validation

3. **System Design**
   - Database modeling and relationships
   - Asynchronous task management
   - Security approach and implementation
   - Scalability considerations

4. **Documentation**
   - README quality and completeness
   - API documentation (OpenAPI/Swagger)
   - Clear explanation of design decisions
   - Code comments where necessary

### ⚠️ Common Pitfalls to Avoid

- **Not handling concurrent balance updates** - Can lead to incorrect balances
- **Missing idempotency** - Duplicate transactions from retries
- **No retry mechanism** - System brittle to temporary failures
- **Poor error messages** - Hard to debug issues
- **Missing database indexes** - Performance issues with scale
- **No request validation** - Security vulnerabilities
- **Synchronous bank calls** - Blocks API responses

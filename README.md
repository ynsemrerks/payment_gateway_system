# Payment Gateway API


A production-grade payment gateway system built with FastAPI that handles financial transactions asynchronously using Celery, with proper data consistency, idempotency, and rate limiting. Includes a **Basic Frontend** for easy interaction.

## 🏗️ Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Client    │────▶│  FastAPI API │────▶│   PostgreSQL  │
└──────┬──────┘     └──────┬───────┘     └───────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│  Frontend   │     │   RabbitMQ   │
│(Nginx/HTML) │     └──────┬───────┘
└─────────────┘            │
                           │
                           ▼
                    ┌──────────────┐     ┌───────────────┐
                    │Celery Worker │────▶│  Bank API     │
                    └──────────────┘     │  (Simulated)  │
                                         └───────────────┘
```

## ✨ Features

- ✅ **Async Transaction Processing**: Deposits and withdrawals processed via Celery
- ✅ **Idempotency**: Duplicate request prevention with 24-hour key retention
- ✅ **Rate Limiting**: Redis-based rate limiting (user-specific and global)
- ✅ **Data Consistency**: Pessimistic locking with `SELECT FOR UPDATE`
- ✅ **Comprehensive Frontend**: Basic UI with real-time status updates
- ✅ **Bank Simulation**: Realistic delays (2-10s) and 90% success rate
- ✅ **Retry Mechanism**: Exponential backoff for transient failures
- ✅ **Webhook Support**: Bank callback handling with signature verification
- ✅ **Monitoring**: Flower dashboard for Celery task monitoring

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (optional, for convenience commands)

### Setup

1. **Clone the repository**
```bash
git clone <https://github.com/ynsemrerks/payment_gateway_system.git>
cd payment_gateway
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

3. **Start all services**
```bash
make up
# Or: docker-compose up -d
```

4. **Run database migrations**
```bash
make migrate
# Or: docker-compose exec api alembic upgrade head
```

5. **Seed test data**
```bash
make seed
# Or: docker-compose exec api python -m app.scripts.seed_data
```

6. **Access the services**
- **Frontend**: http://localhost:5500
  - **Dashboard**: Main view with balance and recent transactions
  - **Deposits**: Dedicated list for viewing deposit history
  - **Withdrawals**: Dedicated list for viewing withdrawal history
  - **Transaction Details**: Detailed view of any transaction with live status polling
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery monitoring)**: http://localhost:5555
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## 📖 Makefile Commands

```bash
make up         # Start all services
make down       # Stop all services
make build      # Build Docker images
make migrate    # Run database migrations
make test       # Run tests
make lint       # Run linters (black, isort, ruff)
make logs       # Show logs from all services
make shell      # Access application shell
make clean      # Remove containers and volumes
make seed       # Seed database with test data

### 💻 Frontend Functionality

The frontend is a basic, responsive web application that provides:

1.  **Secure Login**: Authenticate using your Email and API Key.
2.  **Dashboard**:
    *   Real-time balance display.
    *   Quick actions for making new deposits and withdrawals.
    *   List of the 10 most recent transactions.
3.  **Dedicated List Pages**:
    *   **/deposits.html**: View your entire deposit history.
    *   **/withdrawals.html**: View your entire withdrawal history.
    *   *Backend optimized*: These pages use efficient type-based filtering on the API.
4.  **Transaction Detail View**:
    *   Navigate to any transaction to see its full lifecycle.
    *   View **Bank Reference** numbers once processed.
    *   See detailed **Error Notifications** if a transaction fails.
    *   **Live Status Polling**: The page automatically refreshes every few seconds if a transaction is still in 'pending' or 'processing' states.
```

## 🏛️ Architectural Decisions

### 1. Data Modeling

**Decision**: Three main entities - Users, Transactions, and IdempotencyKeys

**Rationale**:
- **Users**: Store balance directly for fast access with row-level locking
- **Transactions**: Complete audit trail with state machine (pending → processing → success/failed)
- **IdempotencyKeys**: Separate table for 24-hour retention without affecting transaction queries

### 2. Security

**Decision**: API key-based authentication with webhook signature verification

**Rationale**:
- Simple API key auth sufficient for service-to-service communication
- HMAC-SHA256 signatures prevent webhook tampering
- Environment variables for secrets

### 3. Rate Limiting

**Decision**: Redis-based sliding window algorithm

**Rationale**:
- Distributed rate limiting works across multiple API instances
- Sliding window more accurate than fixed window
- Per-user limits (10/min balance, 20/min transactions) + global limit (1000/min)

**Implementation**: Sorted sets in Redis with timestamp scores

### 4. Idempotency

**Decision**: Mandatory `Idempotency-Key` header for POST operations

**Rationale**:
- Prevents duplicate transactions from network retries
- 24-hour retention balances storage vs. usefulness
- Stores full response (status + body) for exact replay

### 5. Data Consistency

**Decision**: Pessimistic locking with `SELECT FOR UPDATE`

**Rationale**:
- Prevents race conditions during concurrent balance updates
- PostgreSQL row-level locks are efficient
- Simpler than optimistic locking for this use case

### 6. Error Handling & Resilience

**Decision**: Celery retry with exponential backoff (max 5 retries)

**Rationale**:
- Automatic retry for transient errors (timeouts, system unavailable)
- Exponential backoff prevents overwhelming failing services
- Non-retryable errors (insufficient funds) fail immediately

**Configuration**:
- Retry backoff: 2^n seconds (jittered)
- Max backoff: 600 seconds (10 minutes)
- Dead letter queue for permanently failed tasks

### 7. Scalability

**Decision**: Cursor-based pagination with database indexes

**Rationale**:
- Indexes on user_id, status, created_at for fast queries
- Offset pagination acceptable for v1 (cursor-based for future)
- Stateless API design allows horizontal scaling

**Indexes Created**:
- `idx_transaction_user_id`
- `idx_transaction_status`
- `idx_transaction_created_at`
- `idx_transaction_user_status` (composite)

## 📊 API Endpoints

### Transactions
```
POST   /api/v1/deposits              - Create deposit (requires Idempotency-Key)
GET    /api/v1/deposits/{id}         - Get deposit details
GET    /api/v1/deposits              - List deposits (paginated)

POST   /api/v1/withdrawals           - Create withdrawal (requires Idempotency-Key)
GET    /api/v1/withdrawals/{id}      - Get withdrawal details
GET    /api/v1/withdrawals           - List withdrawals (paginated)
```

### Users
```
GET    /api/v1/users/{user_id}/balance       - Get balance (10 req/min)
GET    /api/v1/users/{user_id}/transactions  - Transaction history (20 req/min)
```

### Webhooks
```
POST   /webhooks/bank-callback       - Bank callback handler
```

### System
```
POST   /api/v1/auth/login            - Login (Email + API Key)
GET    /health                       - Health check
GET    /                             - API info
GET    /docs                         - OpenAPI documentation
```

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI | High-performance async API framework |
| Database | PostgreSQL | Reliable ACID-compliant database |
| ORM | SQLAlchemy | Database abstraction and migrations |
| Message Broker | RabbitMQ | Reliable message queuing |
| Task Queue | Celery | Async task processing |
| Cache | Redis | Rate limiting and caching |
| Monitoring | Flower | Celery task monitoring |
| Containerization | Docker Compose | Service orchestration |

## 🧪 Testing

Run the test suite:
```bash
make test
```

Tests cover:
- ✅ Deposit creation and validation
- ✅ Withdrawal with insufficient balance
- ✅ Idempotency key handling
- ✅ Rate limiting enforcement
- ✅ Authentication and authorization

## 🔐 Security Considerations

- API keys stored securely in database
- Webhook signatures prevent tampering
- Environment variables for sensitive config
- Database connection pooling with limits
- Rate limiting prevents abuse
- Input validation with Pydantic


## 🎣 Webhook API

### Bank Callback Endpoint

The `POST /webhooks/bank-callback` endpoint is used by the bank (or simulation) to notify the payment gateway about the status of a transaction.

**URL**: `/webhooks/bank-callback`
**Method**: `POST`
**Content-Type**: `application/json`

#### Payload Structure

```json
{
  "transaction_id": 123,
  "bank_reference": "BANK-REF-123456",
  "status": "success",
  "error_message": null,
  "signature": "hex_encoded_hmac_sha256_signature"
}
```

- `transaction_id`: The ID of the transaction in the Payment Gateway.
- `status`: Transaction status (`success` or `failed`).
- `signature`: HMAC-SHA256 signature for verification.

#### Signature Verification

To ensure security, all webhook requests must include a valid signature. The signature is generated using HMAC-SHA256 with your `WEBHOOK_SECRET`.

**Generation Steps:**
1. Create the JSON payload *excluding* the `signature` field.
2. Sort keys alphabetically and remove whitespace (separators: `(',', ':')`).
3. Generate HMAC-SHA256 hash using the `WEBHOOK_SECRET` and the canonical payload string.
4. Add the generated signature to the payload in the `signature` field.

**Python Example:**
You can use the helper script `app/scripts/generate_webhook_signature.py` to generate signatures for testing:

```bash
# Generate signature for transaction_id=1
python app/scripts/generate_webhook_signature.py 1
```

Or manually in Python:
```python
import hmac
import hashlib
import json

secret = "your-webhook-secret-change-in-production"
payload = {
    "transaction_id": 1,
    "bank_reference": "REF-123",
    "status": "success",
    "error_message": None
}

# Canonical JSON string
payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)

# Generate signature
signature = hmac.new(
    secret.encode(),
    payload_str.encode(),
    hashlib.sha256
).hexdigest()

print(signature)
```

## 📚 Additional Documentation

- **CREDENTIALS.md**: Test user credentials and scenarios
- **Postman Collection**: `payment_gateway_system/payment_gateway.postman_collection.json`
- **API Docs**: http://localhost:8000/docs (when running)

## 🤝 Contributing

1. Run linters before committing:
```bash
make lint
```

2. Ensure tests pass:
```bash
make test
```

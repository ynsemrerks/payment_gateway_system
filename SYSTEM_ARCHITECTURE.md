# System Architecture

This diagram illustrates the asynchronous payment processing flow of the Payment Gateway System.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI (API)
    participant DB as PostgreSQL
    participant Q as RabbitMQ
    participant W as Celery Worker
    participant Bank as Bank Simulator

    Note over C, Bank: Async Deposit Flow

    C->>API: POST /api/v1/deposits
    activate API
    API->>DB: Create Transaction (PENDING)
    API->>Q: Publish process_deposit_task
    API-->>C: 202 Accepted (Transaction ID)
    deactivate API

    Q->>W: Consume Task
    activate W
    W->>DB: Fetch Transaction
    W->>DB: Update Status (PROCESSING)
    W->>Bank: Request Deposit
    activate Bank
    Bank-->>W: Success Response
    deactivate Bank
    
    W->>DB: Update Balance (+Amount)
    W->>DB: Update Status (SUCCESS)
    deactivate W

    Note over C, Bank: Webhook Flow (Callback)

    Bank->>API: POST /webhooks/bank-callback
    activate API
    API->>API: Verify Signature (HMAC)
    API->>Q: Publish process_webhook_task
    API-->>Bank: 200 OK
    deactivate API

    Q->>W: Consume Webhook Task
    activate W
    W->>DB: Update Transaction Status
    deactivate W
```

## Component Roles
- **FastAPI**: Handles HTTP requests, validation, and queues tasks.
- **PostgreSQL**: Stores persistent data (Users, Transactions).
- **RabbitMQ**: Message broker for asynchronous task distribution.
- **Celery Worker**: Executes background tasks (Bank simulation, DB updates).
- **Redis**: Caches idempotency keys and stores Celery results.

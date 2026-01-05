# Test Credentials and Scenarios

## Admin Panel Access

To login to the **Admin Panel** (http://localhost:8000/admin):

- **Username**: `admin`
- **Password**: `admin`

## Frontend Access

To login to the **Frontend Dashboard** (http://localhost:5500), use the same credentials as your API User:

- **Email**: Your user email (e.g., `alice@example.com`)
- **API Key**: Your API Key

*(You can find these in the `make seed` output or in the database)*

## Test Users

After running `make seed`, the following test users will be available:

### User 1: Alice
- **Email**: alice@example.com
- **API Key**: (Generated during seeding - check console output)
- **Initial Balance**: $1,000.00
- **Use Case**: Testing deposits and withdrawals with sufficient balance

### User 2: Bob
- **Email**: bob@example.com
- **API Key**: (Generated during seeding - check console output)
- **Initial Balance**: $500.00
- **Use Case**: Testing medium balance scenarios

### User 3: Charlie
- **Email**: charlie@example.com
- **API Key**: (Generated during seeding - check console output)
- **Initial Balance**: $0.00
- **Use Case**: Testing insufficient balance scenarios

## Getting API Keys

Run the seed script and copy the API keys from the output:

```bash
make seed
```

Output will look like:
```
✅ Database seeded successfully!

📝 Test Users Created:
--------------------------------------------------------------------------------
Email: alice@example.com
API Key: abc123xyz...
Balance: $1000.00
--------------------------------------------------------------------------------
```

## Test Scenarios

### Scenario 1: Successful Deposit

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/deposits \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <alice-api-key>" \
  -H "Idempotency-Key: deposit-001" \
  -d '{"amount": 100.00}'
```

**Expected Result:**
- Status: 202 Accepted
- Transaction created with status "pending"
- Celery task queued for processing
- After 2-10 seconds, transaction status becomes "success"
- Balance increased by $100.00

### Scenario 2: Successful Withdrawal

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/withdrawals \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <alice-api-key>" \
  -H "Idempotency-Key: withdrawal-001" \
  -d '{"amount": 50.00}'
```

**Expected Result:**
- Status: 202 Accepted
- Transaction created with status "pending"
- Balance check passes (Alice has $1,000)
- After processing, balance decreased by $50.00

### Scenario 3: Insufficient Balance

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/withdrawals \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <charlie-api-key>" \
  -H "Idempotency-Key: withdrawal-002" \
  -d '{"amount": 100.00}'
```

**Expected Result:**
- Status: 400 Bad Request
- Error: "insufficient_balance"
- Transaction NOT created

### Scenario 4: Idempotency Test

**First Request:**
```bash
curl -X POST http://localhost:8000/api/v1/deposits \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <alice-api-key>" \
  -H "Idempotency-Key: idempotency-test-001" \
  -d '{"amount": 100.00}'
```

**Second Request (same key, different amount):**
```bash
curl -X POST http://localhost:8000/api/v1/deposits \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <alice-api-key>" \
  -H "Idempotency-Key: idempotency-test-001" \
  -d '{"amount": 500.00}'
```

**Expected Result:**
- Both requests return identical responses
- Only ONE transaction created (for $100.00)
- Second request returns cached response

### Scenario 5: Check Balance

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/users/1/balance \
  -H "X-API-Key: <alice-api-key>"
```

**Expected Result:**
- Status: 200 OK
- Current balance returned
- Rate limit headers included

### Scenario 6: Transaction History

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/1/transactions?limit=10&offset=0" \
  -H "X-API-Key: <alice-api-key>"
```

**Expected Result:**
- Status: 200 OK
- Paginated list of transactions
- Total count and pagination info

### Scenario 7: Rate Limiting

**Request (repeat 11 times rapidly):**
```bash
for i in {1..11}; do
  curl -X GET http://localhost:8000/api/v1/users/1/balance \
    -H "X-API-Key: <alice-api-key>"
done
```

**Expected Result:**
- First 10 requests: 200 OK
- 11th request: 429 Too Many Requests
- Retry-After header included

### Scenario 8: Bank Webhook Callback

**Request:**
```bash
curl -X POST http://localhost:8000/webhooks/bank-callback \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 1,
    "bank_reference": "BANK-REF-123",
    "status": "success",
    "signature": "<hmac-signature>"
  }'
```

**Expected Result:**
- Status: 200 OK (if signature valid)
- Webhook queued for processing
- Transaction status updated

## Monitoring

### Flower Dashboard
- URL: http://localhost:5555
- Monitor Celery tasks in real-time
- View task success/failure rates
- Check worker status

### RabbitMQ Management
- URL: http://localhost:15672
- Username: guest
- Password: guest
- Monitor message queues

### API Documentation
- URL: http://localhost:8000/docs
- Interactive Swagger UI
- Test endpoints directly

## Common Issues

### Issue: "Invalid API key"
**Solution**: Ensure you're using the correct API key from the seed output

### Issue: "Idempotency-Key header is required"
**Solution**: Add the header to your request

### Issue: "Rate limit exceeded"
**Solution**: Wait 60 seconds or use a different user

### Issue: Transaction stuck in "pending"
**Solution**: Check Celery worker logs: `make logs`

## Testing Workflow

1. **Seed database**: `make seed`
2. **Copy API keys** from output
3. **Create deposit**: Use Scenario 1
4. **Check balance**: Use Scenario 5
5. **Create withdrawal**: Use Scenario 2
6. **Check balance again**: Verify balance decreased
7. **Monitor in Flower**: http://localhost:5555
8. **Test idempotency**: Use Scenario 4
9. **Test rate limiting**: Use Scenario 7

## Notes

- All amounts are in USD with 2 decimal places
- Transactions process asynchronously (2-10 seconds delay)
- Bank simulation has 90% success rate (10% random failures)
- Idempotency keys are valid for 24 hours
- Rate limits reset every 60 seconds

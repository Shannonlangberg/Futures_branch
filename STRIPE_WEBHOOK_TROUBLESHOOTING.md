# Stripe Webhook Troubleshooting Guide

## Current Issue
Stripe webhooks are not being sent automatically. The webhook endpoint is accessible, but Stripe shows 0 deliveries.

## Common Causes

### 1. Test Mode vs Live Mode Mismatch
**Problem:** Webhook is configured in test mode, but payments are in live mode (or vice versa).

**Solution:**
- Check your Stripe Dashboard → Developers → Webhooks
- Ensure the webhook is in **Test mode** (toggle in top right of Stripe Dashboard)
- Verify your `STRIPE_SECRET_KEY` in Railway starts with `sk_test_` (test mode) or `sk_live_` (live mode)
- The webhook mode must match your API key mode

### 2. Webhook Created After Payments
**Problem:** Stripe doesn't send retroactive events. If the webhook was created after payments were made, those payments won't trigger webhooks.

**Solution:**
- Make a NEW test payment AFTER the webhook is configured
- This will trigger a webhook event

### 3. Webhook Endpoint Not Reachable
**Problem:** Stripe can't reach your webhook endpoint.

**Solution:**
- Test endpoint: `https://futuresbranch-production.up.railway.app/api/webhooks/stripe`
- Should return: `{"status":"ok",...}` for GET requests
- Check Railway logs for any connection errors

### 4. Webhook Secret Mismatch
**Problem:** The webhook secret in Railway doesn't match the one in Stripe Dashboard.

**Solution:**
- Go to Stripe Dashboard → Developers → Webhooks → Your webhook
- Click "Signing secret" → "Reveal"
- Copy the secret (starts with `whsec_`)
- In Railway → Variables → Set `STRIPE_WEBHOOK_SECRET` to this value
- Redeploy

## How to Fix

### Step 1: Verify Webhook Configuration
1. Go to Stripe Dashboard → Developers → Webhooks
2. Click your webhook (`captivating-excellence`)
3. Verify:
   - **Endpoint URL:** `https://futuresbranch-production.up.railway.app/api/webhooks/stripe`
   - **Mode:** Should match your API key mode (Test/Live toggle in top right)
   - **Events:** Should include `payment_intent.succeeded`

### Step 2: Check API Key Mode
1. In Railway → Variables
2. Check `STRIPE_SECRET_KEY`:
   - `sk_test_...` = Test mode
   - `sk_live_...` = Live mode
3. Ensure webhook is in the same mode

### Step 3: Test the Webhook
1. Make a NEW test payment ($0.50) from mobile app
2. Check Stripe Dashboard → Webhooks → Event deliveries
3. You should see a `payment_intent.succeeded` event
4. Check Railway logs for `[WEBHOOK]` messages

### Step 4: Manual Sync (Temporary Workaround)
If webhooks still don't work, manually sync payments:
```bash
curl -X POST https://futuresbranch-production.up.railway.app/api/giving/sync-payment \
  -H "Content-Type: application/json" \
  -d '{"payment_intent_id": "pi_..."}'
```

## Diagnostic Endpoints

- **Test endpoint:** `GET /api/webhooks/test-endpoint`
- **Check transactions:** `GET /api/webhooks/check-transactions`
- **Diagnostics:** `GET /api/webhooks/diagnostics`

## Next Steps

1. Verify webhook is in correct mode (Test/Live)
2. Make a new test payment
3. Check Stripe Dashboard for webhook deliveries
4. Check Railway logs for `[WEBHOOK]` messages


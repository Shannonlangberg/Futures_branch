# Stripe Webhook Automatic Testing Plan

## Goal
Test that Stripe webhooks fire automatically when payments complete, so we don't need manual sync.

## Pre-Test Checklist

### 1. Verify Stripe Dashboard Configuration
- [ ] Go to Stripe Dashboard → Developers → Webhooks (in **Test mode**)
- [ ] Click your webhook endpoint
- [ ] Verify:
  - **Endpoint URL:** `https://futuresbranch-production.up.railway.app/api/webhooks/stripe`
  - **Status:** Active
  - **Mode:** Test mode (not Live)
  - **Events:** Includes `payment_intent.succeeded`
  - **Signing secret:** Copied and matches `STRIPE_WEBHOOK_SECRET` in Railway

### 2. Verify Railway Configuration
- [ ] Railway → Variables → `STRIPE_SECRET_KEY` starts with `sk_test_...`
- [ ] Railway → Variables → `STRIPE_WEBHOOK_SECRET` matches the webhook secret from Stripe Dashboard
- [ ] Railway is deployed and running

## Test Steps

### Test 1: Make a Real Payment
1. Make a test payment ($0.50) from mobile app
2. Complete the payment fully
3. Check Stripe Dashboard → Webhooks → Event deliveries
   - Should see a `payment_intent.succeeded` event
   - Click it to see if it succeeded (200) or failed
4. Check Railway logs for `[WEBHOOK]` messages
5. Check `/api/webhooks/check-transactions` to see if transaction was recorded

### Test 2: Verify Webhook Endpoint is Reachable
```bash
curl https://futuresbranch-production.up.railway.app/api/webhooks/stripe
```
Should return: `{"status":"ok",...}`

### Test 3: Check Payment Intent Status
After making a payment, verify it actually succeeded:
```bash
# Get payment intent ID from mobile app logs
# Then check status in Stripe Dashboard → Payments
```

## Expected Results

✅ **Success:**
- Payment completes in mobile app
- Stripe Dashboard shows `payment_intent.succeeded` event
- Railway logs show `[WEBHOOK]` messages
- Transaction appears in database automatically
- No manual sync needed

❌ **Failure:**
- Payment completes but no webhook event in Stripe Dashboard
- Or webhook event shows as failed
- Transaction not in database

## Troubleshooting

### If webhooks aren't firing:
1. Check webhook is in **Test mode** (same as API keys)
2. Verify webhook is listening to `payment_intent.succeeded`
3. Check webhook endpoint URL is correct
4. Verify webhook secret matches Railway variable

### If webhook fires but fails:
1. Check Railway logs for error messages
2. Verify webhook secret is correct
3. Check if endpoint is accessible from Stripe's servers

## Next Steps After Testing

If test passes:
- ✅ Automatic webhooks are working!
- Deploy to production with same configuration

If test fails:
- Investigate why Stripe isn't sending webhooks
- Check webhook configuration in Stripe Dashboard
- Verify endpoint accessibility


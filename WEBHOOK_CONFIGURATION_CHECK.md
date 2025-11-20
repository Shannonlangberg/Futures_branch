# Stripe Webhook Configuration Verification

## Critical Issue: Payments succeed but webhooks don't fire

**Status:** Payment succeeded ✅, but Stripe isn't sending webhooks ❌

## Step-by-Step Webhook Configuration

### 1. Go to Stripe Dashboard
- Open: https://dashboard.stripe.com
- **IMPORTANT:** Make sure you're in **TEST mode** (toggle in top right should say "Test mode")

### 2. Navigate to Webhooks
- Click: **Developers** (left sidebar)
- Click: **Webhooks**
- You should see your webhook endpoint listed

### 3. Check/Create Webhook Endpoint

**If webhook exists:**
- Click on your webhook
- Verify these settings:

**If webhook doesn't exist:**
- Click **"Add endpoint"** or **"Create endpoint"**
- Set **Endpoint URL:** `https://futuresbranch-production.up.railway.app/api/webhooks/stripe`
- Click **"Select events"**
- Check these events:
  - ✅ `payment_intent.succeeded`
  - ✅ `invoice.payment_succeeded`
  - ✅ `customer.subscription.created`
  - ✅ `customer.subscription.updated`
  - ✅ `customer.subscription.deleted`
  - ✅ `invoice.payment_failed`
- Click **"Add events"**
- Click **"Add endpoint"** or **"Save"**

### 4. Copy Webhook Signing Secret
- After creating/selecting webhook, click **"Reveal"** next to "Signing secret"
- Copy the secret (starts with `whsec_...`)
- Go to Railway → Variables
- Set `STRIPE_WEBHOOK_SECRET` to this value
- Redeploy Railway

### 5. Verify Configuration
- **Endpoint URL:** `https://futuresbranch-production.up.railway.app/api/webhooks/stripe`
- **Status:** Active
- **Mode:** Test mode (same as your API keys)
- **Events:** Includes `payment_intent.succeeded`
- **Signing secret:** Matches Railway variable

## Common Issues

### Issue 1: Webhook in Wrong Mode
- **Symptom:** Webhook exists but shows 0 deliveries
- **Fix:** Ensure webhook is in **Test mode** (same as your `sk_test_...` API keys)

### Issue 2: Webhook Not Listening to Right Events
- **Symptom:** Webhook exists but doesn't fire for payments
- **Fix:** Verify `payment_intent.succeeded` is in the events list

### Issue 3: Wrong Endpoint URL
- **Symptom:** Webhook fires but fails
- **Fix:** Verify URL is exactly: `https://futuresbranch-production.up.railway.app/api/webhooks/stripe`

### Issue 4: Webhook Secret Mismatch
- **Symptom:** Webhook fires but returns "Invalid signature"
- **Fix:** Copy signing secret from Stripe Dashboard and update Railway variable

## Test After Configuration

1. Make a test payment ($0.50) from mobile app
2. Check Stripe Dashboard → Webhooks → **Event deliveries** tab
   - Should see a new `payment_intent.succeeded` event
3. Check Railway logs for `[WEBHOOK]` messages
4. Check `/api/webhooks/check-transactions` - transaction should appear automatically

## If Still Not Working

If webhook is configured correctly but still not firing:
1. Check Stripe Dashboard → Webhooks → Event deliveries
   - Are there ANY events? (even failed ones)
2. Check Railway logs for any `[WEBHOOK]` messages
3. Verify Railway is accessible from internet (not blocked by firewall)
4. Try creating a NEW webhook endpoint (delete old one, create fresh)


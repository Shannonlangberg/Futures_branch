# Stripe Integration Setup Guide

This guide will walk you through setting up Stripe for the giving system, including one-time payments and recurring subscriptions.

## Step 1: Create a Stripe Account

1. Go to [https://stripe.com](https://stripe.com)
2. Sign up for a free account
3. Complete your business information
4. Verify your email

## Step 2: Get Your API Keys

### For Development (Test Mode)

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Make sure you're in **Test mode** (toggle in top right)
3. Navigate to **Developers** → **API keys**
4. You'll see:
   - **Publishable key** (starts with `pk_test_`)
   - **Secret key** (starts with `sk_test_`) - Click "Reveal test key"

### For Production (Live Mode)

1. Switch to **Live mode** in Stripe Dashboard
2. Navigate to **Developers** → **API keys**
3. Get your **Live keys**:
   - **Publishable key** (starts with `pk_live_`)
   - **Secret key** (starts with `sk_live_`)

## Step 3: Configure Environment Variables

### Backend Environment Variables

Add these to your `backend/.env` file or Railway environment variables:

```bash
# Stripe Secret Key (backend only - never expose this!)
STRIPE_SECRET_KEY=sk_test_xxxxx  # Use sk_live_xxxxx for production

# Stripe Webhook Secret (get this after setting up webhook)
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

### Frontend Environment Variables

Add this to your `frontend/.env` file or Railway environment variables:

```bash
# Stripe Publishable Key (safe to expose in frontend)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx  # Use pk_live_xxxxx for production
```

**Note:** For Railway deployment, add `VITE_STRIPE_PUBLISHABLE_KEY` to your Railway environment variables. It will be available to the frontend build.

## Step 4: Set Up Stripe Webhooks

Webhooks are **critical** for security - they ensure all payments go through your system.

### 4.1 Create Webhook Endpoint

1. Go to [Stripe Dashboard](https://dashboard.stripe.com) → **Developers** → **Webhooks**
2. Click **"Add endpoint"**
3. Enter your webhook URL:
   ```
   https://your-domain.com/api/webhooks/stripe
   ```
   Replace `your-domain.com` with your actual domain (e.g., `futures-pulse-production.up.railway.app`)

### 4.2 Select Events to Listen To

Select these events (check the boxes):

- ✅ `payment_intent.succeeded` - One-time payment succeeded
- ✅ `invoice.payment_succeeded` - Subscription payment succeeded
- ✅ `customer.subscription.created` - New subscription created
- ✅ `customer.subscription.updated` - Subscription updated
- ✅ `customer.subscription.deleted` - Subscription canceled
- ✅ `invoice.payment_failed` - Payment failed

### 4.3 Get Webhook Signing Secret

1. After creating the webhook, click on it
2. In the **"Signing secret"** section, click **"Reveal"**
3. Copy the secret (starts with `whsec_`)
4. Add it to your environment variables as `STRIPE_WEBHOOK_SECRET`

### 4.4 Test Your Webhook

1. In Stripe Dashboard → Webhooks → Your endpoint
2. Click **"Send test webhook"**
3. Select an event (e.g., `payment_intent.succeeded`)
4. Check your server logs to confirm it's received

## Step 5: Test the Integration

### Test One-Time Payment

1. Go to your giving page: `https://your-domain.com/give`
2. Fill out the form
3. Use Stripe test card: `4242 4242 4242 4242`
4. Use any future expiry date (e.g., `12/34`)
5. Use any 3-digit CVC (e.g., `123`)
6. Use any ZIP code

### Test Recurring Subscription

1. Go to your giving page
2. Toggle "Make this a recurring gift"
3. Select frequency (Weekly/Monthly/Yearly)
4. Use the same test card
5. The subscription will be created and payments will process automatically

### Test Cards

Stripe provides test cards for different scenarios:

- **Success:** `4242 4242 4242 4242`
- **Decline:** `4000 0000 0000 0002`
- **Requires Authentication:** `4000 0025 0000 3155`
- **Insufficient Funds:** `4000 0000 0000 9995`

See [Stripe Test Cards](https://stripe.com/docs/testing#cards) for more.

## Step 6: Run Database Migration

Make sure the subscription table exists:

```bash
# The migration file is already created: backend/migrations/022_giving_subscriptions.sql
# Apply it to your database
```

## Step 7: Security Checklist

✅ **Never commit API keys to git**
- Use `.env` files (already in `.gitignore`)
- Use Railway environment variables for production

✅ **Use different keys for test vs production**
- Test keys: `sk_test_` and `pk_test_`
- Live keys: `sk_live_` and `pk_live_`

✅ **Webhook signature verification is enabled**
- The webhook handler verifies all requests from Stripe
- Invalid signatures are rejected

✅ **All payments go through webhooks**
- One-time payments: `payment_intent.succeeded`
- Subscription payments: `invoice.payment_succeeded`
- All payments are tracked in your database

## Step 8: Go Live

When ready for production:

1. **Switch to Live Mode** in Stripe Dashboard
2. **Update environment variables:**
   - `STRIPE_SECRET_KEY=sk_live_xxxxx`
   - `VITE_STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx`
3. **Create a new webhook endpoint** for your production domain
4. **Get the production webhook secret** and update `STRIPE_WEBHOOK_SECRET`
5. **Test with a small real payment** first
6. **Monitor webhook logs** in Stripe Dashboard

## Troubleshooting

### "Stripe not configured" error
- Check that `STRIPE_SECRET_KEY` is set in your environment
- Restart your server after adding environment variables

### Webhook not receiving events
- Check your webhook URL is correct and accessible
- Verify `STRIPE_WEBHOOK_SECRET` is set correctly
- Check Stripe Dashboard → Webhooks → Your endpoint → Recent events
- Look for failed deliveries and error messages

### Payments not appearing in database
- Check webhook is receiving events (Stripe Dashboard)
- Check server logs for webhook processing errors
- Verify webhook signature verification is working

### Frontend can't load Stripe
- Check `VITE_STRIPE_PUBLISHABLE_KEY` is set
- Rebuild frontend after adding environment variable
- Check browser console for errors

## Support

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)


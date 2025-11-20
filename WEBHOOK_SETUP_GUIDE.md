# Stripe Webhook Setup - Step by Step Guide

## What is a Webhook?

A webhook is like a phone call from Stripe to your server. When a payment happens, Stripe calls your server to tell you about it. This ensures all payments are tracked in your system.

## Step 1: Determine Your Webhook URL

### If Running Locally (Development)

You need to expose your local server to the internet. Use **ngrok**:

1. **Install ngrok:**
   ```bash
   # Mac
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Start your local server:**
   ```bash
   cd backend
   python app.py
   # Server runs on http://localhost:5000 (or whatever port)
   ```

3. **In a new terminal, start ngrok:**
   ```bash
   ngrok http 5000
   # Or whatever port your server uses
   ```

4. **Copy the HTTPS URL** ngrok gives you:
   ```
   Forwarding: https://abc123.ngrok.io -> http://localhost:5000
   ```
   Your webhook URL will be: `https://abc123.ngrok.io/api/webhooks/stripe`

### If Running on Railway (Production)

1. **Find your Railway domain:**
   - Go to [Railway Dashboard](https://railway.app)
   - Click on your project
   - Click on your backend service
   - Look for "Domains" or "Settings" → "Networking"
   - You'll see something like: `futures-pulse-production.up.railway.app`

2. **Your webhook URL will be:**
   ```
   https://futures-pulse-production.up.railway.app/api/webhooks/stripe
   ```
   (Replace with your actual Railway domain)

## Step 2: Set Up Webhook in Stripe Dashboard

### Visual Step-by-Step:

1. **Go to Stripe Dashboard:**
   - Visit: https://dashboard.stripe.com/test/webhooks
   - Make sure you're in **Test mode** (toggle in top right)

2. **Click "Add endpoint"** button (top right)

3. **Enter your webhook URL:**
   - Paste the URL from Step 1
   - Example: `https://abc123.ngrok.io/api/webhooks/stripe`
   - Or: `https://futures-pulse-production.up.railway.app/api/webhooks/stripe`

4. **Select events to listen to:**
   Click the checkboxes for these events:
   
   ✅ `payment_intent.succeeded` - One-time payment succeeded
   ✅ `invoice.payment_succeeded` - Subscription payment succeeded  
   ✅ `customer.subscription.created` - New subscription created
   ✅ `customer.subscription.updated` - Subscription updated
   ✅ `customer.subscription.deleted` - Subscription canceled
   ✅ `invoice.payment_failed` - Payment failed

5. **Click "Add endpoint"**

## Step 3: Get Your Webhook Secret

After creating the webhook:

1. **Click on your newly created webhook** in the list

2. **Find "Signing secret"** section

3. **Click "Reveal"** button

4. **Copy the secret** (starts with `whsec_`)

5. **Add it to your environment:**
   
   **For local development:**
   ```bash
   # Add to backend/.env
   STRIPE_WEBHOOK_SECRET=whsec_xxxxx
   ```
   
   **For Railway:**
   - Go to Railway Dashboard → Your backend service → Variables
   - Add: `STRIPE_WEBHOOK_SECRET` = `whsec_xxxxx`
   - Redeploy your service

## Step 4: Test Your Webhook

1. **In Stripe Dashboard → Webhooks → Your endpoint**

2. **Click "Send test webhook"** button

3. **Select an event** (e.g., `payment_intent.succeeded`)

4. **Click "Send test webhook"**

5. **Check the response:**
   - Should show "200 OK" if working
   - Check your server logs to see if it received the webhook

## Troubleshooting

### "Webhook endpoint returned an error"

- Check your server is running
- Check the URL is correct (must be HTTPS, not HTTP)
- Check your server logs for errors

### "Webhook not receiving events"

- Verify `STRIPE_WEBHOOK_SECRET` is set correctly
- Make sure you copied the secret from the correct webhook endpoint
- Restart your server after adding the secret

### "Invalid signature" error

- The webhook secret doesn't match
- Make sure you're using the secret from the correct webhook endpoint
- Don't mix test and live webhook secrets

## Quick Reference

**Webhook URL format:**
```
https://your-domain.com/api/webhooks/stripe
```

**Required events:**
- `payment_intent.succeeded`
- `invoice.payment_succeeded`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_failed`

**Environment variable:**
```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
```

## Need Help?

- Check Stripe Dashboard → Webhooks → Your endpoint → Recent events
- Look for failed deliveries and error messages
- Check your server logs for webhook processing errors


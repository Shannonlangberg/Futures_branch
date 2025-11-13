# Google Drive Resources Setup

Follow this guide to configure Google OAuth and Drive access for the new **Resources** tab. These steps assume you have access to the Futures Church Google Workspace and can create OAuth credentials in Google Cloud.

---

## 1. Create or reuse a Google Cloud project

1. Visit the [Google Cloud Console](https://console.cloud.google.com/).
2. Select the project you already use for Futures PULSE or create a new one dedicated to internal tools.
3. Ensure **Google Drive API** is enabled under *APIs & Services → Enabled APIs & services → Enable APIs and services*.

---

## 2. Configure the OAuth consent screen

1. Navigate to *APIs & Services → OAuth consent screen*.
2. Choose **Internal** (limited to your Google Workspace users).
3. Set the application name (e.g. `Futures PULSE Resources`), support email, and add your logo if desired.
4. Add the required scopes:
   - `https://www.googleapis.com/auth/drive.readonly`
5. Add Futures staff Google Workspace emails or groups to the **Test users** section while the app is in testing mode.
6. Save and submit for verification if you want production status (not required for internal use).

---

## 3. Create OAuth client credentials

1. Go to *APIs & Services → Credentials → Create credentials → OAuth client ID*.
2. Select **Web application**.
3. Add authorised redirect URIs:
   - Local development: `http://localhost:5000/api/google/callback`
   - Production: `https://pulse.futures.church/api/google/callback` (replace with your actual domain)
4. Download the client credentials or copy the **Client ID** and **Client secret**.

Update your environment variables (see `ENV_TEMPLATE.txt`):

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=https://pulse.futures.church/api/google/callback
```

If you want to customise the scopes or resource map path, also set:

```env
GOOGLE_DRIVE_RESOURCE_SCOPES=https://www.googleapis.com/auth/drive.readonly
GOOGLE_RESOURCES_MAP_PATH=/absolute/path/to/resources_map.json
```

Restart the backend server after updating environment variables.

---

## 4. Map Google Drive folders to categories

Copy `backend/config/resources_map.json` and populate the `folderId` values with the IDs from Google Drive:

```json
{
  "Finance": {
    "displayName": "Finance",
    "description": "Financial forms, reports, and templates for the finance team.",
    "folderId": "1A2B3C4D5EFG"
  },
  "HR": {
    "displayName": "HR",
    "description": "Human resources policies, onboarding documents, and leave request forms.",
    "folderId": "1H2I3J4K5LMN"
  }
}
```

Tips:

- To locate a folder ID, open the folder in Drive and copy the final segment of the URL.
- Shared drives are supported. Ensure the OAuth client email has at least **Viewer** access to the folders.
- You can add more categories or rename existing ones—each key becomes the category identifier displayed in the UI.

---

## 5. Test the OAuth flow

1. Start the backend (`flask run` or `python app.py`) and frontend (`npm run dev`).
2. Log into Futures PULSE with a role that can see the Resources tab.
3. Navigate to `/resources`, select a category, and click **Connect with Google** when prompted.
4. Complete the Google sign-in flow. The popup will close automatically and files from the mapped folder should appear.

If you encounter errors:

- Check backend logs for messages about missing configuration or Drive API errors.
- Ensure the redirect URI matches exactly between Google Cloud and your environment variable.
- Confirm the signed-in Google account has access to the shared folder.

---

## 6. Deployment considerations

- Store the client secret securely (e.g. environment variables or secret manager).
- If running multiple backend instances, verify they share the same database so token storage works consistently.
- Periodically review and prune stored tokens in the `google_oauth_tokens` table if staff membership changes.

---

With these steps complete, staff will have a clean, secure hub that surfaces Google Drive resources directly within Futures PULSE.



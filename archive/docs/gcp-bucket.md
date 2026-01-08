# GCP Cloud Storage Bucket Setup

Create Bucket: viralens-audio-files



This guide explains how to set up Google Cloud Storage (GCS) for storing audio files in the Viralens backend.

## Prerequisites

- A Google Cloud Platform (GCP) account
- `gcloud` CLI installed (optional, but recommended)

## Step 1: Create a GCP Project

1. Go to the [GCP Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "viralens")
5. Click "Create"

## Step 2: Enable Cloud Storage API

1. In the GCP Console, navigate to "APIs & Services" > "Library"
2. Search for "Cloud Storage API"
3. Click on it and click "Enable"

## Step 3: Create a Storage Bucket

1. Navigate to "Cloud Storage" > "Buckets" in the GCP Console
2. Click "Create Bucket"
3. Configure the bucket:
   - **Name**: Choose a unique bucket name (e.g., `viralens-audio-files`)
   - **Location type**: Choose "Region" or "Multi-region" based on your needs
   - **Location**: Select a region close to your users
   - **Storage class**: Standard is recommended
   - **Access control**: Choose "Uniform" (recommended) or "Fine-grained"
   - **Protection tools**: Configure as needed
4. Click "Create"

## Step 4: Create a Service Account

1. Navigate to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter details:
   - **Service account name**: `viralens-storage-service`
   - **Service account ID**: Auto-generated (or customize)
   - **Description**: "Service account for uploading audio files to GCS"
4. Click "Create and Continue"
5. Grant the following role:
   - **Storage Object Admin** (or `roles/storage.objectAdmin`)
   - This role allows creating, updating, and deleting objects in the bucket
6. Click "Continue" then "Done"

## Step 5: Create and Download Service Account Key

1. In the Service Accounts list, click on the service account you just created
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Click "Create"
6. The JSON key file will be downloaded to your computer
7. **Important**: Keep this file secure and never commit it to version control

## Step 6: Configure Environment Variables

Add the following environment variables to your `.env` file:

```bash
# GCP Bucket Configuration
GCP_BUCKET_NAME=your-bucket-name-here
GCP_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project-id",...}'
```

### Option A: Using the JSON file content directly

1. Open the downloaded JSON key file
2. Copy the entire JSON content
3. Paste it as a single-line string in your `.env` file (escape quotes if needed)
4. Example:
   ```bash
   GCP_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"viralens","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'
   ```

### Option B: Using a file path (if you modify the code)

Alternatively, you could modify the code to read from a file path, but the current implementation expects the JSON as a string.

## Step 7: Set Bucket Permissions (Optional)

If you want to ensure public access to uploaded files:

1. Go to your bucket in the GCP Console
2. Click on the "Permissions" tab
3. Add the following principal: `allUsers`
4. Grant the role: "Storage Object Viewer"
5. This allows public read access to objects (files are made public by default in the code)

**Note**: The current implementation automatically makes uploaded files public via `blob.make_public()`. If you want to keep files private, you'll need to modify the `GCSClient.upload_audio()` method.

## Step 8: Verify Setup

1. Ensure your `.env` file has both variables set:
   ```bash
   GCP_BUCKET_NAME=viralens-audio-files
   GCP_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
   ```

2. Test the connection by running your application and attempting to upload a file

3. Check the GCP Console to verify files are being uploaded to the bucket

## Troubleshooting

### Error: "Invalid service account key"
- Ensure the JSON is properly formatted and all quotes are escaped
- Verify the entire JSON is on a single line in the `.env` file
- Check that the JSON contains all required fields

### Error: "Bucket not found"
- Verify the bucket name matches exactly (case-sensitive)
- Ensure the service account has permissions to access the bucket
- Check that the bucket exists in the same project as the service account

### Error: "Permission denied"
- Verify the service account has the "Storage Object Admin" role
- Check that the bucket's IAM permissions include the service account

### Files not accessible publicly
- Ensure the bucket allows public access (if needed)
- Check that `blob.make_public()` is being called in the code
- Verify bucket-level permissions allow public reads

## Security Best Practices

1. **Never commit service account keys to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Use least privilege principle**
   - Only grant the minimum permissions needed
   - Consider using "Storage Object Creator" instead of "Storage Object Admin" if you don't need delete permissions

3. **Rotate keys regularly**
   - Create new keys periodically
   - Delete old unused keys

4. **Monitor access**
   - Enable Cloud Audit Logs
   - Review access logs regularly

5. **Consider using signed URLs** (future enhancement)
   - Instead of making files public, generate time-limited signed URLs
   - This provides better security for private content

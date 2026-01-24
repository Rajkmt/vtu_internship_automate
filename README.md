# VTU Incremental Application Fetcher

Automated system to fetch new internship applications from VTU Internyet API and send them to n8n webhook.

## How It Works

1. **Loads last processed ID** from `last_id.txt` (or starts from 0)
2. **Logs in** to VTU API using credentials
3. **Fetches applications** page by page until it finds IDs <= last processed ID
4. **Filters** only new applications (ID > last processed ID)
5. **Fetches full details** for each new application
6. **Updates** `last_id.txt` with the highest new ID
7. **Sends** data to n8n webhook

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export VTU_EMAIL="your-email@example.com"
export VTU_PASSWORD="your-password"
export N8N_WEBHOOK_URL="https://your-n8n.com/webhook/endpoint"
```

### 3. Run Locally

```bash
python3 fetch_new_applications.py
```

## GitHub Actions Setup

### 1. Add Secrets to GitHub Repository

Go to: `Settings → Secrets and variables → Actions → New repository secret`

Add these secrets:
- `VTU_EMAIL`: Your VTU admin email
- `VTU_PASSWORD`: Your VTU admin password
- `N8N_WEBHOOK_URL`: Your n8n webhook URL

### 2. Workflow Configuration

The workflow (`.github/workflows/fetch-applications.yml`) will:
- Run automatically every hour (cron schedule)
- Can be triggered manually (workflow_dispatch)
- Commits `last_id.txt` back to the repo after each run

### 3. First Run

On first run, `last_id.txt` doesn't exist, so it starts from ID 0 (fetches all applications).

**To start from a specific ID:**
1. Create `last_id.txt` with your desired starting ID
2. Commit it to the repo
3. The script will start from that ID

## File Structure

```
.
├── fetch_new_applications.py    # Main script
├── requirements.txt              # Python dependencies
├── last_id.txt                  # Last processed ID (auto-updated)
├── .github/
│   └── workflows/
│       └── fetch-applications.yml
└── README.md
```

## Output Format

The script sends this JSON to n8n webhook:

```json
{
  "lastProcessedId": 1813015,
  "applications": [
    {
      "id": 1813015,
      "message": "...",
      "status": 1,
      "created_at": "2026-01-24T18:42:58.000000Z",
      "internship": {
        "name": "Data Science Internship - Online Kodnest",
        "expire_date": "2026-05-31"
      },
      "student": {
        "name": "Akhilesh B Magdum",
        "email": "akhilesh.magadum2023@gmail.com",
        "mobile": "9606339691",
        "college": "DAYANANDA SAGAR COLLEGE OF ENGINEERING",
        "branch": "MCA",
        "skills": [...],
        "tags": [...]
      }
    }
  ]
}
```

## n8n Workflow

Your n8n workflow should:
1. Receive the webhook payload
2. Extract `applications` array
3. Append each application to Excel
4. Store `lastProcessedId` (optional, since script manages it)

## Manual ID Update

To manually set the last processed ID:
1. Edit `last_id.txt`
2. Set it to the desired ID (e.g., `1813000`)
3. Commit and push
4. Next run will start from that ID

## Troubleshooting

### Token Expired
- Script will exit with error
- Check credentials in GitHub Secrets
- Re-run the workflow

### Rate Limiting
- Script automatically waits and retries on 429 errors
- Adjust `DELAY_BETWEEN_REQUESTS` if needed

### No New Applications
- Script will still update `last_id.txt`
- Sends empty array to n8n (or skips if no data)

## Notes

- Applications are sorted by ID descending (newest first)
- Script stops pagination when it finds ID <= last processed ID
- Safety limit: 100 pages per run (prevents infinite loops)
- All API calls use same headers as `last_10_days_data.py`


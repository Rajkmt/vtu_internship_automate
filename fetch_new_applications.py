#!/usr/bin/env python3
"""
Incremental VTU Application Fetcher
- Logs in to VTU API
- Fetches only NEW applications (id > lastProcessedId)
- Sends to n8n webhook
- Updates last_id.txt for next run
"""

import json
import os
import time
import requests
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
LOGIN_URL = "https://vtuapi.internyet.in/api/v1/auth/login"
APPLICATIONS_URL = "https://vtuapi.internyet.in/api/v1/company/internship/applications"
DETAIL_URL = "https://vtuapi.internyet.in/api/v1/company/internship/application-detail"

# File to store last processed ID
LAST_ID_FILE = "last_id.txt"

# Headers (same as last_10_days_data.py)
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-GB,en;q=0.6",
    "connection": "keep-alive",
    "host": "vtuapi.internyet.in",
    "origin": "https://vtu.internyet.in",
    "referer": "https://vtu.internyet.in/",
    "sec-ch-ua": '"Brave";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
}

DELAY_BETWEEN_REQUESTS = 0.5
REQUEST_TIMEOUT = 30
MAX_PAGES_PER_RUN = 100  # Safety limit to prevent infinite loops

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def print_step(step_num, title):
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {title}")
    print("=" * 70)

def print_action(msg):
    print(f"→ {msg}")

def load_last_id():
    """Load last processed ID from file. Returns 0 if file doesn't exist."""
    if os.path.exists(LAST_ID_FILE):
        try:
            with open(LAST_ID_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return int(content)
        except (ValueError, IOError) as e:
            print(f"⚠ Warning: Could not read {LAST_ID_FILE}: {e}")
    return 0

def save_last_id(last_id):
    """Save last processed ID to file."""
    try:
        with open(LAST_ID_FILE, 'w') as f:
            f.write(str(last_id))
        print(f"✓ Saved last_id.txt: {last_id}")
    except IOError as e:
        print(f"✗ Error saving last_id.txt: {e}")
        raise

def login(email, password):
    """Login to VTU API and return cookies."""
    print_action(f"Logging in as {email}...")
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        resp = requests.post(
            LOGIN_URL,
            json=payload,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code != 200:
            print(f"✗ Login failed: Status {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
            raise Exception(f"Login failed with status {resp.status_code}")
        
        # Check if login was successful
        response_data = resp.json()
        if not response_data.get("success", False):
            print(f"✗ Login failed: {response_data.get('message', 'Unknown error')}")
            raise Exception("Login API returned success=false")
        
        # Extract cookies from response
        # Cookies are typically set in Set-Cookie headers or response.cookies
        cookies = {}
        
        # Method 1: Extract from response.cookies (requests library handles this)
        for cookie in resp.cookies:
            cookies[cookie.name] = cookie.value
        
        # Method 2: Parse Set-Cookie headers if needed
        set_cookie_header = resp.headers.get('Set-Cookie', '')
        if set_cookie_header and not cookies:
            # Parse Set-Cookie header manually if needed
            # Format: "name=value; Path=/; HttpOnly"
            for cookie_str in set_cookie_header.split(','):
                if '=' in cookie_str:
                    name_value = cookie_str.split(';')[0].strip()
                    if '=' in name_value:
                        name, value = name_value.split('=', 1)
                        cookies[name.strip()] = value.strip()
        
        # Verify we have access_token
        if 'access_token' not in cookies:
            print("⚠ Warning: access_token not found in cookies")
            print(f"  Cookies received: {list(cookies.keys())}")
            # Still continue, might work with other auth method
        
        print(f"✓ Login successful")
        print(f"  Cookies: {list(cookies.keys())}")
        
        # Return cookies dict (will be used in subsequent requests)
        return cookies
        
    except requests.exceptions.Timeout:
        print("✗ Login timeout")
        raise
    except Exception as e:
        print(f"✗ Login error: {e}")
        raise

def fetch_applications_page(cookies, page):
    """Fetch a single page of applications. Returns list of applications."""
    url = f"{APPLICATIONS_URL}?page={page}"
    
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            cookies=cookies,
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code == 401:
            raise Exception("Token expired (401)")
        
        if resp.status_code == 429:
            print(f"⚠ Rate limit (429) at page {page}. Waiting 15s...")
            time.sleep(15)
            return fetch_applications_page(cookies, page)  # Retry
        
        if resp.status_code != 200:
            raise Exception(f"Status {resp.status_code}")
        
        response_data = resp.json()
        if not response_data.get("success", False):
            raise Exception("API returned success=false")
        
        page_data = response_data.get("data", {})
        applications = page_data.get("data", [])
        
        return applications
        
    except requests.exceptions.Timeout:
        raise Exception("Timeout")
    except Exception as e:
        raise Exception(str(e))

def fetch_application_details(cookies, app_id):
    """Fetch full details for a single application ID."""
    url = f"{DETAIL_URL}?id={app_id}"
    
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            cookies=cookies,
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code == 401:
            raise Exception("Token expired (401)")
        
        if resp.status_code == 429:
            print(f"⚠ Rate limit (429) at ID {app_id}. Waiting 15s...")
            time.sleep(15)
            return fetch_application_details(cookies, app_id)  # Retry
        
        if resp.status_code != 200:
            raise Exception(f"Status {resp.status_code}")
        
        response_data = resp.json()
        if not response_data.get("success", False):
            raise Exception("API returned success=false")
        
        detail_data = response_data.get("data", {})
        return detail_data
        
    except requests.exceptions.Timeout:
        raise Exception("Timeout")
    except Exception as e:
        raise Exception(str(e))

def flatten_record(record):
    """Flatten nested application detail to flat structure for n8n/Excel."""
    flat = {}
    flat['id'] = record.get('id', '')
    flat['message'] = record.get('message', '')
    flat['status'] = record.get('status', '')
    flat['created_at'] = record.get('created_at', '')
    flat['offer_letter'] = record.get('offer_letter', '')
    
    internship = record.get('internship', {})
    if isinstance(internship, dict):
        flat['internship_name'] = internship.get('name', '')
    else:
        flat['internship_name'] = ''
    
    student = record.get('student', {})
    if isinstance(student, dict):
        flat['student_semester'] = student.get('semester', '')
        flat['student_linkedin'] = student.get('linkedin', '')
        flat['student_address'] = student.get('address', '')
        flat['student_pincode'] = student.get('pincode', '')
        flat['student_gender'] = student.get('gender', '')
        flat['student_dob'] = student.get('dob', '')
        flat['student_introduce_yourself'] = student.get('introduce_yourself', '')
        flat['student_bio'] = student.get('bio', '')
        flat['student_resume'] = student.get('resume', '')
        flat['student_name'] = student.get('name', '')
        flat['student_email'] = student.get('email', '')
        flat['student_mobile'] = student.get('mobile', '')
        flat['student_college'] = student.get('college', '')
        flat['student_branch'] = student.get('branch', '')
        flat['student_country'] = student.get('country', '')
        flat['student_state'] = student.get('state', '')
        flat['student_city'] = student.get('city', '')
        
        skills = student.get('skills', [])
        if isinstance(skills, list):
            skill_names = [s.get('name', '') if isinstance(s, dict) else str(s) for s in skills]
            flat['student_skills'] = ', '.join(skill_names)
        else:
            flat['student_skills'] = ''
        
        tags = student.get('tags', [])
        if isinstance(tags, list):
            tag_names = [t.get('name', '') if isinstance(t, dict) else str(t) for t in tags]
            flat['student_tags'] = ', '.join(tag_names)
        else:
            flat['student_tags'] = ''
    else:
        for field in ['semester', 'linkedin', 'address', 'pincode', 'gender', 'dob',
                     'introduce_yourself', 'bio', 'resume', 'name', 'email', 'mobile',
                     'college', 'branch', 'country', 'state', 'city', 'skills', 'tags']:
            flat[f'student_{field}'] = ''
    
    # Convert None to empty string and all values to strings
    for key in flat:
        if flat[key] is None:
            flat[key] = ''
        else:
            flat[key] = str(flat[key])
    
    return flat

def send_to_n8n(webhook_url, last_processed_id, applications):
    """Send flattened data to n8n webhook."""
    # Flatten all applications before sending
    flattened_apps = []
    for app in applications:
        flattened_apps.append(flatten_record(app))
    
    payload = {
        "lastProcessedId": last_processed_id,
        "applications": flattened_apps
    }
    
    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code == 200 or resp.status_code == 201:
            print(f"✓ Sent to n8n webhook: {len(flattened_apps)} applications")
            return True
        else:
            print(f"⚠ n8n webhook returned status {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error sending to n8n: {e}")
        return False

# ============================================================================
# MAIN SCRIPT
# ============================================================================
def main():
    print("=" * 70)
    print("VTU INCREMENTAL APPLICATION FETCHER")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get credentials from environment variables
    vtu_email = os.getenv("VTU_EMAIL")
    vtu_password = os.getenv("VTU_PASSWORD")
    n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
    
    if not vtu_email or not vtu_password:
        print("✗ Error: VTU_EMAIL and VTU_PASSWORD environment variables required")
        exit(1)
    
    if not n8n_webhook_url:
        print("✗ Error: N8N_WEBHOOK_URL environment variable required")
        exit(1)
    
    # ========================================================================
    # STEP 1: Load last processed ID
    # ========================================================================
    print_step(1, "LOADING LAST PROCESSED ID")
    last_processed_id = load_last_id()
    print(f"✓ Last processed ID: {last_processed_id if last_processed_id > 0 else 'None (first run)'}")
    
    # ========================================================================
    # STEP 2: Login
    # ========================================================================
    print_step(2, "LOGGING IN TO VTU API")
    try:
        cookies = login(vtu_email, vtu_password)
    except Exception as e:
        print(f"✗ Failed to login: {e}")
        exit(1)
    
    # ========================================================================
    # STEP 3: Fetch new applications (paginated)
    # ========================================================================
    print_step(3, "FETCHING NEW APPLICATIONS")
    print(f"→ Fetching pages until we find ID <= {last_processed_id}")
    print(f"→ Safety limit: {MAX_PAGES_PER_RUN} pages per run")
    
    new_application_ids = []
    page = 1
    found_old_id = False
    
    while page <= MAX_PAGES_PER_RUN and not found_old_id:
        try:
            applications = fetch_applications_page(cookies, page)
            
            if not applications:
                print(f"✓ Page {page}: No more applications. Finished.")
                break
            
            # Process applications on this page
            for app in applications:
                app_id = app.get('id')
                if not app_id:
                    continue
                
                app_id_int = int(app_id)
                
                if app_id_int > last_processed_id:
                    # New application
                    new_application_ids.append(app_id_int)
                    print(f"  ✓ Found new ID: {app_id_int}")
                else:
                    # Found old ID, stop pagination
                    print(f"  → Found old ID: {app_id_int} (<= {last_processed_id})")
                    found_old_id = True
                    break
            
            print(f"✓ Page {page}: {len(applications)} applications | New IDs so far: {len(new_application_ids)}")
            
            if found_old_id:
                break
            
            page += 1
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except Exception as e:
            print(f"✗ Page {page}: Error - {e}")
            # Continue to next page or exit?
            if "Token expired" in str(e):
                print("✗ Token expired. Please check credentials.")
                exit(1)
            page += 1
            time.sleep(5)
    
    if page > MAX_PAGES_PER_RUN:
        print(f"⚠ Reached safety limit of {MAX_PAGES_PER_RUN} pages")
    
    print(f"\n✓ Total new application IDs found: {len(new_application_ids)}")
    
    if not new_application_ids:
        print("→ No new applications. Updating last_id and exiting.")
        # Still update last_id in case it was manually changed
        # But don't send empty payload to n8n
        print("✓ No new data to send to n8n")
        return
    
    # ========================================================================
    # STEP 4: Fetch full details for new applications
    # ========================================================================
    print_step(4, f"FETCHING FULL DETAILS FOR {len(new_application_ids)} APPLICATIONS")
    
    application_details = []
    failed_ids = []
    
    for idx, app_id in enumerate(new_application_ids, 1):
        try:
            detail = fetch_application_details(cookies, app_id)
            if detail:
                application_details.append(detail)
                print(f"  ✓ ID {app_id}: Detail fetched ({idx}/{len(new_application_ids)})")
            else:
                print(f"  ⚠ ID {app_id}: Empty detail ({idx}/{len(new_application_ids)})")
                failed_ids.append(app_id)
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except Exception as e:
            print(f"  ✗ ID {app_id}: Error - {e} ({idx}/{len(new_application_ids)})")
            failed_ids.append(app_id)
    
    print(f"\n✓ Successfully fetched: {len(application_details)}/{len(new_application_ids)}")
    if failed_ids:
        print(f"⚠ Failed IDs: {failed_ids}")
    
    # ========================================================================
    # STEP 5: Calculate new last processed ID
    # ========================================================================
    print_step(5, "CALCULATING NEW LAST PROCESSED ID")
    
    if new_application_ids:
        new_last_id = max(new_application_ids)
        print(f"✓ New last processed ID: {new_last_id} (was {last_processed_id})")
    else:
        new_last_id = last_processed_id
        print(f"✓ No new IDs, keeping last processed ID: {new_last_id}")
    
    # ========================================================================
    # STEP 6: Save new last processed ID
    # ========================================================================
    print_step(6, "SAVING LAST PROCESSED ID")
    try:
        save_last_id(new_last_id)
    except Exception as e:
        print(f"✗ Failed to save last_id.txt: {e}")
        print("⚠ Continuing to send data to n8n...")
    
    # ========================================================================
    # STEP 7: Send to n8n webhook
    # ========================================================================
    print_step(7, "SENDING TO N8N WEBHOOK")
    
    if application_details:
        success = send_to_n8n(n8n_webhook_url, new_last_id, application_details)
        if success:
            print("✓ Successfully sent data to n8n")
        else:
            print("⚠ Warning: n8n webhook may have failed")
    else:
        print("→ No application details to send")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Last processed ID: {last_processed_id} → {new_last_id}")
    print(f"✓ New applications found: {len(new_application_ids)}")
    print(f"✓ Details fetched: {len(application_details)}")
    print(f"✓ Sent to n8n: {len(application_details)} applications")
    print(f"✓ Process complete!")
    print(f"Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    main()


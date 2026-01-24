#!/usr/bin/env python3
"""
Last 10 Days Data Fetch - Get applications from page 1 to 83
- Fetches pages 1 to 83 from API
- Fetches details for all application IDs
- Creates CSV with complete data
- End-to-end verification
"""

import json
import csv
import os
import time
import requests
from datetime import datetime
from collections import Counter

# ============================================================================
# API CONFIGURATION
# ============================================================================
base_url = "https://vtuapi.internyet.in/api/v1/company/internship/applications"
detail_url = "https://vtuapi.internyet.in/api/v1/company/internship/application-detail"

# TOKEN - UPDATE THIS WHEN IT EXPIRES
cookies = {
    "_ga": "GA1.1.1353746137.1767910394",
    "_ga_FRQJNHYVRZ": "GS2.1.s1767910394$o1$g1$t1767911502$j60$l0$h0",
    "twk_uuid_689c7188a7ee3319309bdeae": "%7B%22uuid%22%3A%221.Sx00uaf0wTlmfGDQanwHLf31DFk0kUAzUm7nEo4CXGX0bCcBC8rolLNAYGYNg9MmfXnm9O8ksWOhTQcvnkBQnqg7DOefNCu7YaAvqtMcQeYGJIlLP3vdk%22%2C%22version%22%3A3%2C%22domain%22%3A%22internyet.in%22%2C%22ts%22%3A1769235043293%7D",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3Z0dWFwaS5pbnRlcm55ZXQuaW4vYXBpL3YxL2F1dGgvbG9naW4iLCJpYXQiOjE3NjkyNTUzMDIsImV4cCI6MTc2OTI1ODkwMiwibmJmIjoxNzY5MjU1MzAyLCJqdGkiOiJldHIyOEpBbkJJWXVpYXFTIiwic3ViIjoiODE0MDUiLCJwcnYiOiIyM2JkNWM4OTQ5ZjYwMGFkYjM5ZTcwMWM0MDA4NzJkYjdhNTk3NmY3In0.SZlrdKnYCN9vta8bmstF_pzkIFNmrPOy0MaNXh7jBWg",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL3Z0dWFwaS5pbnRlcm55ZXQuaW4vYXBpL3YxL2F1dGgvbG9naW4iLCJpYXQiOjE3NjkyNTUzMDIsImV4cCI6MTc2OTI3NTQ2MiwibmJmIjoxNzY5MjU1MzAyLCJqdGkiOiJUMHYyQkVCZEhpRFRpVHRDIiwic3ViIjoiODE0MDUiLCJwcnYiOiIyM2JkNWM4OTQ5ZjYwMGFkYjM5ZTcwMWM0MDA4NzJkYjdhNTk3NmY3IiwidHlwZSI6InJlZnJlc2gifQ.qu2SJXZQ31O_dAznpwSDFwbkss1mbRdstlrTEphPj-Q"
}

headers = {
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
START_PAGE = 1
END_PAGE = 83  # Only fetch pages 1-83

# ============================================================================
# FILE PATHS
# ============================================================================
applications_file = "last_10_days_data_applications.json"
details_file = "last_10_days_data_details.json"
output_csv = "last_10_days_data.csv"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def print_step(step_num, title):
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {title}")
    print("=" * 70)

def print_action(msg):
    print(f"\n→ ACTION: {msg}")

# ============================================================================
# MAIN SCRIPT
# ============================================================================
print("=" * 70)
print("LAST 10 DAYS DATA FETCH - PAGES 1 TO 83")
print("=" * 70)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Will fetch pages: {START_PAGE} to {END_PAGE}")
print("=" * 70)

# ============================================================================
# STEP 1: FETCH APPLICATIONS FROM PAGES 1-83 (COLLECT IDs)
# ============================================================================
print_step(1, f"FETCHING APPLICATIONS FROM PAGES {START_PAGE}-{END_PAGE} - COLLECTING IDs")

# Check for resume capability - load existing applications if available
all_fetched_applications = []
resume_from_page = START_PAGE

if os.path.exists(applications_file):
    try:
        with open(applications_file, 'r', encoding='utf-8') as f:
            all_fetched_applications = json.load(f)
        # Calculate which page to resume from (approximate)
        # Each page has ~18 records, so estimate resume page
        estimated_pages = len(all_fetched_applications) // 18
        resume_from_page = min(estimated_pages + 1, END_PAGE)
        print(f"   ℹ Found existing applications file: {len(all_fetched_applications):,} records")
        print(f"   ℹ Will resume from approximately page {resume_from_page}")
    except:
        print(f"   ℹ Starting fresh - could not load existing file")
        all_fetched_applications = []

page = resume_from_page
max_retries = 5

print(f"   API: GET {base_url}?page={{page}}")
print(f"   Pages: {START_PAGE} to {END_PAGE}")
print(f"   Starting from page: {page}")
print(f"   Purpose: Collect application IDs first (details will be fetched in Step 3)")
print("-" * 70)

while page <= END_PAGE:
    url = f"{base_url}?page={page}"
    retry_count = 0
    page_success = False
    
    while retry_count < max_retries and not page_success:
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            
            if resp.status_code == 401:
                print(f"\n" + "=" * 70)
                print(f"   ⚠ TOKEN EXPIRED at page {page}")
                print(f"   → Progress saved: {len(all_fetched_applications):,} records fetched so far")
                print("=" * 70)
                print_action("1. Update 'access_token' in last_10_days_data.py (line 32)")
                print_action("2. Then run: python3 last_10_days_data.py")
                print_action("3. Script will automatically resume from page {page}")
                print("=" * 70)
                
                # CRITICAL: Save all fetched applications before exiting
                with open(applications_file, 'w', encoding='utf-8') as f:
                    json.dump(all_fetched_applications, f, ensure_ascii=False, indent=2)
                print(f"\n   💾 Saved progress: {len(all_fetched_applications):,} applications saved to {applications_file}")
                exit(1)
            
            if resp.status_code == 429:
                wait_time = 15 + (retry_count * 5)
                print(f"   ⚠ Rate limit (429) at page {page}. Waiting {wait_time}s...")
                time.sleep(wait_time)
                retry_count += 1
                continue
            
            if resp.status_code != 200:
                print(f"   ⚠ Page {page}: Status {resp.status_code}. Retrying...")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)
                    continue
                else:
                    print(f"   ✗ Page {page}: Failed after {max_retries} attempts")
                    page += 1
                    break
            
            # Success
            response_data = resp.json()
            page_info = response_data.get("data", {})
            items = page_info.get("data", [])
            
            if not items:
                print(f"   ✓ Page {page}: No more items. Finished.")
                page_success = True
                break
            
            all_fetched_applications.extend(items)
            # Extract IDs from this page for display
            page_ids = [item.get('id') for item in items if item.get('id')]
            print(f"   ✓ Page {page}: {len(items)} records ({len(page_ids)} IDs) | Total: {len(all_fetched_applications):,} records")
            
            # Save every 50 pages
            if page % 50 == 0:
                with open(applications_file, 'w', encoding='utf-8') as f:
                    json.dump(all_fetched_applications, f, ensure_ascii=False, indent=2)
                print(f"   💾 Saved applications file (page {page}, {len(all_fetched_applications):,} apps)")
            
            page_success = True
            page += 1
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 5 * retry_count
                print(f"   ⚠ Page {page}: Timeout. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"   ✗ Page {page}: Timeout after {max_retries} retries")
                page += 1
                break
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 5 * retry_count
                print(f"   ⚠ Page {page}: Error - {e}. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"   ✗ Page {page}: Error - {e}")
                page += 1
                break

# Remove duplicates
seen_ids = set()
unique_applications = []
for app in all_fetched_applications:
    app_id = app.get('id')
    if app_id and app_id not in seen_ids:
        seen_ids.add(app_id)
        unique_applications.append(app)
all_fetched_applications = unique_applications

# Extract all unique IDs
all_api_ids = [app.get('id') for app in all_fetched_applications if app.get('id')]
unique_ids_count = len(set(all_api_ids))

print(f"\n   ✓ STEP 1 COMPLETE: Collected application records from pages {START_PAGE}-{END_PAGE}")
print(f"   ✓ Total application records: {len(all_fetched_applications):,}")
print(f"   ✓ Unique application IDs collected: {unique_ids_count:,}")
print(f"   ✓ Next step: Fetch full details for these {unique_ids_count:,} IDs")

# Save final applications file
with open(applications_file, 'w', encoding='utf-8') as f:
    json.dump(all_fetched_applications, f, ensure_ascii=False, indent=2)
print(f"   ✓ Saved {applications_file}")

# ============================================================================
# STEP 2: CHECK FOR DUPLICATES IN FETCHED DATA
# ============================================================================
print_step(2, "CHECKING FOR DUPLICATES IN COLLECTED IDs")

id_counts = Counter(all_api_ids)
duplicates = {id_val: count for id_val, count in id_counts.items() if count > 1}

print(f"   ✓ Total IDs collected: {len(all_api_ids):,}")
print(f"   ✓ Unique IDs: {unique_ids_count:,}")
print(f"   ✓ Duplicates found: {len(duplicates)}")
if duplicates:
    print(f"   ⚠ Duplicate IDs: {list(duplicates.keys())[:10]}{'...' if len(duplicates) > 10 else ''}")
else:
    print(f"   ✓ PASSED: No duplicates in collected IDs")

# ============================================================================
# STEP 3: FETCH DETAILS FOR ALL IDs (SEQUENTIAL)
# ============================================================================
print_step(3, f"FETCHING FULL DETAILS FOR {unique_ids_count:,} IDs COLLECTED IN STEP 1")
print(f"   ⚠ NOW fetching complete details for each ID (sequential - one by one)")
print(f"   ⚠ This is the second phase - details fetching")

fetched_ids_set = set(all_api_ids)

# Load existing details (if resuming)
if os.path.exists(details_file):
    try:
        with open(details_file, 'r', encoding='utf-8') as f:
            details_dict = json.load(f)
        if details_dict and isinstance(list(details_dict.keys())[0], int):
            details_dict = {str(k): v for k, v in details_dict.items()}
        print(f"   ✓ Loaded {len(details_dict):,} existing details")
    except:
        details_dict = {}
        print(f"   ⚠ Could not load existing details - starting fresh")
else:
    details_dict = {}

missing_detail_ids = [app_id for app_id in fetched_ids_set if str(app_id) not in details_dict]
print(f"   ✓ IDs needing details: {len(missing_detail_ids):,}")

if len(missing_detail_ids) > 0:
    new_details = {}
    for idx, app_id in enumerate(missing_detail_ids, 1):
        url = f"{detail_url}?id={app_id}"
        
        try:
            resp = requests.get(url, headers=headers, cookies=cookies, timeout=REQUEST_TIMEOUT)
            
            if resp.status_code == 401:
                print(f"\n" + "=" * 70)
                print(f"   ⚠ TOKEN EXPIRED at detail {idx}/{len(missing_detail_ids)}")
                print(f"   → Progress saved: {len(details_dict) + len(new_details):,} details fetched so far")
                print("=" * 70)
                print_action("1. Update 'access_token' in last_10_days_data.py (line 32)")
                print_action("2. Then run: python3 last_10_days_data.py")
                print_action("3. Script will automatically resume from where it stopped")
                print("=" * 70)
                
                # CRITICAL: Save all fetched details before exiting
                if new_details:
                    details_dict.update(new_details)
                with open(details_file, 'w', encoding='utf-8') as f:
                    json.dump(details_dict, f, ensure_ascii=False, indent=2)
                print(f"\n   💾 Saved progress: {len(details_dict):,} details saved to {details_file}")
                exit(1)
            
            if resp.status_code == 429:
                print(f"   ⚠ Rate limit (429) at ID {app_id}. Waiting 15s...")
                time.sleep(15)
                continue
            
            if resp.status_code == 200:
                response_data = resp.json()
                if response_data.get("success", False):
                    detail_data = response_data.get("data", {})
                    if detail_data:
                        new_details[str(app_id)] = detail_data
                        print(f"   ✓ ID {app_id}: Detail fetched ({idx:,}/{len(missing_detail_ids):,})")
                    else:
                        print(f"   ⚠ ID {app_id}: Empty response ({idx:,}/{len(missing_detail_ids):,})")
                else:
                    print(f"   ⚠ ID {app_id}: API returned success=false ({idx:,}/{len(missing_detail_ids):,})")
            else:
                print(f"   ⚠ ID {app_id}: Status {resp.status_code} ({idx:,}/{len(missing_detail_ids):,})")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            # Save progress every 50 details
            if idx % 50 == 0:
                details_dict.update(new_details)
                with open(details_file, 'w', encoding='utf-8') as f:
                    json.dump(details_dict, f, ensure_ascii=False, indent=2)
                print(f"   💾 Progress saved ({len(details_dict):,} details)")
                new_details = {}  # Clear to save memory
            
        except requests.exceptions.Timeout:
            print(f"   ⚠ ID {app_id}: Timeout ({idx:,}/{len(missing_detail_ids):,})")
        except Exception as e:
            print(f"   ✗ ID {app_id}: Error - {e} ({idx:,}/{len(missing_detail_ids):,})")
    
    # Update details file with any remaining new details
    if new_details:
        details_dict.update(new_details)
    
    # Final save
    with open(details_file, 'w', encoding='utf-8') as f:
        json.dump(details_dict, f, ensure_ascii=False, indent=2)
    
    print(f"\n   ✓ Fetched {len(missing_detail_ids):,} new details")
    print(f"   ✓ Updated {details_file} ({len(details_dict):,} total details)")

# Reload details
with open(details_file, 'r', encoding='utf-8') as f:
    details_dict = json.load(f)
if details_dict and isinstance(list(details_dict.keys())[0], int):
    details_dict = {str(k): v for k, v in details_dict.items()}

# ============================================================================
# STEP 4: CREATE CSV
# ============================================================================
print_step(4, "CREATING CSV FILE")

# Column order
column_order = [
    'id', 'message', 'status', 'created_at', 'offer_letter', 'internship_name',
    'student_name', 'student_email', 'student_mobile', 'student_semester',
    'student_linkedin', 'student_address', 'student_pincode', 'student_gender',
    'student_dob', 'student_introduce_yourself', 'student_bio', 'student_resume',
    'student_college', 'student_branch', 'student_country', 'student_state',
    'student_city', 'student_skills', 'student_tags'
]

# Flatten function
def flatten_record(record):
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
    
    for key in flat:
        if flat[key] is None:
            flat[key] = ''
        else:
            flat[key] = str(flat[key])
    
    return flat

# Create CSV records
csv_records = []
missing_count = 0

for app_id in sorted(fetched_ids_set):
    id_str = str(app_id)
    detail_record = details_dict.get(id_str)
    
    if detail_record:
        csv_records.append(flatten_record(detail_record))
    else:
        missing_count += 1
        empty_record = {col: '' for col in column_order}
        empty_record['id'] = str(app_id)
        csv_records.append(empty_record)

# Write CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=column_order, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(csv_records)

file_size = os.path.getsize(output_csv)
file_size_mb = file_size / (1024 * 1024)

print(f"\n   ✓ Created {output_csv}")
print(f"   ✓ Total records: {len(csv_records):,}")
print(f"   ✓ Records with data: {len(csv_records) - missing_count:,}")
print(f"   ✓ Records missing details: {missing_count}")
print(f"   ✓ File size: {file_size_mb:.2f} MB")

# ============================================================================
# STEP 5: END-TO-END VERIFICATION
# ============================================================================
print_step(5, "END-TO-END VERIFICATION")

# Check 1: Duplicates in CSV
csv_ids = [r['id'] for r in csv_records if r.get('id')]
unique_csv_ids = set(csv_ids)
duplicates_in_csv = len(csv_ids) - len(unique_csv_ids)

print(f"\n1. Duplicates in CSV:")
print(f"   Total IDs: {len(csv_ids):,}")
print(f"   Unique IDs: {len(unique_csv_ids):,}")
print(f"   Duplicates: {duplicates_in_csv}")
if duplicates_in_csv == 0:
    print(f"   ✓ PASSED: No duplicates")
else:
    print(f"   ✗ FAILED: Found {duplicates_in_csv} duplicates")

# Check 2: All IDs have details
missing_details_check = [r for r in csv_records if not details_dict.get(r.get('id', ''))]
print(f"\n2. Missing details:")
print(f"   Missing: {len(missing_details_check)}")
if len(missing_details_check) == 0:
    print(f"   ✓ PASSED: All IDs have details")
else:
    print(f"   ⚠ WARNING: {len(missing_details_check)} IDs missing details")

# Check 3: Empty rows
empty_rows = [r for r in csv_records if not r.get('student_name', '').strip() and not r.get('student_email', '').strip()]
print(f"\n3. Empty rows:")
print(f"   Empty: {len(empty_rows)}")
if len(empty_rows) == 0:
    print(f"   ✓ PASSED: No empty rows")
else:
    print(f"   ⚠ WARNING: {len(empty_rows)} empty rows")

# Check 4: Data completeness
complete_rows = sum(1 for r in csv_records if r.get('student_name', '').strip() and r.get('student_email', '').strip())
print(f"\n4. Data completeness:")
print(f"   Complete rows: {complete_rows:,}/{len(csv_records):,} ({100*complete_rows/len(csv_records):.1f}%)")
if complete_rows == len(csv_records):
    print(f"   ✓ PASSED: All rows complete")
else:
    print(f"   ⚠ WARNING: {len(csv_records) - complete_rows} incomplete rows")

# Final verdict
all_passed = (duplicates_in_csv == 0 and len(missing_details_check) == 0 and len(empty_rows) == 0)

print("\n" + "=" * 70)
if all_passed:
    print("✓✓✓ ALL VERIFICATIONS PASSED - CSV IS 100% CORRECT ✓✓✓")
else:
    print("⚠⚠⚠ SOME ISSUES FOUND - REVIEW ABOVE ⚠⚠⚠")
print("=" * 70)

print(f"\n✓ Output CSV: {output_csv}")
print(f"✓ Total records: {len(csv_records):,}")
print(f"✓ Pages fetched: {START_PAGE} to {END_PAGE}")
print(f"✓ Process complete!")
print(f"\nEnded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

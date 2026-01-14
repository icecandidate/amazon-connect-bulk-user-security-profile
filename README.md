## Amazon Connect Bulk User Security Profile Updater
At the time of writing, Amazon Connect has a limitation where you can only bulk update the security profile for up to 100 users simultaneously via the UI. When performing large scale user migrations this limit is quickly hit.

The Amazon Connect Bulk Security Profile Updater uses the AWS CLI and takes in a CSV file with the username and a target security profile id. The script searches for the username and returns the user id. Assuming the user is found, the script then updates the target security profile of the user with the supplied security profile id. 

### Usage

```python connect_security_profile_updater.py --instance-id 12345678-1234-1234-1234-123456789012 --csv-file users.csv```

The script can easily be updated to take an AWS CLI profile or it can be run from CloudShell. I've tested the script with 7000 users without issue.

### Logging
Example log entries:
```
===========================================================
2025-08-11 15:14:21,691 - INFO - Amazon Connect Security Profile Updater Started
2025-08-11 15:14:21,691 - INFO - ============================================================
2025-08-11 15:14:21,691 - INFO - Instance ID: 12345678-1234-1234-1234-123456789012
2025-08-11 15:14:21,691 - INFO - CSV File: users.csv
2025-08-11 15:14:21,691 - INFO - Log File: connect_security_update_20250811_151421.log
2025-08-11 15:14:21,692 - INFO - Detected header row, skipping...
2025-08-11 15:14:23,333 - INFO - SUCCESS: Updated user user@user.com (ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890) with security profile a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

```
============================================================
2025-08-11 15:14:38,040 - INFO - SUMMARY
2025-08-11 15:14:38,040 - INFO - ============================================================
2025-08-11 15:14:38,040 - INFO - Total processed: 500
2025-08-11 15:14:38,040 - INFO - Successful updates: 500
2025-08-11 15:14:38,040 - INFO - Failed updates: 0
2025-08-11 15:14:38,040 - INFO - All updates completed successfully!
```
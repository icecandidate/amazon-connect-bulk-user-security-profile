#!/usr/bin/env python3
"""
Amazon Connect Security Profile Updater
This script updates user security profiles in Amazon Connect using AWS CLI.
It reads usernames and security profile ids from a CSV file. It then searches Amazon Connect
for that username and finds the matching userid. The script then updates the security profile id
for that user.
"""

import argparse
import csv
import subprocess
import logging
import sys
import os
import json
from datetime import datetime


def setup_logging():
    """Setup logging configuration with timestamped log file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"connect_security_update_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_filename

def search_user_by_username(instance_id, username):
    """
    Search for a user by username to get their user ID.
    """
    try:
        search_criteria = f'StringCondition={{FieldName=Username,Value={username},ComparisonType=EXACT}}'
        
        cmd = [
            'aws', 'connect', 'search-users',
            '--instance-id', instance_id,
            '--search-criteria', search_criteria
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        response = json.loads(result.stdout)
        users = response.get('Users', [])
        
        if not users:
            return None, f"No user found with username: {username}"
        
        if len(users) > 1:
            return None, f"Multiple users found with username: {username}"
        
        user_id = users[0].get('Id')
        if not user_id:
            return None, f"User ID not found in response for username: {username}"
        
        return user_id, None
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else f"Search command failed with return code {e.returncode}"
        return None, error_msg
    except subprocess.TimeoutExpired:
        return None, "Search command timed out after 30 seconds"
    except json.JSONDecodeError as e:
        return None, f"Failed to parse search response: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error during search: {str(e)}"


def update_user_security_profile(instance_id, user_id, security_profile_id):
    """
    Update a single user's security profile using AWS CLI.
    """
    try:
        cmd = [
            'aws', 'connect', 'update-user-security-profiles',
            '--instance-id', instance_id,
            '--user-id', user_id,
            '--security-profile-ids', security_profile_id
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        return True, None
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else f"Command failed with return code {e.returncode}"
        return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 30 seconds"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def validate_csv_file(csv_file_path):
    """Validate that the CSV file exists and is readable."""
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
    
    if not os.access(csv_file_path, os.R_OK):
        raise PermissionError(f"Cannot read CSV file: {csv_file_path}")


def process_csv_file(instance_id, csv_file_path):
    """
    Process the CSV file and update user security profiles.
    """
    success_count = 0
    error_count = 0
    
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        # Check if first row is header
        first_row = next(reader, None)
        if not first_row:
            logging.warning("CSV file is empty")
            return success_count, error_count
        
        # Skip header row if it contains column names
        if first_row[0].lower() in ['user_id', 'userid', 'username'] and len(first_row) > 1:
            logging.info("Detected header row, skipping...")
        else:
            # Process first row as data
            if len(first_row) >= 2:
                username = first_row[0].strip()
                security_profile_id = first_row[1].strip()
                
                if username and security_profile_id:
                    # Search for user ID by username
                    user_id, search_error = search_user_by_username(instance_id, username)
                    
                    if user_id:
                        success, error = update_user_security_profile(instance_id, user_id, security_profile_id)
                        if success:
                            logging.info(f"SUCCESS: Updated user {username} (ID: {user_id}) with security profile {security_profile_id}")
                            success_count += 1
                        else:
                            logging.error(f"FAILED: User {username} (ID: {user_id}), Security Profile {security_profile_id} - {error}")
                            error_count += 1
                    else:
                        logging.error(f"FAILED: Could not find user {username} - {search_error}")
                        error_count += 1
                else:
                    logging.warning(f"Skipping row with empty values: {first_row}")
        
        # Process remaining rows
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 2:
                logging.warning(f"Row {row_num}: Insufficient columns, skipping: {row}")
                continue
            
            username = row[0].strip()
            security_profile_id = row[1].strip()
            
            if not username or not security_profile_id:
                logging.warning(f"Row {row_num}: Empty values, skipping: {row}")
                continue
            
            # Search for user ID by username
            user_id, search_error = search_user_by_username(instance_id, username)
            
            if user_id:
                success, error = update_user_security_profile(instance_id, user_id, security_profile_id)
                if success:
                    logging.info(f"SUCCESS: Updated user {username} (ID: {user_id}) with security profile {security_profile_id}")
                    success_count += 1
                else:
                    logging.error(f"FAILED: User {username} (ID: {user_id}), Security Profile {security_profile_id} - {error}")
                    error_count += 1
            else:
                logging.error(f"FAILED: Could not find user {username} - {search_error}")
                error_count += 1
    
    return success_count, error_count


def main():
    parser = argparse.ArgumentParser(
        description='Update Amazon Connect user security profiles from CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python connect_security_profile_updater.py --instance-id 12345678-1234-1234-1234-123456789012 --csv-file users.csv

CSV file format:
  username,security_profile_id
  john.doe,a1b2c3d4-e5f6-7890-abcd-ef1234567890
        '''
    )
    
    parser.add_argument(
        '--instance-id',
        required=True,
        help='Amazon Connect instance ID or ARN'
    )
    
    parser.add_argument(
        '--csv-file',
        required=True,
        help='Path to CSV file containing username and security_profile_id columns'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_filename = setup_logging()
    
    logging.info("=" * 60)
    logging.info("Amazon Connect Security Profile Updater Started")
    logging.info("=" * 60)
    logging.info(f"Instance ID: {args.instance_id}")
    logging.info(f"CSV File: {args.csv_file}")
    logging.info(f"Log File: {log_filename}")
    
    try:
        # Validate inputs
        validate_csv_file(args.csv_file)
        
        # Process the CSV file
        success_count, error_count = process_csv_file(args.instance_id, args.csv_file)
        
        # Summary
        total_processed = success_count + error_count
        logging.info("=" * 60)
        logging.info("SUMMARY")
        logging.info("=" * 60)
        logging.info(f"Total processed: {total_processed}")
        logging.info(f"Successful updates: {success_count}")
        logging.info(f"Failed updates: {error_count}")
        
        if error_count > 0:
            logging.warning(f"Process completed with {error_count} errors. Check log for details.")
            sys.exit(1)
        else:
            logging.info("All updates completed successfully!")
            
    except FileNotFoundError as e:
        logging.error(f"File error: {e}")
        sys.exit(1)
    except PermissionError as e:
        logging.error(f"Permission error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import csv
from datetime import datetime
import os
from collections import defaultdict

app = Flask(__name__)
CORS(app)

PATH = 'all excels/'
##> ------ Karthik Sarode : karthik.sarode23@gmail.com - UI for excel files ------
@app.route('/')
def home():
    """Displays the home page of the application."""
    return render_template('index.html')

@app.route('/applied-jobs', methods=['GET'])
def get_applied_jobs():
    '''
    Retrieves a list of applied jobs from the applications history CSV file.
    
    Returns a JSON response containing a list of jobs, each with details such as 
    Job ID, Title, Company, HR Name, HR Link, Job Link, External Job link, and Date Applied.
    
    If the CSV file is not found, returns a 404 error with a relevant message.
    If any other exception occurs, returns a 500 error with the exception message.
    '''

    try:
        jobs = []
        with open(PATH + 'all_applied_applications_history.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                jobs.append({
                    'Job_ID': row['Job ID'],
                    'Title': row['Title'],
                    'Company': row['Company'],
                    'HR_Name': row['HR Name'],
                    'HR_Link': row['HR Link'],
                    'Job_Link': row['Job Link'],
                    'External_Job_link': row['External Job link'],
                    'Date_Applied': row['Date Applied']
                })
        return jsonify(jobs)
    except FileNotFoundError:
        return jsonify({"error": "No applications history found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applied-jobs/<job_id>', methods=['PUT'])
def update_applied_date(job_id):
    """
    Updates the 'Date Applied' field of a job in the applications history CSV file.

    Args:
        job_id (str): The Job ID of the job to be updated.

    Returns:
        A JSON response with a message indicating success or failure of the update
        operation. If the job is not found, returns a 404 error with a relevant
        message. If any other exception occurs, returns a 500 error with the
        exception message.
    """
    try:
        data = []
        csvPath = PATH + 'all_applied_applications_history.csv'
        
        if not os.path.exists(csvPath):
            return jsonify({"error": f"CSV file not found at {csvPath}"}), 404
            
        # Read current CSV content
        with open(csvPath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldNames = reader.fieldnames
            found = False
            for row in reader:
                if row['Job ID'] == job_id:
                    row['Date Applied'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    found = True
                data.append(row)
        
        if not found:
            return jsonify({"error": f"Job ID {job_id} not found"}), 404

        with open(csvPath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldNames)
            writer.writeheader()
            writer.writerows(data)
        
        return jsonify({"message": "Date Applied updated successfully"}), 200
    except Exception as e:
        print(f"Error updating applied date: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/analytics/messages', methods=['GET'])
def get_messages():
    '''
    Retrieves a list of all recruiter messages from the history CSV file.
    '''
    try:
        messages = []
        csv_path = 'all excels/recruiter_messages_history.csv'
        if not os.path.exists(csv_path):
            return jsonify({"error": "No message history found"}), 404

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                messages.append({
                    'Message ID': row['Message ID'],
                    'Job ID': row['Job ID'],
                    'Job Title': row['Job Title'],
                    'Company': row['Company'],
                    'Job Link': row['Job Link'],
                    'Recruiter Name': row['Recruiter Name'],
                    'Recruiter Title': row['Recruiter Title'],
                    'Recruiter ID': row['Recruiter ID'],
                    'Recruiter Profile Link': row['Recruiter Profile Link'],
                    'Message Type': row['Message Type'],
                    'Subject': row['Subject'],
                    'Message Body': row['Message Body'],
                    'Date Sent': row['Date Sent'],
                    'Status': row['Status'],
                    'Skip Reason': row['Skip Reason'],
                    'Error Message': row['Error Message'],
                    'Template Name': row['Template Name'],
                    'Response Received': row['Response Received'],
                    'Response Date': row['Response Date']
                })
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analytics/summary', methods=['GET'])
def get_summary():
    '''
    Provides summary analytics for recruiter messaging.
    '''
    try:
        csv_path = 'all excels/recruiter_messages_history.csv'
        if not os.path.exists(csv_path):
            return jsonify({"error": "No message history found"}), 404

        total_messages = 0
        sent_messages = 0
        skipped_messages = 0
        failed_messages = 0
        responses_received = 0
        templates_used = defaultdict(int)
        companies_messaged = set()
        recruiters_messaged = set()

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                total_messages += 1
                status = row['Status']
                if status == 'Sent':
                    sent_messages += 1
                    companies_messaged.add(row['Company'])
                    recruiters_messaged.add(row['Recruiter ID'])
                elif status == 'Skipped':
                    skipped_messages += 1
                elif status == 'Failed':
                    failed_messages += 1

                if row['Response Received'].lower() in ('yes', 'true', '1'):
                    responses_received += 1

                template = row['Template Name']
                if template:
                    templates_used[template] += 1

        response_rate = (responses_received / sent_messages * 100) if sent_messages > 0 else 0

        return jsonify({
            'total_messages': total_messages,
            'sent_messages': sent_messages,
            'skipped_messages': skipped_messages,
            'failed_messages': failed_messages,
            'response_rate': round(response_rate, 2),
            'responses_received': responses_received,
            'unique_companies': len(companies_messaged),
            'unique_recruiters': len(recruiters_messaged),
            'templates_used': dict(templates_used)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analytics/templates', methods=['GET'])
def get_template_analytics():
    '''
    Provides analytics on template effectiveness.
    '''
    try:
        csv_path = 'all excels/recruiter_messages_history.csv'
        if not os.path.exists(csv_path):
            return jsonify({"error": "No message history found"}), 404

        template_stats = defaultdict(lambda: {'sent': 0, 'responses': 0, 'response_rate': 0})

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                template = row['Template Name']
                if not template:
                    continue
                if row['Status'] == 'Sent':
                    template_stats[template]['sent'] += 1
                    if row['Response Received'].lower() in ('yes', 'true', '1'):
                        template_stats[template]['responses'] += 1

        # Calculate response rates
        for template, stats in template_stats.items():
            if stats['sent'] > 0:
                stats['response_rate'] = round(stats['responses'] / stats['sent'] * 100, 2)
            else:
                stats['response_rate'] = 0

        return jsonify(dict(template_stats))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analytics/messages/<message_id>/response', methods=['PUT'])
def update_response(message_id):
    """
    Updates the response status for a specific message.
    Expected JSON: {"response_received": true/false, "response_date": "YYYY-MM-DD HH:MM:SS"} (optional)
    """
    try:
        data = request.get_json()
        if not data or 'response_received' not in data:
            return jsonify({"error": "Missing 'response_received' field"}), 400

        response_received = 'Yes' if data['response_received'] else 'No'
        response_date = data.get('response_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S') if response_received == 'Yes' else '')

        csv_path = 'all excels/recruiter_messages_history.csv'
        if not os.path.exists(csv_path):
            return jsonify({"error": "Message history file not found"}), 404

        # Read and update CSV
        rows = []
        found = False
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['Message ID'] == message_id:
                    row['Response Received'] = response_received
                    row['Response Date'] = response_date
                    found = True
                rows.append(row)

        if not found:
            return jsonify({"error": f"Message ID {message_id} not found"}), 404

        # Write back
        with open(csv_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return jsonify({"message": "Response status updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

##<
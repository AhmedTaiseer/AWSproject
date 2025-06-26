from flask import Flask, render_template, request, redirect, flash, url_for
from dotenv import load_dotenv
import boto3
import os
from werkzeug.utils import secure_filename

# Load environment variables from the .env file
load_dotenv(dotenv_path=r'/home/ec2-user/app2/keys.env')

AWS_REGION = 'us-east-1'

# Configure Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Needed for flash messages

# S3 config
BUCKET_NAME = 'my-file-sharing-bucket-fcds2025'
s3 = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

@app.route('/')
def home():
    try:
        # List files in the S3 bucket
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        print("S3 response:", response)  # Debug: print S3 response

        # Extract filenames from the response if there are objects
        files = response.get('Contents', [])
        
        # If files are present, extract the filenames
        file_names = [file['Key'] for file in files] if files else []

        print("Files found:", file_names)  # Debug: print filenames

        return render_template('index.html', files=file_names)
    
    except Exception as e:
        flash(f'Error fetching files: {str(e)}')
        return render_template('index.html', files=[])

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect('/')
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect('/')

    filename = secure_filename(file.filename)
    
    try:
        # Upload to S3
        s3.upload_fileobj(file, BUCKET_NAME, filename)

        # Get file URL
        file_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600
        )

        # ⬇️ Get list of all files in the S3 bucket
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
        all_files = [obj['Key'] for obj in objects.get('Contents', [])]

        return render_template('success.html', filename=filename, file_url=file_url, files=all_files)

    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect('/')

@app.route('/download/<filename>')
def download(filename):
    try:
        # Generate a pre-signed URL to download the file
        file_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600  # 1 hour validity
        )
        return redirect(file_url)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}')
        return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
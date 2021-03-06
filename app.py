#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import zipfile
import flask
from flask import Flask, request, redirect, url_for, flash, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
import shutil   
from tf_detector import TFDetector

# File route setup
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = set(['zip'])

#initiate the app
app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        #check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        #extract requests from webpage
        file = request.files['file']
        conf = request.form['value']

        if file and allowed_file(file.filename):

            #renew the folder following last task
            shutil.rmtree(UPLOAD_FOLDER)
            os.mkdir(UPLOAD_FOLDER)
            shutil.rmtree(OUTPUT_FOLDER)
            os.mkdir(OUTPUT_FOLDER)

            #Extract and save the zip file
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
            zip_ref.extractall(UPLOAD_FOLDER)
            zip_ref.close()
            
            #OS Housekeeping
            os.remove(os.path.join(UPLOAD_FOLDER, filename))
            shutil.rmtree(os.path.join(UPLOAD_FOLDER, "__MACOSX"))

            #Update the Model here. This is where the inference happens
            tf_detector = TFDetector(model_path='md_v4.1.0.pb', output_path='output', render_conf_threshold=conf)
            result = tf_detector.run_detection(input_path='uploads')

            #Save and compress the fiel for download
            zf = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(OUTPUT_FOLDER):
                for file in files:
                    zf.write(os.path.join(root, file))
            zf.close()

            return send_file(filename, attachment_filename='Processed_'+filename, as_attachment=True)
            
            
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)

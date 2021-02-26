#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import zipfile
import flask
from flask import Flask, request, redirect, url_for, flash, render_template, send_from_directory, send_file
from werkzeug.utils import secure_filename
import shutil
import subprocess
import time    
import click

from utils import chunk_list, find_images, load_image, truncate_float
from tf_detector import TFDetector


UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = set(['zip'])

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
        
        file = request.files['file']
        conf = request.form['value']

        if file and allowed_file(file.filename):

            shutil.rmtree(UPLOAD_FOLDER)
            os.mkdir(UPLOAD_FOLDER)
            shutil.rmtree(OUTPUT_FOLDER)
            os.mkdir(OUTPUT_FOLDER)

            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
            zip_ref.extractall(UPLOAD_FOLDER)
            zip_ref.close()
            
            os.remove(os.path.join(UPLOAD_FOLDER, filename))
            shutil.rmtree(os.path.join(UPLOAD_FOLDER, "__MACOSX"))

            tf_detector = TFDetector(model_path='md_v4.1.0.pb', output_path='output', render_conf_threshold=conf)
            image_file_names = find_images('uploads', recursive=True)
            results = []
            count = 0
            with click.progressbar(length=len(image_file_names),
                                    label='Processing Images',
                                    show_pos=True, show_eta=True,
                                    show_percent=True, info_sep='|') as bar:
                for im_file in image_file_names:
                    result = tf_detector._TFDetector__process_image(im_file, True)
                    results.append(result)
                    bar.update(1)
                    count +=1
                    flash(count)
                    return redirect(url_for('upload_file'))

            tf_detector.save(results)


            zf = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(OUTPUT_FOLDER):
                for file in files:
                    zf.write(os.path.join(root, file))
            zf.close()

            return send_file(filename, attachment_filename='Processed_'+filename, as_attachment=True)
    
                     
    return render_template('index.html')


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'


    app.debug = True
    app.run()

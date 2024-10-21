from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
import os
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
import textwrap

app = Flask(__name__)

# Generate a random secret key using os.urandom(24)
app.secret_key = os.urandom(24)

# Fetch all messages (text and images) from the database
def get_messages():
    db_path = os.path.join('/app/db', 'messages.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, chat_id, message, file_path, timestamp FROM messages ORDER BY timestamp DESC')
    messages = c.fetchall()
    conn.close()
    return messages

# Fetch a single message by id
def get_message_by_id(message_id):
    db_path = os.path.join('/app/db', 'messages.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT id, chat_id, message, file_path, timestamp FROM messages WHERE id = ?', (message_id,))
    message = c.fetchone()
    conn.close()
    return message

# Update message by id
def update_message(message_id, new_message):
    db_path = os.path.join('/app/db', 'messages.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('UPDATE messages SET message = ? WHERE id = ?', (new_message, message_id))
    conn.commit()
    conn.close()

# Delete message by id
def delete_message(message_id):
    db_path = os.path.join('/app/db', 'messages.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE id = ?', (message_id,))
    conn.commit()
    conn.close()

# Generate PDF from messages
def generate_pdf(messages):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setFont("Helvetica", 12)

    left_margin = 50
    right_margin = 50
    available_width = width - left_margin - right_margin
    top_margin = 50
    bottom_margin = 50

    y_position = height - top_margin

    pdf.drawString(left_margin, y_position, "Chat History")
    y_position -= 30

    for message in messages:
        chat_id, msg_text, file_path, timestamp = message[1], message[2], message[3], message[4]

        if y_position < bottom_margin:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y_position = height - top_margin

        pdf.drawString(left_margin, y_position, f"Chat ID: {chat_id}, Timestamp: {timestamp}")
        y_position -= 15  # Adjust for the next line

        if msg_text:
            text_object = pdf.beginText(left_margin, y_position)
            text_object.setFont("Helvetica", 12)

            wrapped_text = textwrap.wrap(msg_text, width=95)  # Estimated 95 characters fitting in available width
            for line in wrapped_text:
                text_object.textLine(line)

            pdf.drawText(text_object)
            y_position -= (15 * len(wrapped_text) + 5)  # Adjust y_position accordingly

        if file_path and os.path.exists(file_path):
            image_width = 4 * inch  # Fixed width for the image
            image_height = 3 * inch  # Adjust height to maintain aspect ratio
            available_height = y_position - bottom_margin  # Height left on the page

            if image_height > available_height:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y_position = height - top_margin  # Reset y_position after page break

            pdf.drawImage(file_path, left_margin, y_position - image_height, width=image_width, height=image_height, preserveAspectRatio=True)
            y_position -= (image_height + 20)  # Move down for the next message

        if y_position < bottom_margin:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y_position = height - top_margin

    pdf.save()
    buffer.seek(0)
    return buffer

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == os.getenv('WEB_PASSWORD'):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return 'Invalid password', 403
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    messages = get_messages()
    return render_template('index.html', messages=messages)

@app.route('/edit/<int:message_id>', methods=['GET', 'POST'])
@login_required
def edit_message(message_id):
    message = get_message_by_id(message_id)
    if not message:
        return 'Message not found', 404

    if request.method == 'POST':
        new_message = request.form['message']
        update_message(message_id, new_message)
        flash('Message updated successfully!')
        return redirect(url_for('index'))

    return render_template('edit.html', message=message)

@app.route('/delete/<int:message_id>', methods=['POST'])
@login_required
def delete_message_route(message_id):
    message = get_message_by_id(message_id)
    if not message:
        return 'Message not found', 404
    delete_message(message_id)
    flash('Message deleted successfully!')
    return redirect(url_for('index'))

# Route to serve image files
@app.route('/image/<filename>')
@login_required
def serve_image(filename):
    image_path = os.path.join('/app/images', filename)
    return send_file(image_path, mimetype='image/jpeg')

# Route to download chat history as PDF
@app.route('/download')
@login_required
def download_pdf():
    messages = get_messages()
    pdf_buffer = generate_pdf(messages)
    return send_file(pdf_buffer, as_attachment=True, download_name="chat_history.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

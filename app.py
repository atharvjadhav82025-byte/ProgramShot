from flask import Flask, render_template, request, send_from_directory, send_file
import os
import base64
import sqlite3

app = Flask(__name__)

GENERATED_FOLDER = "generated"
DATABASE = "programshot.db"

os.makedirs(GENERATED_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()

    images = conn.execute(
        "SELECT * FROM images ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template("index.html", images=images)


@app.route("/save", methods=["POST"])
def save_image():
    try:
        data = request.json["image"]
        question = request.json["question"].strip()

        if not question:
            return {"error": "Question is required"}, 400

        if "," not in data:
            return {"error": "Invalid image data"}, 400

        data = data.split(",", 1)[1]

        conn = get_db()

        cursor = conn.execute(
            "INSERT INTO images (question, filename) VALUES (?, ?)",
            (question, "")
        )

        image_id = cursor.lastrowid
        filename = f"Question_{image_id:02d}.png"
        filepath = os.path.join(GENERATED_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))

        conn.execute(
            "UPDATE images SET filename = ? WHERE id = ?",
            (filename, image_id)
        )

        conn.commit()
        conn.close()

        return {
            "message": "Image saved",
            "filename": filename
        }

    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/generated/<filename>")
def generated(filename):
    return send_from_directory(GENERATED_FOLDER, filename)
@app.route("/pdf/<filename>")
def download_pdf(filename):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        image_path = os.path.join(GENERATED_FOLDER, filename)

        if not os.path.exists(image_path):
            return {"error": "Image not found"}, 404

        pdf_filename = os.path.splitext(filename)[0] + ".pdf"
        pdf_path = os.path.join(GENERATED_FOLDER, pdf_filename)

        img = ImageReader(image_path)
        img_width, img_height = img.getSize()

        pdf = canvas.Canvas(
            pdf_path,
            pagesize=(img_width, img_height)
        )

        pdf.drawImage(
            img,
            0,
            0,
            width=img_width,
            height=img_height
        )

        pdf.save()

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename
        )

    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/delete/<filename>", methods=["POST"])
def delete_image(filename):
    try:
        filepath = os.path.join(GENERATED_FOLDER, filename)

        if os.path.exists(filepath):
            os.remove(filepath)

        conn = get_db()

        conn.execute(
            "DELETE FROM images WHERE filename = ?",
            (filename,)
        )

        conn.commit()
        conn.close()

        return {"message": "Image deleted"}

    except Exception as e:
        return {"error": str(e)}, 500
if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=5000
    )

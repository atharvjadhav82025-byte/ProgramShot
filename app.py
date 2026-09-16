from flask import Flask, render_template, request, send_file
import os
import base64
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

BUCKET = "generated"


def supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


@app.route("/")
def home():
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/images"
        "?select=*&order=id.desc",
        headers=supabase_headers()
    )

    if response.ok:
        images = response.json()
    else:
        images = []

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

        image_data = base64.b64decode(
            data.split(",", 1)[1]
        )

        # Create database record first
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/images",
            headers={
                **supabase_headers(),
                "Prefer": "return=representation"
            },
            json={
                "question": question,
                "filename": "temporary"
            }
        )

        if not response.ok:
            return {
                "error": "Database error: " + response.text
            }, 500

        record = response.json()[0]

        image_id = record["id"]

        filename = f"Question_{image_id:02d}.png"

        # Upload image to Supabase Storage
        upload_response = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/"
            f"{BUCKET}/{filename}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "image/png",
                "x-upsert": "false"
            },
            data=image_data
        )

        if not upload_response.ok:
            return {
                "error": "Storage error: "
                + upload_response.text
            }, 500

        # Update database with real filename
        update_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/images?id=eq.{image_id}",
            headers=supabase_headers(),
            json={
                "filename": filename
            }
        )

        if not update_response.ok:
            return {
                "error": "Database update failed"
            }, 500

        return {
            "message": "Image saved",
            "filename": filename
        }

    except Exception as e:
        return {
            "error": str(e)
        }, 500


@app.route("/generated/<filename>")
def generated(filename):

    response = requests.get(
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{BUCKET}/{filename}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
    )

    if not response.ok:
        return {
            "error": "Image not found"
        }, 404

    return send_file(
        BytesIO(response.content),
        mimetype="image/png"
    )


@app.route("/pdf/<filename>")
def download_pdf(filename):

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        response = requests.get(
            f"{SUPABASE_URL}/storage/v1/object/"
            f"{BUCKET}/{filename}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
        )

        if not response.ok:
            return {
                "error": "Image not found"
            }, 404

        image = ImageReader(
            BytesIO(response.content)
        )

        width, height = image.getSize()

        pdf_buffer = BytesIO()

        pdf = canvas.Canvas(
            pdf_buffer,
            pagesize=(width, height)
        )

        pdf.drawImage(
            image,
            0,
            0,
            width=width,
            height=height
        )

        pdf.save()

        pdf_buffer.seek(0)

        pdf_filename = (
            os.path.splitext(filename)[0]
            + ".pdf"
        )

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        return {
            "error": str(e)
        }, 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )

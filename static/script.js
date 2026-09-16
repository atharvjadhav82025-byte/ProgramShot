function showImage(input, previewId) {
    const file = input.files[0];

    if (file) {
        const image = document.getElementById(previewId);
        image.src = URL.createObjectURL(file);
        image.style.display = "block";
    }
}


async function generateImage() {

    const question =
        document.getElementById("question").value.trim();

    const program =
        document.getElementById("programPreview");

    const output =
        document.getElementById("outputPreview");


    if (!question || !program.src || !output.src) {
        alert("Please enter the question and select both images.");
        return;
    }


    const pageWidth = 1240;
    const pageHeight = 1754;
    const margin = 60;
    const gap = 30;


    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    canvas.width = pageWidth;
    canvas.height = pageHeight;


    function drawPage() {
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, pageWidth, pageHeight);
    }


    function drawWrappedText(
        text,
        x,
        y,
        maxWidth,
        fontSize
    ) {

        ctx.font = `bold ${fontSize}px Arial`;
        ctx.textAlign = "left";
        ctx.fillStyle = "black";


        const words = text.split(" ");
        const lines = [];
        let line = "";


        for (const word of words) {

            const testLine =
                line ? line + " " + word : word;


            if (ctx.measureText(testLine).width > maxWidth) {

                if (line) {
                    lines.push(line);
                }

                line = word;

            } else {

                line = testLine;

            }
        }


        if (line) {
            lines.push(line);
        }


        const lineHeight = 58;


        lines.forEach((item, index) => {

            ctx.fillText(
                item,
                x,
                y + index * lineHeight
            );

        });


        return lines.length * lineHeight;
    }


    const questionHeight =
        drawWrappedText(
            question,
            margin,
            margin + 42,
            pageWidth - margin * 2,
            56
        );


    const availableWidth =
        pageWidth - margin * 2;


    const programRatio =
        availableWidth / program.naturalWidth;


    const programHeight =
        program.naturalHeight * programRatio;


    const outputRatio =
        availableWidth / output.naturalWidth;


    const outputHeight =
        output.naturalHeight * outputRatio;


    const totalHeight =
        margin +
        questionHeight +
        gap +
        programHeight +
        gap +
        outputHeight +
        margin;


    canvas.height =
        Math.max(pageHeight, totalHeight);


    drawPage();


    const qHeight =
        drawWrappedText(
            question,
            margin,
            margin + 42,
            pageWidth - margin * 2,
            56
        );


    let y =
        margin +
        qHeight +
        gap;


    ctx.drawImage(
        program,
        margin,
        y,
        availableWidth,
        programHeight
    );


    y +=
        programHeight +
        gap;


    ctx.drawImage(
        output,
        margin,
        y,
        availableWidth,
        outputHeight
    );


    const imageData =
        canvas.toDataURL("image/png");


    const response =
        await fetch("/save", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                image: imageData,
                question: question
            })
        });


    if (response.ok) {

    const result = await response.json();

    const preview = document.getElementById("resultPreview");
    const generatedImage = document.getElementById("generatedPreview");
    const download = document.getElementById("generatedDownload");

    generatedImage.src = imageData;
    download.href = imageData;
    download.download = result.filename;

    const pdfDownload = document.getElementById("pdfDownload");
    pdfDownload.href = "/pdf/" + result.filename;

    preview.style.display = "block";

    alert("Image saved successfully! ✅\n" + result.filename);

} else {

    const error = await response.json();

    alert(
        "Failed to save image ❌\n" +
        (error.error || "Unknown error")
    );
}
}


function resetForm() {
    location.reload();
}
async function deleteImage(filename) {

    if (!confirm("Delete this image?")) {
        return;
    }

    const response = await fetch(
        "/delete/" + filename,
        {
            method: "POST"
        }
    );

    if (response.ok) {
        alert("Image deleted successfully! ✅");
        location.reload();
    } else {
        alert("Failed to delete image ❌");
    }
}

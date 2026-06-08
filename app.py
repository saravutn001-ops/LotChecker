import base64
import io
import json
import os
import re
from calendar import monthrange
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STAMP_DIR = "stamped_images"
os.makedirs(STAMP_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>Lot Checker</title>
<style>
body { font-family: Arial, sans-serif; background:#f4f6f8; padding:20px; }
.box { max-width:900px; margin:auto; background:white; padding:20px; border-radius:16px; box-shadow:0 4px 12px #0002; }
h1 { text-align:center; }
label { font-weight:bold; margin-top:10px; display:block; }
input, select, button { width:100%; font-size:20px; padding:12px; margin-top:8px; box-sizing:border-box; }
button { background:#0066cc; color:white; border:0; border-radius:10px; font-weight:bold; }
video, img { width:100%; margin-top:15px; border-radius:12px; border:1px solid #ccc; }
.pass { background:#d7ffd7; color:green; font-size:42px; text-align:center; padding:20px; border-radius:12px; margin-top:15px; font-weight:bold; }
.ng { background:#ffd7d7; color:red; font-size:42px; text-align:center; padding:20px; border-radius:12px; margin-top:15px; font-weight:bold; }
.warn { background:#fff3cd; color:#8a5a00; padding:12px; border-radius:10px; margin-top:10px; }
.info { background:#e7f1ff; color:#004085; padding:12px; border-radius:10px; margin-top:10px; }
table { width:100%; margin-top:15px; border-collapse:collapse; }
th, td { border:1px solid #ccc; padding:8px; font-size:15px; }
th { background:#eee; }
hr { margin:20px 0; }
.small { color:#666; font-size:14px; }
.download { display:block; text-align:center; background:#222; color:white; padding:14px; border-radius:10px; margin-top:15px; text-decoration:none; font-size:20px; }
</style>
</head>
<body>

<div class="box">
<h1>ตรวจสอบล็อตวันที่ผลิต</h1>

<label>ประเภทไลน์</label>
<select id="mode" onchange="changeMode()">
    <option value="sachet">Sachet</option>
    <option value="linapack">Linapack</option>
</select>

<label>ประเภทผลิตภัณฑ์</label>
<select id="productType" onchange="changeProduct()">
    <option value="EPC">EPC</option>
    <option value="EPW">EPW</option>
</select>

<label>ประเภทงาน</label>
<select id="marketType" onchange="changeProduct()">
    <option value="TH">งานไทย</option>
    <option value="EXPORT">งานต่างประเทศ</option>
    <option value="LAOS">งานลาว</option>
</select>

<label>วันที่ผลิต (MFG)</label>
<input type="date" id="mfgDate" onchange="updateMFGFromDate()">

<label>MFG ที่ใช้ตรวจ</label>
<input id="mfg" value="" placeholder="ระบบสร้างจากวันที่ผลิต" readonly>

<div id="sachetBox">
    <label>Sachet Code</label>
    <input id="sachetLine" value="MS11" placeholder="เช่น MS11">

    <label>EXP</label>
    <input id="sachetExp" value="" placeholder="เช่น 080927">

    <p class="small">Sachet: MFG 080626 MS11 1 EXP 080927 ถึง MS11 6</p>
</div>

<div id="linapackBox" style="display:none;">
    <label>เครื่อง Linapack</label>
    <select id="lpMachine">
        <option value="LP1">LP1</option>
        <option value="LP2">LP2</option>
        <option value="LP3">LP3</option>
        <option value="LP4">LP4</option>
        <option value="LP5">LP5</option>
        <option value="LP6">LP6</option>
        <option value="LP7" selected>LP7</option>
        <option value="LP8">LP8</option>
        <option value="LP9">LP9</option>
    </select>

    <div id="mixCodeBox">
        <label>รหัสวันที่ผสม / Mix Code</label>
        <input id="mixCode" value="08F" placeholder="เช่น 08F">
        <p class="small">ใช้กับ EPW งานไทย เช่น MFG 080626 08F 09:40</p>
    </div>

    <label>EXP</label>
    <input id="linapackExp" value="" placeholder="เช่น 080927">

    <p id="linapackHint" class="small"></p>
</div>

<div id="autoExpInfo" class="info"></div>

<hr>
<h3>อัปโหลดรูป</h3>
<input type="file" id="fileInput" accept="image/*">

<hr>
<h3>หรือถ่ายจากกล้อง</h3>
<button onclick="startCamera()">เปิดกล้อง</button>
<video id="video" autoplay playsinline></video>
<button onclick="captureImage()">ถ่ายรูปจากกล้อง</button>

<canvas id="canvas" style="display:none;"></canvas>
<h3>รูปตัวอย่าง</h3>
<img id="preview" style="display:none;">

<button onclick="sendCheck()">ตรวจสอบล็อต</button>

<div id="result"></div>
<div id="detail"></div>
</div>

<script>
let imageData = "";

function setTodayDefault() {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    document.getElementById("mfgDate").value = `${yyyy}-${mm}-${dd}`;
    updateMFGFromDate();
}

function parseDDMMYY(s) {
    if (!/^\\d{6}$/.test(s)) return null;
    const d = parseInt(s.substring(0, 2));
    const m = parseInt(s.substring(2, 4));
    const y = 2000 + parseInt(s.substring(4, 6));
    return new Date(y, m - 1, d);
}

function formatDDMMYY(date) {
    const d = String(date.getDate()).padStart(2, "0");
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const y = String(date.getFullYear()).slice(-2);
    return d + m + y;
}

function addMonths(date, months) {
    const d = date.getDate();
    const newDate = new Date(date);
    newDate.setMonth(newDate.getMonth() + months);
    if (newDate.getDate() !== d) newDate.setDate(0);
    return newDate;
}

function updateMFGFromDate() {
    const dateValue = document.getElementById("mfgDate").value;
    if (!dateValue) return;
    const parts = dateValue.split("-");
    const mfg = parts[2] + parts[1] + parts[0].slice(-2);
    document.getElementById("mfg").value = mfg;
    autoExp();
}

function autoExp() {
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mfg = document.getElementById("mfg").value.trim();
    const info = document.getElementById("autoExpInfo");
    const sachetExp = document.getElementById("sachetExp");
    const linapackExp = document.getElementById("linapackExp");

    if (!/^\\d{6}$/.test(mfg)) {
        info.innerHTML = "เลือกวันที่ผลิตจากปฏิทิน";
        return;
    }

    const date = parseDDMMYY(mfg);
    if (!date) return;

    if (product === "EPC") {
        if (market === "TH") {
            const exp = formatDDMMYY(addMonths(date, 15));
            sachetExp.value = exp;
            linapackExp.value = exp;
            info.innerHTML = "EPC งานไทย: EXP = MFG + 1 ปี 3 เดือน → " + exp;
        } else if (market === "LAOS") {
            const exp = formatDDMMYY(addMonths(date, 24));
            sachetExp.value = exp;
            linapackExp.value = exp;
            info.innerHTML = "EPC งานลาว: EXP = MFG + 2 ปี → " + exp;
        } else {
            sachetExp.value = "";
            linapackExp.value = "";
            info.innerHTML = "EPC งานต่างประเทศ: ไม่มีวันหมดอายุ";
        }
    } else {
        if (market === "TH") {
            sachetExp.value = "";
            linapackExp.value = "";
            info.innerHTML = "EPW งานไทย: มีวันผสม / ไม่มี EXP";
        } else if (market === "LAOS") {
            const exp = formatDDMMYY(addMonths(date, 24));
            sachetExp.value = exp;
            linapackExp.value = exp;
            info.innerHTML = "EPW งานลาว: EXP = MFG + 2 ปี → " + exp;
        } else {
            sachetExp.value = "";
            linapackExp.value = "";
            info.innerHTML = "EPW งานต่างประเทศ: ไม่มีวันผสม และไม่มี EXP";
        }
    }
}

function changeMode() {
    const mode = document.getElementById("mode").value;
    document.getElementById("sachetBox").style.display = mode === "sachet" ? "block" : "none";
    document.getElementById("linapackBox").style.display = mode === "linapack" ? "block" : "none";
    changeProduct();
}

function changeProduct() {
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mode = document.getElementById("mode").value;

    const mixCodeBox = document.getElementById("mixCodeBox");
    const linapackExp = document.getElementById("linapackExp");
    const sachetExp = document.getElementById("sachetExp");
    const hint = document.getElementById("linapackHint");

    const noExp = ((product === "EPC" && market === "EXPORT") || (product === "EPW" && market === "TH") || (product === "EPW" && market === "EXPORT"));
    sachetExp.disabled = noExp;
    linapackExp.disabled = noExp;

    if (mode === "linapack") {
        if (product === "EPW" && market === "TH") {
            mixCodeBox.style.display = "block";
            hint.innerHTML = "EPW ไทย: ตรวจ MFG + Mix Code + เวลา เช่น MFG 080626 08F 09:40";
        } else if (product === "EPW" && market === "LAOS") {
            mixCodeBox.style.display = "none";
            hint.innerHTML = "EPW ลาว: ตรวจ MFG + เวลา + EXP เช่น MFG 080626 09:40 / EXP 080628";
        } else if (product === "EPW" && market === "EXPORT") {
            mixCodeBox.style.display = "none";
            hint.innerHTML = "EPW ต่างประเทศ: ตรวจ MFG + เวลา ไม่มีวันผสม และไม่มี EXP";
        } else {
            mixCodeBox.style.display = "none";
            if (market === "TH") hint.innerHTML = "EPC ไทย: ตรวจ MFG + LP1-9 + เวลา + EXP";
            else if (market === "LAOS") hint.innerHTML = "EPC ลาว: ตรวจ MFG + LP1-9 + เวลา + EXP 2 ปี";
            else hint.innerHTML = "EPC ต่างประเทศ: ตรวจ MFG + LP1-9 + เวลา ไม่มี EXP";
        }
    }

    document.getElementById("result").innerHTML = "";
    document.getElementById("detail").innerHTML = "";
    autoExp();
}

document.getElementById("fileInput").addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) {
        imageData = event.target.result;
        const preview = document.getElementById("preview");
        preview.src = imageData;
        preview.style.display = "block";
    };
    reader.readAsDataURL(file);
});

async function startCamera() {
    try {
        const video = document.getElementById("video");
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
        video.srcObject = stream;
    } catch (err) {
        document.getElementById("result").innerHTML = '<div class="ng">เปิดกล้องไม่ได้</div><p>' + err + '</p>';
    }
}

function captureImage() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const preview = document.getElementById("preview");

    if (!video.videoWidth) {
        document.getElementById("result").innerHTML = '<div class="ng">กรุณาเปิดกล้องก่อน</div>';
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    imageData = canvas.toDataURL("image/jpeg", 0.9);
    preview.src = imageData;
    preview.style.display = "block";
}

async function sendCheck() {
    const resultDiv = document.getElementById("result");
    const detailDiv = document.getElementById("detail");

    if (!imageData) {
        resultDiv.innerHTML = '<div class="ng">กรุณาอัปโหลดรูปหรือถ่ายรูปก่อน</div>';
        return;
    }

    const mode = document.getElementById("mode").value;
    const productType = document.getElementById("productType").value;
    const marketType = document.getElementById("marketType").value;

    let payload = { mode: mode, productType: productType, marketType: marketType, mfg: document.getElementById("mfg").value, image: imageData };

    if (mode === "sachet") {
        payload.line = document.getElementById("sachetLine").value;
        payload.exp = document.getElementById("sachetExp").value;
        payload.mixCode = "";
    } else {
        payload.line = document.getElementById("lpMachine").value;
        payload.exp = document.getElementById("linapackExp").value;
        payload.mixCode = document.getElementById("mixCode").value;
    }

    resultDiv.innerHTML = '<div class="warn">กำลังตรวจสอบ...</div>';
    detailDiv.innerHTML = "";

    try {
        const res = await fetch("/check", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
        const data = await res.json();

        if (data.error) {
            resultDiv.innerHTML = `<div class="ng">ERROR</div><p>${data.error}</p>`;
            return;
        }

        resultDiv.innerHTML = data.summary === "PASS" ? `<div class="pass">PASS ✅</div>` : `<div class="ng">NG ❌</div>`;

        let html = `<p><b>เวลา:</b> ${data.time}</p>`;
        html += `<p><b>ประเภทไลน์:</b> ${data.mode}</p>`;
        html += `<p><b>ประเภทผลิตภัณฑ์:</b> ${data.productType}</p>`;
        html += `<p><b>ประเภทงาน:</b> ${data.marketType}</p>`;
        html += `<p><b>Expected EXP:</b> ${data.expectedExp}</p>`;

        if (data.stampedImageUrl) {
            html += `<a class="download" href="${data.stampedImageUrl}" target="_blank">เปิด / ดาวน์โหลดรูปที่แสตมป์ผลแล้ว</a>`;
            html += `<img src="${data.stampedImageUrl}">`;
        }

        html += `<table><tr><th>รายการ</th><th>ผล</th><th>อ่านได้</th><th>ค่าที่ควรเป็น</th></tr>`;
        data.details.forEach(row => {
            html += `<tr><td>${row.item}</td><td>${row.status}</td><td>${row.actual}</td><td>${row.expected}</td></tr>`;
        });
        html += `</table>`;
        html += `<h3>AI อ่านได้ทั้งหมด</h3><pre>${JSON.stringify(data.lines, null, 2)}</pre>`;
        detailDiv.innerHTML = html;
    } catch (err) {
        resultDiv.innerHTML = `<div class="ng">ERROR</div><p>${err}</p>`;
    }
}

window.onload = function() { setTodayDefault(); changeProduct(); };
</script>
</body>
</html>
"""


def normalize(text):
    text = str(text).upper()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_json_text(text):
    return text.replace("```json", "").replace("```", "").strip()


def parse_ddmmyy(s):
    s = str(s).strip()
    if not re.fullmatch(r"\d{6}", s):
        return None
    return datetime(2000 + int(s[4:6]), int(s[2:4]), int(s[:2]))


def add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return datetime(year, month, day)


def format_ddmmyy(dt):
    return dt.strftime("%d%m%y")


def calculate_exp(product_type, market_type, mfg):
    dt = parse_ddmmyy(mfg)
    if not dt:
        return ""

    if product_type == "EPC":
        if market_type == "TH":
            return format_ddmmyy(add_months(dt, 15))
        if market_type == "LAOS":
            return format_ddmmyy(add_months(dt, 24))
        return ""

    if product_type == "EPW":
        if market_type == "LAOS":
            return format_ddmmyy(add_months(dt, 24))
        return ""

    return ""


def no_exp_required(product_type, market_type):
    if product_type == "EPC":
        return market_type == "EXPORT"
    if product_type == "EPW":
        return market_type in ["TH", "EXPORT"]
    return False


def get_font(size):
    candidates = [
        "fonts/NotoSansThai-Regular.ttf",
        "fonts/THSarabunNew.ttf",
        "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_text_with_shadow(draw, position, text, font, fill, shadow=(0, 0, 0)):
    x, y = position
    draw.text((x + 3, y + 3), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def stamp_image(image_base64, summary, product_type, market_type, mode, checked_time):
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    image_bytes = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    draw = ImageDraw.Draw(image)
    w, h = image.size

    title_font = get_font(max(30, int(w * 0.045)))
    body_font = get_font(max(20, int(w * 0.028)))

    if summary == "PASS":
        title = "LOT CHECK PASS"
        line2 = "LOT VERIFIED"
        color = (0, 180, 0)
    else:
        title = "LOT CHECK NG"
        line2 = "LOT VERIFICATION FAILED"
        color = (255, 0, 0)

    x = 30
    y = 500

    # ไม่มีกรอบ / ไม่มีพื้นหลัง ใช้เงาดำให้อ่านง่าย
    draw_text_with_shadow(draw, (x, y), title, title_font, color)
    y += int(title_font.size * 1.25)
    draw_text_with_shadow(draw, (x, y), line2, body_font, color)
    y += int(body_font.size * 1.25)
    draw_text_with_shadow(draw, (x, y), f"By Lot Checker | {checked_time}", body_font, (255, 255, 255))
    y += int(body_font.size * 1.25)
    draw_text_with_shadow(draw, (x, y), f"{mode} | {product_type} | {market_type}", body_font, (255, 255, 255))

    filename = f"{summary}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    output_path = os.path.join(STAMP_DIR, filename)
    image.save(output_path, quality=95)
    return filename


def read_lot_with_ai(image_base64, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code):
    skip_exp = no_exp_required(product_type, market_type)

    if mode == "sachet":
        if skip_exp:
            prompt = f"""
Read ONLY printed lot code lines from the image.
This is Sachet format. EXP is NOT required.

Expected 6 rows:
MFG {expected_mfg} {expected_line} 1
MFG {expected_mfg} {expected_line} 2
MFG {expected_mfg} {expected_line} 3
MFG {expected_mfg} {expected_line} 4
MFG {expected_mfg} {expected_line} 5
MFG {expected_mfg} {expected_line} 6

Return JSON only:
{{"lines":["line 1 exactly as seen","line 2 exactly as seen","line 3 exactly as seen","line 4 exactly as seen","line 5 exactly as seen","line 6 exactly as seen"]}}
"""
        else:
            prompt = f"""
Read ONLY printed lot code lines from the image.
This is Sachet format.

Expected 6 rows:
MFG {expected_mfg} {expected_line} 1 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 2 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 3 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 4 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 5 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 6 EXP {expected_exp}

Return JSON only:
{{"lines":["line 1 exactly as seen","line 2 exactly as seen","line 3 exactly as seen","line 4 exactly as seen","line 5 exactly as seen","line 6 exactly as seen"]}}
"""
    else:
        if product_type == "EPW" and market_type == "TH":
            prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPW Thailand format. EXP is NOT required.

Expected:
MFG {expected_mfg} {mix_code} TT:TT

Example:
MFG {expected_mfg} {mix_code} 09:40

Return JSON only:
{{"lines":["MFG line exactly as seen"],"time":"HH:MM exactly as seen"}}
"""
        elif product_type == "EPW" and market_type == "LAOS":
            prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPW Laos format. No Mix Code.

Expected:
MFG {expected_mfg} TT:TT
EXP {expected_exp}

Example:
MFG {expected_mfg} 09:40
EXP {expected_exp}

Return JSON only:
{{"lines":["MFG line exactly as seen","EXP line exactly as seen"],"time":"HH:MM exactly as seen"}}
"""
        elif product_type == "EPW" and market_type == "EXPORT":
            prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPW Export format. No Mix Code and no EXP.

Expected:
MFG {expected_mfg} TT:TT

Example:
MFG {expected_mfg} 09:40

Return JSON only:
{{"lines":["MFG line exactly as seen"],"time":"HH:MM exactly as seen"}}
"""
        else:
            if skip_exp:
                prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPC Export format. EXP is NOT required.

Expected:
MFG {expected_mfg} {expected_line} TT:TT

Example:
MFG {expected_mfg} {expected_line} 09:40

Return JSON only:
{{"lines":["MFG line exactly as seen"],"time":"HH:MM exactly as seen"}}
"""
            else:
                prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPC format.

Expected:
MFG {expected_mfg} {expected_line} TT:TT
EXP {expected_exp}

Example:
MFG {expected_mfg} {expected_line} 09:40
EXP {expected_exp}

Return JSON only:
{{"lines":["MFG line exactly as seen","EXP line exactly as seen"],"time":"HH:MM exactly as seen"}}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_base64}"},
                ],
            }
        ],
    )
    return response.output_text


def check_sachet(lines, product_type, market_type, expected_mfg, expected_line, expected_exp):
    details = []
    overall = True
    skip_exp = no_exp_required(product_type, market_type)
    lines = [normalize(x) for x in lines]

    for i in range(1, 7):
        actual = lines[i - 1] if i <= len(lines) else ""
        if skip_exp:
            expected = f"MFG {expected_mfg} {expected_line} {i}"
            status = "PASS" if expected in actual else "NG"
        else:
            expected = f"MFG {expected_mfg} {expected_line} {i} EXP {expected_exp}"
            status = "PASS" if actual == expected else "NG"
        if status == "NG":
            overall = False
        details.append({"item": f"แถว {i}", "status": status, "actual": actual, "expected": expected if not skip_exp else expected + " / ไม่ตรวจ EXP"})
    return overall, details


def extract_time(text):
    match = re.search(r"\b([0-2][0-9]:[0-5][0-9])\b", text)
    return match.group(1) if match else ""


def check_linapack(lines, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code, ai_time=""):
    details = []
    overall = True
    skip_exp = no_exp_required(product_type, market_type)
    lines = [normalize(x) for x in lines]
    all_text = " ".join(lines)
    mfg_line = lines[0] if len(lines) > 0 else ""
    exp_line = lines[1] if len(lines) > 1 else ""

    if product_type == "EPW" and market_type == "TH":
        expected_mfg_part = f"MFG {expected_mfg} {mix_code}".upper()
    elif product_type == "EPW":
        expected_mfg_part = f"MFG {expected_mfg}".upper()
    else:
        expected_mfg_part = f"MFG {expected_mfg} {expected_line}".upper()

    expected_exp_part = f"EXP {expected_exp}".upper() if expected_exp else ""
    time_found = ai_time or extract_time(all_text)

    mfg_ok = expected_mfg_part in mfg_line
    time_ok = bool(time_found)
    exp_ok = True if skip_exp else (expected_exp_part in exp_line or expected_exp_part in all_text)

    if not mfg_ok:
        overall = False
    details.append({"item": "MFG / Line / Mix", "status": "PASS" if mfg_ok else "NG", "actual": mfg_line, "expected": expected_mfg_part + " TT:TT"})

    if not time_ok:
        overall = False
    details.append({"item": "เวลา TT:TT", "status": "PASS" if time_ok else "NG", "actual": time_found, "expected": "รูปแบบ HH:MM เช่น 09:40"})

    if skip_exp:
        details.append({"item": "EXP", "status": "PASS", "actual": "ไม่ต้องมี EXP", "expected": "ไม่ตรวจวันหมดอายุ"})
    else:
        if not exp_ok:
            overall = False
        details.append({"item": "EXP", "status": "PASS" if exp_ok else "NG", "actual": exp_line, "expected": expected_exp_part})
    return overall, details


@app.route("/")
def index():
    return HTML


@app.route("/stamped/<filename>")
def stamped_file(filename):
    return send_from_directory(STAMP_DIR, filename)


@app.route("/check", methods=["POST"])
def check():
    try:
        data = request.json
        mode = data.get("mode", "sachet").strip().lower()
        product_type = data.get("productType", "EPC").strip().upper()
        market_type = data.get("marketType", "TH").strip().upper()
        expected_mfg = data.get("mfg", "").strip()
        expected_line = data.get("line", "").strip().upper()
        expected_exp = data.get("exp", "").strip()
        mix_code = data.get("mixCode", "").strip().upper()
        image_data = data.get("image", "")

        if not expected_mfg:
            return jsonify({"error": "กรุณาเลือกวันที่ผลิต"}), 400
        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY"}), 500

        auto_exp = calculate_exp(product_type, market_type, expected_mfg)
        if auto_exp:
            expected_exp = auto_exp
        skip_exp = no_exp_required(product_type, market_type)
        if not skip_exp and not expected_exp:
            return jsonify({"error": "กรุณากรอก EXP หรือเลือกประเภทงานที่ไม่ต้องมี EXP"}), 400

        image_base64 = image_data.split(",", 1)[1] if "," in image_data else image_data
        raw_ai = read_lot_with_ai(image_base64, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code)
        result_json = json.loads(clean_json_text(raw_ai))
        lines = result_json.get("lines", [])

        if mode == "sachet":
            overall, details = check_sachet(lines, product_type, market_type, expected_mfg, expected_line, expected_exp)
            mode_name = "Sachet"
        else:
            ai_time = result_json.get("time", "")
            overall, details = check_linapack(lines, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code, ai_time)
            mode_name = "Linapack"

        summary = "PASS" if overall else "NG"
        checked_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stamped_filename = stamp_image(image_data, summary, product_type, market_type, mode_name, checked_time)

        return jsonify({
            "summary": summary,
            "mode": mode_name,
            "productType": product_type,
            "marketType": market_type,
            "expectedExp": expected_exp if expected_exp else "ไม่ใช้ EXP",
            "lines": lines,
            "details": details,
            "time": checked_time,
            "stampedImageUrl": f"/stamped/{stamped_filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

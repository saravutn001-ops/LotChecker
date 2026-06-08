import json
import os
import re
from datetime import datetime
from calendar import monthrange

from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")
HTML = """
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<title>Lot Checker</title>
<style>
body { font-family: Arial; background:#f4f6f8; padding:20px; }
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
    <option value="EPW_TH">EPW ไทย</option>
    <option value="EPW_EXPORT">EPW ต่างประเทศ</option>
</select>

<label>ประเภทงาน</label>
<select id="marketType" onchange="changeProduct()">
    <option value="TH">งานไทย</option>
    <option value="EXPORT">งานต่างประเทศ</option>
    <option value="LAOS">งานลาว</option>
</select>

<label>MFG</label>
<input id="mfg" value="080626" placeholder="เช่น 080626" oninput="autoExp()">

<div id="sachetBox">
    <label>Sachet Code</label>
    <input id="sachetLine" value="MS11" placeholder="เช่น MS11">

    <label>EXP</label>
    <input id="sachetExp" value="080927" placeholder="เช่น 080927">

    <p class="small">Sachet EPC/EPW Export: MFG 080626 MS11 1 EXP 080927 ถึง MS11 6</p>
    <p class="small">Sachet EPW ไทย / EPC Export: ไม่ตรวจ EXP</p>
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
        <p class="small">ใช้กับ EPW เช่น MFG 080626 08F 09:40</p>
    </div>

    <label>EXP</label>
    <input id="linapackExp" value="080927" placeholder="เช่น 080927">

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

    if (newDate.getDate() !== d) {
        newDate.setDate(0);
    }

    return newDate;
}

function autoExp() {
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mfg = document.getElementById("mfg").value.trim();

    const info = document.getElementById("autoExpInfo");
    const sachetExp = document.getElementById("sachetExp");
    const linapackExp = document.getElementById("linapackExp");

    if (!/^\\d{6}$/.test(mfg)) {
        info.innerHTML = "กรอก MFG 6 หลัก เช่น 080626";
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
            info.innerHTML = "EPC งานต่างประเทศ: ไม่มีวันหมดอายุ ระบบจะไม่ตรวจ EXP";
        }
    } else if (product === "EPW_TH") {
        sachetExp.value = "";
        linapackExp.value = "";
        info.innerHTML = "EPW ไทย: ไม่มีวันหมดอายุ ระบบจะไม่ตรวจ EXP";
    } else {
        info.innerHTML = "EPW ต่างประเทศ: ตอนนี้ให้กรอก EXP เองก่อน เพราะมีหลายรูปแบบ";
    }
}

function isNoExpRequired() {
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;

    return (
        product === "EPW_TH" ||
        (product === "EPC" && market === "EXPORT")
    );
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

    const marketBox = document.getElementById("marketType");
    const mixCodeBox = document.getElementById("mixCodeBox");
    const linapackExp = document.getElementById("linapackExp");
    const sachetExp = document.getElementById("sachetExp");
    const hint = document.getElementById("linapackHint");

    marketBox.disabled = false;

    const noExp = (
        product === "EPW_TH" ||
        (product === "EPC" && market === "EXPORT")
    );

    sachetExp.disabled = noExp;
    linapackExp.disabled = noExp;

    if (mode === "linapack") {
        if (product === "EPW_TH") {
            mixCodeBox.style.display = "block";
            hint.innerHTML = "EPW ไทย: ตรวจรูปแบบ MFG 080626 08F TT:TT และไม่ตรวจ EXP";
        } else if (product === "EPW_EXPORT") {
            mixCodeBox.style.display = "block";
            hint.innerHTML = "EPW ต่างประเทศ: ตรวจ MFG + Mix Code + เวลา + EXP";
        } else {
            mixCodeBox.style.display = "none";
            if (market === "TH") {
                hint.innerHTML = "EPC งานไทย: ตรวจ MFG + LP1-9 + เวลา + EXP";
            } else if (market === "LAOS") {
                hint.innerHTML = "EPC งานลาว: ตรวจ MFG + LP1-9 + เวลา + EXP 2 ปี";
            } else {
                hint.innerHTML = "EPC งานต่างประเทศ: ตรวจ MFG + LP1-9 + เวลา และไม่ตรวจ EXP";
            }
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

        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
            audio: false
        });

        video.srcObject = stream;
    } catch (err) {
        document.getElementById("result").innerHTML =
            '<div class="ng">เปิดกล้องไม่ได้</div><p>' + err + '</p>';
    }
}

function captureImage() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const preview = document.getElementById("preview");

    if (!video.videoWidth) {
        document.getElementById("result").innerHTML =
            '<div class="ng">กรุณาเปิดกล้องก่อน</div>';
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

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

    let payload = {
        mode: mode,
        productType: productType,
        marketType: marketType,
        mfg: document.getElementById("mfg").value,
        image: imageData
    };

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
        const res = await fetch("/check", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.error) {
            resultDiv.innerHTML = `<div class="ng">ERROR</div><p>${data.error}</p>`;
            return;
        }

        resultDiv.innerHTML = data.summary === "PASS"
            ? `<div class="pass">PASS ✅</div>`
            : `<div class="ng">NG ❌</div>`;

        let html = `<p><b>เวลา:</b> ${data.time}</p>`;
        html += `<p><b>ประเภทไลน์:</b> ${data.mode}</p>`;
        html += `<p><b>ประเภทผลิตภัณฑ์:</b> ${data.productType}</p>`;
        html += `<p><b>ประเภทงาน:</b> ${data.marketType}</p>`;
        html += `<p><b>Expected EXP:</b> ${data.expectedExp}</p>`;

        html += `<table>
            <tr>
                <th>รายการ</th>
                <th>ผล</th>
                <th>อ่านได้</th>
                <th>ค่าที่ควรเป็น</th>
            </tr>`;

        data.details.forEach(row => {
            html += `<tr>
                <td>${row.item}</td>
                <td>${row.status}</td>
                <td>${row.actual}</td>
                <td>${row.expected}</td>
            </tr>`;
        });

        html += `</table>`;
        html += `<h3>AI อ่านได้ทั้งหมด</h3><pre>${JSON.stringify(data.lines, null, 2)}</pre>`;

        detailDiv.innerHTML = html;

    } catch (err) {
        resultDiv.innerHTML = `<div class="ng">ERROR</div><p>${err}</p>`;
    }
}

window.onload = function() {
    changeProduct();
};
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
    day = int(s[:2])
    month = int(s[2:4])
    year = 2000 + int(s[4:6])
    return datetime(year, month, day)


def add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return datetime(year, month, day)


def format_ddmmyy(dt):
    return dt.strftime("%d%m%y")


def calculate_exp(product_type, market_type, mfg):
    if product_type == "EPC":
        dt = parse_ddmmyy(mfg)
        if not dt:
            return ""

        if market_type == "TH":
            return format_ddmmyy(add_months(dt, 15))

        if market_type == "LAOS":
            return format_ddmmyy(add_months(dt, 24))

        if market_type == "EXPORT":
            return ""

    if product_type == "EPW_TH":
        return ""

    return ""


def no_exp_required(product_type, market_type):
    return (
        product_type == "EPW_TH" or
        (product_type == "EPC" and market_type == "EXPORT")
    )


def read_lot_with_ai(image_base64, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code):
    skip_exp = no_exp_required(product_type, market_type)

    if mode == "sachet":
        if skip_exp:
            prompt = f"""
You are a factory OCR checker.

Read ONLY printed lot code lines from the image.
Ignore handwriting, notebook lines, pen marks, shadows, and background.

This is Sachet format. EXP is NOT required for this product/market.

Expected target pattern has 6 rows:
MFG {expected_mfg} {expected_line} 1
MFG {expected_mfg} {expected_line} 2
MFG {expected_mfg} {expected_line} 3
MFG {expected_mfg} {expected_line} 4
MFG {expected_mfg} {expected_line} 5
MFG {expected_mfg} {expected_line} 6

Return JSON only:
{{"lines":["line 1 exactly as seen","line 2 exactly as seen","line 3 exactly as seen","line 4 exactly as seen","line 5 exactly as seen","line 6 exactly as seen"]}}

Rules:
- Do not silently correct mistakes.
- Keep the number after {expected_line} exactly as seen.
- If EXP appears in the image, include it exactly as seen in the line.
- If one row is missing or unreadable, put an empty string for that row.
"""
        else:
            prompt = f"""
You are a factory OCR checker.

Read ONLY printed lot code lines from the image.
Ignore handwriting, notebook lines, pen marks, shadows, and background.

This is Sachet format. The target lot code must have 6 rows.

Expected pattern:
MFG {expected_mfg} {expected_line} 1 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 2 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 3 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 4 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 5 EXP {expected_exp}
MFG {expected_mfg} {expected_line} 6 EXP {expected_exp}

Return JSON only:
{{"lines":["line 1 exactly as seen","line 2 exactly as seen","line 3 exactly as seen","line 4 exactly as seen","line 5 exactly as seen","line 6 exactly as seen"]}}

Rules:
- Do not silently correct mistakes.
- If you see EXP 0800927, return EXP 0800927.
- Keep the number after {expected_line} exactly as seen.
- If one row is missing or unreadable, put an empty string for that row.
"""
    else:
        if product_type.startswith("EPW"):
            if skip_exp:
                prompt = f"""
You are a factory OCR checker.

Read ONLY printed lot code from the image.
Ignore handwriting, notebook lines, pen marks, shadows, and background.

This is Linapack format. EXP is NOT required.

Expected format:
MFG {expected_mfg} {mix_code} TT:TT

Example:
MFG {expected_mfg} {mix_code} 09:40

Return JSON only:
{{
  "lines": [
    "MFG line exactly as seen"
  ],
  "time": "HH:MM exactly as seen"
}}

Rules:
- Do not silently correct mistakes.
- TT:TT is a time such as 09:40.
- If time is unreadable, return empty string for time.
"""
            else:
                prompt = f"""
You are a factory OCR checker.

Read ONLY printed lot code from the image.
Ignore handwriting, notebook lines, pen marks, shadows, and background.

This is Linapack format, EPW export product.
Expected format for now:
MFG {expected_mfg} {mix_code} TT:TT
EXP {expected_exp}

Example:
MFG {expected_mfg} {mix_code} 09:40
EXP {expected_exp}

Return JSON only:
{{
  "lines": [
    "MFG line exactly as seen",
    "EXP line exactly as seen"
  ],
  "time": "HH:MM exactly as seen"
}}

Rules:
- Do not silently correct mistakes.
- TT:TT is a time such as 09:40.
- If one line is missing or unreadable, put an empty string for that row.
"""
        else:
            if skip_exp:
                prompt = f"""
You are a factory OCR checker.

Read ONLY printed lot code from the image.
Ignore handwriting, notebook lines, pen marks, shadows, and background.

This is Linapack format, EPC export product. EXP is NOT required.

Expected format:
MFG {expected_mfg} {expected_line} TT:TT

Example:
MFG {expected_mfg} {expected_line} 09:40

Return JSON only:
{{
  "lines": [
    "MFG line exactly as seen"
  ],
  "time": "HH:MM exactly as seen"
}}

Rules:
- Do not silently correct mistakes.
- {expected_line} must be one of LP1, LP2, LP3, LP4, LP5, LP6, LP7, LP8, LP9.
- TT:TT is a time such as 09:40.
- If time is unreadable, return empty string for time.
"""
            else:
                prompt = f"""
You are a factory OCR checker.

Read ONLY printed lot code from the image.
Ignore handwriting, notebook lines, pen marks, shadows, and background.

This is Linapack format, EPC product.
Expected format:
MFG {expected_mfg} {expected_line} TT:TT
EXP {expected_exp}

Example:
MFG {expected_mfg} {expected_line} 09:40
EXP {expected_exp}

Return JSON only:
{{
  "lines": [
    "MFG line exactly as seen",
    "EXP line exactly as seen"
  ],
  "time": "HH:MM exactly as seen"
}}

Rules:
- Do not silently correct mistakes.
- {expected_line} must be one of LP1, LP2, LP3, LP4, LP5, LP6, LP7, LP8, LP9.
- TT:TT is a time such as 09:40.
- If time is unreadable, return empty string for time.
- If one line is missing or unreadable, put an empty string for that row.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                    },
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
        if skip_exp:
            expected = f"MFG {expected_mfg} {expected_line} {i}"
            actual = lines[i - 1] if i <= len(lines) else ""
            status = "PASS" if expected in actual else "NG"
        else:
            expected = f"MFG {expected_mfg} {expected_line} {i} EXP {expected_exp}"
            actual = lines[i - 1] if i <= len(lines) else ""
            status = "PASS" if actual == expected else "NG"

        if status == "NG":
            overall = False

        details.append({
            "item": f"แถว {i}",
            "status": status,
            "actual": actual,
            "expected": expected if not skip_exp else expected + " / ไม่ตรวจ EXP"
        })

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

    if product_type.startswith("EPW"):
        expected_mfg_part = f"MFG {expected_mfg} {mix_code}".upper()
    else:
        expected_mfg_part = f"MFG {expected_mfg} {expected_line}".upper()

    expected_exp_part = f"EXP {expected_exp}".upper() if expected_exp else ""

    time_found = ai_time or extract_time(all_text)

    mfg_ok = expected_mfg_part in mfg_line
    time_ok = bool(time_found)

    if skip_exp:
        exp_ok = True
    else:
        exp_ok = expected_exp_part in exp_line or expected_exp_part in all_text

    if not mfg_ok:
        overall = False
    details.append({
        "item": "MFG / Line / Mix",
        "status": "PASS" if mfg_ok else "NG",
        "actual": mfg_line,
        "expected": expected_mfg_part + " TT:TT"
    })

    if not time_ok:
        overall = False
    details.append({
        "item": "เวลา TT:TT",
        "status": "PASS" if time_ok else "NG",
        "actual": time_found,
        "expected": "รูปแบบ HH:MM เช่น 09:40"
    })

    if skip_exp:
        details.append({
            "item": "EXP",
            "status": "PASS",
            "actual": "ไม่ต้องมี EXP",
            "expected": "ผลิตภัณฑ์/ประเภทงานนี้ไม่ตรวจวันหมดอายุ"
        })
    else:
        if not exp_ok:
            overall = False
        details.append({
            "item": "EXP",
            "status": "PASS" if exp_ok else "NG",
            "actual": exp_line,
            "expected": expected_exp_part
        })

    return overall, details


@app.route("/")
def index():
    return HTML


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
            return jsonify({"error": "กรุณากรอก MFG"}), 400

        auto_exp = calculate_exp(product_type, market_type, expected_mfg)
        if auto_exp:
            expected_exp = auto_exp

        skip_exp = no_exp_required(product_type, market_type)

        if not skip_exp and not expected_exp:
            return jsonify({"error": "กรุณากรอก EXP หรือเลือกผลิตภัณฑ์/ประเภทงานที่ไม่ต้องมี EXP"}), 400

        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY ในไฟล์ .env"}), 500

        if "," in image_data:
            image_base64 = image_data.split(",", 1)[1]
        else:
            image_base64 = image_data

        raw_ai = read_lot_with_ai(
            image_base64,
            mode,
            product_type,
            market_type,
            expected_mfg,
            expected_line,
            expected_exp,
            mix_code
        )

        result_json = json.loads(clean_json_text(raw_ai))
        lines = result_json.get("lines", [])

        if mode == "sachet":
            overall, details = check_sachet(
                lines,
                product_type,
                market_type,
                expected_mfg,
                expected_line,
                expected_exp
            )
            mode_name = "Sachet"
        else:
            ai_time = result_json.get("time", "")
            overall, details = check_linapack(
                lines,
                product_type,
                market_type,
                expected_mfg,
                expected_line,
                expected_exp,
                mix_code,
                ai_time
            )
            mode_name = "Linapack"

        return jsonify({
            "summary": "PASS" if overall else "NG",
            "mode": mode_name,
            "productType": product_type,
            "marketType": market_type,
            "expectedExp": expected_exp if expected_exp else "ไม่ใช้ EXP",
            "lines": lines,
            "details": details,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

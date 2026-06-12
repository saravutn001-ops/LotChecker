import base64
import io
import json
import os
import re
from calendar import monthrange
from datetime import datetime, timedelta

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

:root {
    --primary:#0b63ce;
    --primary-dark:#084c9e;
    --bg:#eef3f8;
    --card:#ffffff;
    --text:#1f2937;
    --muted:#6b7280;
    --border:#d7dee8;
    --success:#16a34a;
    --danger:#dc2626;
}
* { box-sizing:border-box; }
body {
    font-family: Arial, sans-serif;
    background:
        radial-gradient(circle at top left, #d7eaff 0, transparent 32%),
        linear-gradient(180deg, #f7fbff 0%, var(--bg) 100%);
    margin:0;
    padding:14px;
    color:var(--text);
}
.box {
    max-width:960px;
    margin:auto;
    background:rgba(255,255,255,0.97);
    padding:18px;
    border-radius:24px;
    box-shadow:0 18px 50px rgba(15, 23, 42, 0.14);
    border:1px solid rgba(255,255,255,0.8);
}
h1 {
    text-align:center;
    margin:6px 0 4px;
    font-size:34px;
    letter-spacing:0.5px;
}
h1::after {
    content:"AI Lot Verification";
    display:block;
    font-size:14px;
    color:var(--muted);
    font-weight:normal;
    margin-top:4px;
}
h3 { font-size:22px; margin:10px 0 8px; }
label {
    font-weight:bold;
    margin-top:14px;
    display:block;
    color:#374151;
}
input, select {
    width:100%;
    font-size:20px;
    padding:13px 14px;
    margin-top:7px;
    border:1px solid var(--border);
    border-radius:14px;
    background:#fbfdff;
    color:var(--text);
    outline:none;
}
input:focus, select:focus {
    border-color:var(--primary);
    box-shadow:0 0 0 4px rgba(11,99,206,0.12);
}
input[readonly], input:disabled {
    background:#f3f6fa;
    color:#4b5563;
}
button {
    width:100%;
    font-size:20px;
    padding:14px;
    margin-top:8px;
    border:0;
    border-radius:14px;
    font-weight:bold;
    background:linear-gradient(135deg, var(--primary), var(--primary-dark));
    color:white;
    box-shadow:0 10px 22px rgba(11,99,206,0.25);
}
button:active { transform:translateY(1px); }
video, img {
    width:100%;
    margin-top:14px;
    border-radius:18px;
    border:1px solid var(--border);
    background:#0f172a;
}
.pass {
    background:linear-gradient(135deg, #dcfce7, #bbf7d0);
    color:#087f36;
    font-size:46px;
    text-align:center;
    padding:24px;
    border-radius:20px;
    margin-top:16px;
    font-weight:bold;
    border:1px solid #86efac;
}
.ng {
    background:linear-gradient(135deg, #fee2e2, #fecaca);
    color:#b91c1c;
    font-size:46px;
    text-align:center;
    padding:24px;
    border-radius:20px;
    margin-top:16px;
    font-weight:bold;
    border:1px solid #fca5a5;
}
.warn {
    background:#fff7ed;
    color:#9a3412;
    padding:14px;
    border-radius:14px;
    margin-top:12px;
    border:1px solid #fed7aa;
}
.info {
    background:#eff6ff;
    color:#1d4ed8;
    padding:14px;
    border-radius:14px;
    margin-top:14px;
    border:1px solid #bfdbfe;
}
table {
    width:100%;
    margin-top:16px;
    border-collapse:separate;
    border-spacing:0;
    overflow:hidden;
    border-radius:16px;
    border:1px solid var(--border);
    background:white;
}
th, td {
    border-bottom:1px solid var(--border);
    padding:10px;
    font-size:15px;
    vertical-align:top;
}
th { background:#f1f5f9; text-align:left; }
tr:last-child td { border-bottom:0; }
hr { margin:22px 0; border:0; border-top:1px solid var(--border); }
.small { color:var(--muted); font-size:14px; line-height:1.45; }
.download {
    display:block;
    text-align:center;
    background:#111827;
    color:white;
    padding:15px;
    border-radius:14px;
    margin-top:15px;
    text-decoration:none;
    font-size:20px;
    font-weight:bold;
}
.step-page { display:none; }
.step-page.active { display:block; animation:fadeIn .18s ease-in; }
@keyframes fadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
.step-tabs {
    display:grid;
    grid-template-columns:repeat(3, 1fr);
    gap:8px;
    margin:18px 0;
    padding:6px;
    background:#edf2f7;
    border-radius:18px;
}
.step-tabs button {
    font-size:15px;
    padding:12px 8px;
    background:transparent;
    color:#475569;
    border-radius:14px;
    box-shadow:none;
    margin:0;
}
.step-tabs button.active {
    background:white;
    color:var(--primary);
    box-shadow:0 8px 18px rgba(15,23,42,0.10);
}
.nav-row {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:18px;
}
.nav-row button { margin-top:0; }
.btn-secondary {
    background:#64748b !important;
    box-shadow:0 10px 22px rgba(100,116,139,0.20) !important;
}
.btn-success {
    background:linear-gradient(135deg, #16a34a, #15803d) !important;
    box-shadow:0 10px 22px rgba(22,163,74,0.25) !important;
}
#pouchSection, #cartonSection, #pouchHeader, #sachetBox, #linapackBox, #cartonTHBox, #cartonExportBox {
    background:#f8fafc;
    padding:14px;
    border-radius:18px;
    border:1px solid #e2e8f0;
    margin-top:12px;
}
#preview {
    max-height:520px;
    object-fit:contain;
    background:#111827;
}
pre {
    white-space:pre-wrap;
    background:#0f172a;
    color:#d1e7ff;
    padding:14px;
    border-radius:14px;
    overflow:auto;
}
@media (max-width:640px) {
    body { padding:8px; }
    .box { padding:14px; border-radius:18px; }
    h1 { font-size:28px; }
    input, select, button { font-size:18px; }
    .pass, .ng { font-size:38px; }
    .step-tabs button { font-size:13px; padding:10px 4px; }
    .nav-row { grid-template-columns:1fr; }
    th, td { font-size:13px; padding:8px; }
}


.status-pass { color:#087f36; font-weight:bold; }
.status-ng { color:#b91c1c; font-weight:bold; }
</style>
</head>
<body>

<div class="box">
<h1>Lot Checker</h1>

<div class="step-tabs">
    <button id="tab1" onclick="goPage(1)">1 ตั้งค่า</button>
    <button id="tab2" onclick="goPage(2)">2 รูปภาพ</button>
    <button id="tab3" onclick="goPage(3)">3 ผลตรวจ</button>
</div>

<div id="page1" class="step-page active">

<label>ประเภทการตรวจ</label>
<select id="checkType" onchange="changeCheckType()">
    <option value="pouch">ตรวจล็อตซอง</option>
    <option value="carton">ตรวจล็อตกล่อง</option>
</select>

<div id="pouchHeader">
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
</div>

<label>ประเภทงาน</label>
<select id="marketType" onchange="changeProduct()">
    <option value="TH">งานไทย</option>
    <option value="EXPORT">งานต่างประเทศ</option>
    <option id="marketLaosOption" value="LAOS">งานต่างประเทศ ลาว</option>
</select>

<label>วันที่ผลิต (MFG)</label>
<input type="date" id="mfgDate" onchange="updateMFGFromDate()">

<label>MFG ที่ใช้ตรวจ</label>
<input id="mfg" value="" readonly>

<div id="pouchSection">
    <div id="sachetBox">
        <label>Sachet Code</label>
        <input id="sachetLine" value="MS11" placeholder="เช่น MS11">

        <label>EXP</label>
        <input id="sachetExp" value="" placeholder="Auto Calculated" readonly>

        <p class="small">Sachet: MFG 080626 MS11 1 EXP 080927 ถึง MS11 6</p>
    </div>

    <div id="linapackBox" style="display:none;">
        <label>เครื่อง Linapack</label>
        <select id="lpMachine">
            <option value="LP1">LP1</option><option value="LP2">LP2</option><option value="LP3">LP3</option>
            <option value="LP4">LP4</option><option value="LP5">LP5</option><option value="LP6">LP6</option>
            <option value="LP7" selected>LP7</option><option value="LP8">LP8</option><option value="LP9">LP9</option>
        </select>

        <div id="mixCodeBox">
            <label>รหัสวันที่ผสม / Mix Code</label>
            <input id="mixCode" value="08F" placeholder="เช่น 08F">
            <p class="small">ใช้กับ EPW งานไทย เช่น MFG 080626 08F 09:40</p>
        </div>

        <label>EXP</label>
        <input id="linapackExp" value="" placeholder="Auto Calculated" readonly>

        <p id="linapackHint" class="small"></p>
    </div>
</div>

<div id="cartonSection" style="display:none;">
    <div id="cartonTHBox">
        <p class="small">กล่องงานไทย: ระบบจะตรวจรูปแบบ <b>00001 00 080626 3</b></p>
        <p class="small">เลขลำดับกล่องต้องเป็นตัวเลข 5 หลัก / รหัสงานไทยต้องเป็น 00 / เลขอาคารเลือกได้ 1-6 หรือ ไม่มี</p>

        <label>เลขอาคาร</label>
        <select id="buildingNo">
            <option value="">ไม่มี</option><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option>
            <option value="4">4</option><option value="5">5</option><option value="6">6</option>
        </select>

        <label>Suffix หลังเลขอาคาร</label>
        <input id="buildingSuffixTH" value="" placeholder="เว้นว่างได้ เช่น N หรือ QR">
        <p class="small">ถ้าเลือกเลขอาคารและมีการเติมท้ายเลขอาคาร เช่น 3N หรือ 3QR ให้กรอก N หรือ QR</p>
    </div>

    <div id="cartonExportBox" style="display:none;">
        <label>Prefix</label>
        <select id="cartonPrefix" onchange="updateShippingMarkByPrefix()">
            <option value="KC">KC → ZZZZZ</option>
            <option value="VN">VN → IPO VN</option>
            <option value="VT">VT → VN-MT</option>
            <option value="KK">KK → AKK</option>
            <option value="CT">CT → SHIPPING MARK: CDT</option>
            <option value="TS">TS → TS</option>
            <option value="AC">AC → AKC</option>
            <option value="SM">SM → SOMCHAICHALUEN</option>
            <option value="AX">AX → AKX</option>
            <option value="MM">MM → IP ONE-MYANMAR</option>
            <option value="ML">ML → ML</option>
            <option value="KT">KT → KT</option>
            <option value="MW">MW → MWD</option>
            <option value="MK">MK → MK</option>
            <option value="MY">MY → MDY</option>
            <option value="TG">TG → TG</option>
            <option value="MN">MN → MNJM</option>
            <option value="MA">MA → MLA</option>
            <option value="LM">LM → MT/LM+VY</option>
            <option value="DK">DK → DKSH</option>
            <option value="NT">NT → NTPL</option>
            <option value="XR">XR → XR</option>
            <option value="BU">BU → BUL</option>
            <option value="UK">UK → U,K,T-7</option>
            <option value="DB">DB → DBL INDUSTRIES PLC</option>
            <option value="OL">OL → IMPORTER:ORGANIC LINE CO., LTD</option>
            <option value="MI">MI → ZZZZZ</option>
            <option value="WD">WD → WEDAR</option>
            <option value="CZ">CZ → ZZZZZ</option>
            <option value="ND">ND → NDF</option>
            <option value="CS">CS → CSMS</option>
            <option value="FN">FN → FENIX</option>
            <option value="CD">CD → CDM</option>
            <option value="DT">DT → DBT</option>
            <option value="YP">YP → YPG</option>
            <option value="LB">LB → ZZZZZ</option>
            <option value="LQ">LQ → ZZZZZ</option>
            <option value="CUSTOM">CUSTOM → กรอกเอง</option>
        </select>

        <label>Shipping Mark</label>
        <input id="shippingMark" value="" placeholder="ระบบเติมจาก Prefix อัตโนมัติ" readonly>

        <p class="small">ตัวอย่าง: Prefix AC → Shipping Mark AKC / Prefix KC → ไม่มี Shipping Mark</p>

        <label>เลขอาคาร</label>
        <select id="buildingNoExport">
            <option value="">ไม่มี</option><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option>
            <option value="4">4</option><option value="5">5</option><option value="6">6</option>
        </select>

        <label>Suffix หลังเลขอาคาร</label>
        <input id="buildingSuffixExport" value="" placeholder="เว้นว่างได้ เช่น N หรือ QR">
        <p class="small">เช่น N = เปลี่ยน Artwork Packaging / QR = งาน XR STK แบบใหม่</p>

        <label>EXP สำหรับ Pattern ที่มี EXP</label>
        <input id="cartonExp" value="" placeholder="Auto Calculated" readonly>

        <p class="small">กล่องต่างประเทศ: มีหลายรูปแบบตาม D48 เช่น Shipping Mark + Running No. + รหัสตัวอักษร + MFG + EXP/K</p>
    </div>
</div>

<div id="autoExpInfo" class="info"></div>

<div class="nav-row">
    <button onclick="goPage(2)">ถัดไป: รูปภาพ</button>
</div>
</div>

<div id="page2" class="step-page">
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

<div class="nav-row">
    <button class="btn-secondary" onclick="goPage(1)">ย้อนกลับ</button>
    <button class="btn-success" onclick="sendCheck()">ตรวจสอบล็อต</button>
</div>
</div>

<div id="page3" class="step-page">
<div class="nav-row">
    <button class="btn-secondary" onclick="goPage(1)">ตั้งค่า</button>
    <button class="btn-secondary" onclick="goPage(2)">รูปภาพ</button>
</div>
<div id="result"></div>
<div id="detail"></div>
</div>
</div>

<script>
let imageData = "";

function goPage(page) {
    for (let i = 1; i <= 3; i++) {
        const pageEl = document.getElementById("page" + i);
        const tabEl = document.getElementById("tab" + i);
        if (pageEl) pageEl.classList.toggle("active", i === page);
        if (tabEl) tabEl.classList.toggle("active", i === page);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
}

const PREFIX_SHIPPING_MAP = {
    "KC": "",
    "VN": "IPO VN",
    "VT": "VN-MT",
    "KK": "AKK",
    "CT": "CDT",
    "TS": "TS",
    "AC": "AKC",
    "SM": "SOMCHAICHALUEN",
    "AX": "AKX",
    "MM": "I.P. ONE-MYANMAR",
    "ML": "ML",
    "KT": "KT",
    "MW": "MWD",
    "MK": "MK",
    "MY": "MDY",
    "TG": "TG",
    "MN": "MNJM",
    "MA": "MLA",
    "LM": "MT/LM+VY",
    "DK": "DKSH",
    "NT": "NTPL",
    "XR": "XR",
    "BU": "BUL",
    "UK": "U,K,T-7",
    "DB": "DBL INDUSTRIES PLC",
    "OL": "IMPORTER:ORGANIC LINE CO., LTD",
    "OD": "IMPORTER:ORGANIC LINE CO., LTD",
    "MI": "ZZZZZ",
    "WD": "WEDAR",
    "CZ": "ZZZZZ",
    "ND": "NDF",
    "CS": "CSMS",
    "FN": "FENIX",
    "CD": "CDM",
    "DT": "DBT",
    "YP": "YPG",
    "LB": "ZZZZZ",
    "LQ": "ZZZZZ"
};

function updateShippingMarkByPrefix() {
    const prefix = document.getElementById("cartonPrefix").value;
    const shippingInput = document.getElementById("shippingMark");

    if (prefix === "CUSTOM") {
        shippingInput.readOnly = false;
        shippingInput.value = "";
        shippingInput.placeholder = "กรอก Shipping Mark เอง";
        return;
    }

    shippingInput.readOnly = true;
    shippingInput.value = PREFIX_SHIPPING_MAP[prefix] || "";
}


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
    const checkType = document.getElementById("checkType").value;
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mfg = document.getElementById("mfg").value.trim();
    const info = document.getElementById("autoExpInfo");
    const sachetExp = document.getElementById("sachetExp");
    const linapackExp = document.getElementById("linapackExp");
    const cartonExp = document.getElementById("cartonExp");

    if (!/^\\d{6}$/.test(mfg)) {
        info.innerHTML = "เลือกวันที่ผลิตจากปฏิทิน";
        return;
    }

    const date = parseDDMMYY(mfg);
    if (!date) return;

    if (checkType === "carton") {
        if (market === "TH") {
            cartonExp.value = "";
            info.innerHTML = "กล่องงานไทย: ตรวจ Running No. 5 หลัก + 00 + MFG + อาคาร 1-6";
        } else {
            info.innerHTML = "กล่องงานต่างประเทศ: ตรวจ Shipping Mark / Running No. / รหัสตัวอักษร / MFG / EXP ตาม Pattern";
        }
        return;
    }

    if (product === "EPC") {
        if (market === "TH") {
            const exp = formatDDMMYY(addMonths(date, 15));
            sachetExp.value = exp; linapackExp.value = exp;
            info.innerHTML = "EPC งานไทย: EXP = MFG + 1 ปี 3 เดือน → " + exp;
        } else if (market === "LAOS") {
            const exp = formatDDMMYY(addMonths(date, 24));
            sachetExp.value = exp; linapackExp.value = exp;
            info.innerHTML = "EPC งานต่างประเทศ ลาว: EXP = MFG + 2 ปี → " + exp;
        } else {
            sachetExp.value = ""; linapackExp.value = "";
            info.innerHTML = "EPC งานต่างประเทศ: ไม่มีวันหมดอายุ";
        }
    } else {
        if (market === "TH") {
            sachetExp.value = ""; linapackExp.value = "";
            info.innerHTML = "EPW งานไทย: มีวันผสม / ไม่มี EXP";
        } else if (market === "LAOS") {
            const exp = formatDDMMYY(addMonths(date, 36));
            sachetExp.value = exp; linapackExp.value = exp;
            info.innerHTML = "EPW งานต่างประเทศ ลาว: EXP = MFG + 3 ปี → " + exp;
        } else {
            sachetExp.value = ""; linapackExp.value = "";
            info.innerHTML = "EPW งานต่างประเทศ: ไม่มีวันผสม และไม่มี EXP";
        }
    }
}

function changeCheckType() {
    const checkType = document.getElementById("checkType").value;
    const marketType = document.getElementById("marketType");
    const laosOption = document.getElementById("marketLaosOption");

    document.getElementById("pouchHeader").style.display = checkType === "pouch" ? "block" : "none";
    document.getElementById("pouchSection").style.display = checkType === "pouch" ? "block" : "none";
    document.getElementById("cartonSection").style.display = checkType === "carton" ? "block" : "none";

    // Carton lot does not separate Laos. Laos is treated as normal Export for carton mode.
    if (checkType === "carton") {
        if (laosOption) laosOption.style.display = "none";
        if (marketType.value === "LAOS") marketType.value = "EXPORT";
    } else {
        if (laosOption) laosOption.style.display = "block";
    }

    changeProduct();
}

function changeMode() {
    const mode = document.getElementById("mode").value;
    document.getElementById("sachetBox").style.display = mode === "sachet" ? "block" : "none";
    document.getElementById("linapackBox").style.display = mode === "linapack" ? "block" : "none";
    changeProduct();
}

function changeProduct() {
    const checkType = document.getElementById("checkType").value;
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mode = document.getElementById("mode").value;

    const mixCodeBox = document.getElementById("mixCodeBox");
    const cartonTHBox = document.getElementById("cartonTHBox");
    const cartonExportBox = document.getElementById("cartonExportBox");
    const linapackExp = document.getElementById("linapackExp");
    const sachetExp = document.getElementById("sachetExp");
    const hint = document.getElementById("linapackHint");

    const noExp = (
        (product === "EPC" && market === "EXPORT") ||
        (product === "EPW" && market === "TH") ||
        (product === "EPW" && market === "EXPORT")
    );

    sachetExp.disabled = noExp;
    linapackExp.disabled = noExp;

    if (checkType === "carton") {
        cartonTHBox.style.display = market === "TH" ? "block" : "none";
        cartonExportBox.style.display = (market === "EXPORT" || market === "LAOS") ? "block" : "none";
        if (market === "EXPORT" || market === "LAOS") updateShippingMarkByPrefix();
    }

    if (checkType === "pouch" && mode === "linapack") {
        if (product === "EPW" && market === "TH") {
            mixCodeBox.style.display = "block";
            hint.innerHTML = "EPW ไทย: ตรวจ MFG + Mix Code + เวลา เช่น MFG 080626 08F 09:40";
        } else if (product === "EPW" && market === "LAOS") {
            mixCodeBox.style.display = "none";
            hint.innerHTML = "EPW งานต่างประเทศ ลาว: ตรวจ MFG + เวลา + EXP 3 ปี";
        } else if (product === "EPW" && market === "EXPORT") {
            mixCodeBox.style.display = "none";
            hint.innerHTML = "EPW ต่างประเทศ: ตรวจ MFG + เวลา ไม่มีวันผสม และไม่มี EXP";
        } else {
            mixCodeBox.style.display = "none";
            if (market === "TH") hint.innerHTML = "EPC ไทย: ตรวจ MFG + LP1-9 + เวลา + EXP";
            else if (market === "LAOS") hint.innerHTML = "EPC งานต่างประเทศ ลาว: ตรวจ MFG + LP1-9 + เวลา + EXP 2 ปี";
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

    const checkType = document.getElementById("checkType").value;
    const mode = document.getElementById("mode").value;
    const productType = document.getElementById("productType").value;
    const marketType = document.getElementById("marketType").value;

    let payload = {
        checkType: checkType,
        mode: mode,
        productType: productType,
        marketType: marketType,
        mfg: document.getElementById("mfg").value,
        image: imageData
    };

    if (checkType === "pouch") {
        if (mode === "sachet") {
            payload.line = document.getElementById("sachetLine").value;
            payload.exp = document.getElementById("sachetExp").value;
            payload.mixCode = "";
        } else {
            payload.line = document.getElementById("lpMachine").value;
            payload.exp = document.getElementById("linapackExp").value;
            payload.mixCode = document.getElementById("mixCode").value;
        }
    } else {
        payload.line = "";
        payload.exp = marketType === "TH" ? "" : document.getElementById("cartonExp").value;
        payload.mixCode = "";
        payload.buildingNo = marketType === "TH" ? document.getElementById("buildingNo").value : document.getElementById("buildingNoExport").value;
        payload.buildingSuffix = marketType === "TH" ? document.getElementById("buildingSuffixTH").value : document.getElementById("buildingSuffixExport").value;
        payload.shippingMark = (marketType === "EXPORT" || marketType === "LAOS") ? document.getElementById("shippingMark").value : "";
        payload.cartonAlphaCode = (marketType === "EXPORT" || marketType === "LAOS") ? document.getElementById("cartonPrefix").value : "";
    }

    goPage(3);
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
        html += `<p><b>ประเภทการตรวจ:</b> ${data.checkType}</p>`;
        html += `<p><b>ประเภทงาน:</b> ${data.marketType}</p>`;
        html += `<p><b>Expected EXP:</b> ${data.expectedExp}</p>`;
if (data.stampedImageUrl) {
            html += `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:15px;">
                <a class="download" href="${data.stampedImageUrl}" target="_blank">เปิดรูป</a>
                <a class="download" href="${data.stampedImageUrl}" download="Lot_Check_Result.jpg" style="background:#16a34a;">ดาวน์โหลดรูป</a>
            </div>
            `;
            html += `<img src="${data.stampedImageUrl}">`;
        }

        html += `<table><tr><th>รายการ</th><th>ผล</th><th>อ่านได้</th><th>ค่าที่ควรเป็น</th></tr>`;

        data.details.forEach(row => {
            const cls = row.status === "PASS" ? "status-pass" : (row.status === "NG" ? "status-ng" : "");
            html += `<tr><td>${row.item}</td><td class="${cls}">${row.status}</td><td>${row.actual}</td><td>${row.expected}</td></tr>`;
        });

        html += `</table>`;

        if (data.abnormalPoints && data.abnormalPoints.length > 0) {
            html += `<h3>จุดผิดปกติที่พบ</h3>`;
            html += `<table><tr><th>จุดที่ผิด</th><th>ปัญหา</th><th>อ่านได้</th><th>ควรเป็น</th><th>ตำแหน่งในรูป/ล็อต</th></tr>`;
            data.abnormalPoints.forEach(p => {
                html += `<tr>
                    <td>${p.item || ""}</td>
                    <td>${p.problem || ""}</td>
                    <td>${p.actual || ""}</td>
                    <td>${p.expected || ""}</td>
                    <td>${p.position_hint || ""}</td>
                </tr>`;
            });
            html += `</table>`;
        }

        html += `<h3>AI อ่านได้ทั้งหมด</h3><pre>${JSON.stringify(data.lines, null, 2)}</pre>`;
        detailDiv.innerHTML = html;

    } catch (err) {
        resultDiv.innerHTML = `<div class="ng">ERROR</div><p>${err}</p>`;
    }
}

window.onload = function() { setTodayDefault(); updateShippingMarkByPrefix(); changeCheckType(); goPage(1); };
</script>
</body>
</html>
"""


def now_thai():
    return datetime.utcnow() + timedelta(hours=7)


def normalize(text):
    text = str(text).upper()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_json_text(text):
    text = text.replace("```json", "").replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        return text[start:end + 1]
    return text


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
            return format_ddmmyy(add_months(dt, 36))
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



def get_red_boxes_with_ai(image_base64, details, lines):
    """
    Ask GPT Vision to locate the printed lot area that caused NG.
    Returns boxes in normalized coordinates 0-1000.
    """
    try:
        ng_items = []
        for d in details:
            if str(d.get("status", "")).upper() == "NG":
                ng_items.append({
                    "item": d.get("item", ""),
                    "actual": d.get("actual", ""),
                    "expected": d.get("expected", "")
                })

        if not ng_items:
            return []

        prompt = f"""
You are locating defective printed LOT text on a product photo.

The verification result is NG.
NG details:
{json.dumps(ng_items, ensure_ascii=False)}

AI read these lot lines:
{json.dumps(lines, ensure_ascii=False)}

Task:
Return bounding boxes around the actual printed LOT / MFG / EXP / batch text area on the image that caused the NG.

Important:
- If MFG or EXP words are missing, draw the box around the printed date/lot lines where MFG/EXP should have appeared.
- Do NOT box logo, barcode, QR code, product name, marketing text, machine, floor, or background.
- For pouch images, the lot text is usually printed near the top edge of the pouch.
- For carton images, the lot text is usually dot-matrix printed on the carton surface.
- If multiple printed lot lines are involved, return one box around the whole lot text area.
- Coordinates must be normalized 0-1000 relative to the full original image.

Return JSON only:
{{
  "boxes": [
    {{"label":"LOT NG", "x1":0, "y1":0, "x2":1000, "y2":1000}}
  ]
}}
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

        result_text = clean_json_text(response.output_text)
        data = json.loads(result_text)
        boxes = data.get("boxes", [])
        if not isinstance(boxes, list):
            return []

        cleaned = []
        for b in boxes:
            if not isinstance(b, dict):
                continue
            try:
                x1 = float(b.get("x1", 0))
                y1 = float(b.get("y1", 0))
                x2 = float(b.get("x2", 0))
                y2 = float(b.get("y2", 0))
            except Exception:
                continue

            if x2 <= x1 or y2 <= y1:
                continue

            # clamp
            x1 = max(0, min(1000, x1))
            y1 = max(0, min(1000, y1))
            x2 = max(0, min(1000, x2))
            y2 = max(0, min(1000, y2))

            cleaned.append({
                "label": str(b.get("label", "LOT NG")),
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            })

        return cleaned

    except Exception:
        return []


def find_dark_lot_area_fallback(image):
    """
    Deterministic fallback for lot text box.
    Finds small black dot-matrix / inkjet lot text printed on a lighter local background.
    This avoids AI putting a box on tanks/background.
    """
    try:
        gray = image.convert("L")
        w, h = gray.size
        pix = gray.load()

        # Lot code usually appears on product/carton, not on the machine background.
        # Search the middle/product area first.
        x_start = int(w * 0.06)
        x_end = int(w * 0.94)
        y_start = int(h * 0.34)
        y_end = int(h * 0.72)

        points = []

        # Dark text on light/pink/brown carton background:
        # pixel is dark, but surrounding background is not dark.
        for y in range(y_start, y_end, 3):
            for x in range(x_start, x_end, 3):
                v = pix[x, y]
                if v > 95:
                    continue

                # local average around the point
                total = 0
                count = 0
                r = 9
                for yy in range(max(0, y-r), min(h, y+r+1), 6):
                    for xx in range(max(0, x-r), min(w, x+r+1), 6):
                        total += pix[xx, yy]
                        count += 1
                avg = total / max(count, 1)

                # reject dark logo/background; accept black print on lighter background
                if avg >= 105:
                    points.append((x, y))

        if not points:
            return []

        # Group by row bands. Lot text usually forms 1-3 compact horizontal rows.
        rows = {}
        band = max(8, int(h * 0.008))
        for x, y in points:
            key = int(y / band)
            rows.setdefault(key, []).append((x, y))

        candidates = []
        for key, pts in rows.items():
            if len(pts) < 8:
                continue

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)

            # Merge nearby row bands to include 2-line codes
            for k2 in [key + 1, key + 2, key - 1, key - 2]:
                if k2 in rows:
                    pts2 = rows[k2]
                    if len(pts2) >= 6:
                        xs2 = [p[0] for p in pts2]
                        # only merge if horizontally overlaps
                        if not (max(xs2) < x1 or min(xs2) > x2):
                            xs += xs2
                            ys += [p[1] for p in pts2]
                            x1, x2 = min(xs), max(xs)
                            y1, y2 = min(ys), max(ys)

            bw = x2 - x1
            bh = y2 - y1

            # Filter text-like compact area
            if bw < w * 0.08 or bw > w * 0.55:
                continue
            if bh < h * 0.006 or bh > h * 0.09:
                continue

            # Prefer upper area of product and compact wide text.
            # The actual lot is usually above product logo/marketing text.
            score = (y1 / h) * 1000 + (bh / h) * 100 + abs((bw / w) - 0.24) * 200
            candidates.append((score, x1, y1, x2, y2))

        if not candidates:
            return []

        candidates.sort(key=lambda t: t[0])
        _, x1, y1, x2, y2 = candidates[0]

        # Expand enough to cover both MFG/EXP lines and missing words area
        pad_x = int(w * 0.035)
        pad_y = int(h * 0.018)
        x1 = max(0, x1 - pad_x)
        x2 = min(w - 1, x2 + pad_x)
        y1 = max(0, y1 - pad_y)
        y2 = min(h - 1, y2 + pad_y)

        return [{
            "label": "LOT TEXT",
            "x1": x1 * 1000 / w,
            "y1": y1 * 1000 / h,
            "x2": x2 * 1000 / w,
            "y2": y2 * 1000 / h,
        }]
    except Exception:
        return []


def draw_red_boxes_on_image(image, boxes):
    """
    Draw red rectangles on image using normalized coordinates 0-1000.
    """
    if not boxes:
        return image

    draw = ImageDraw.Draw(image)
    w, h = image.size

    for b in boxes:
        try:
            x1 = int(float(b.get("x1", 0)) * w / 1000)
            y1 = int(float(b.get("y1", 0)) * h / 1000)
            x2 = int(float(b.get("x2", 0)) * w / 1000)
            y2 = int(float(b.get("y2", 0)) * h / 1000)

            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))

            if x2 <= x1 or y2 <= y1:
                continue

            pad = max(8, int(w * 0.008))
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(w - 1, x2 + pad)
            y2 = min(h - 1, y2 + pad)

            thickness = max(5, int(w * 0.006))
            for i in range(thickness):
                draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=(255, 0, 0))

            label = str(b.get("label", "LOT NG")).strip() or "LOT NG"
            font = get_font(max(22, int(w * 0.025)))
            text = f"{label}"
            try:
                tb = draw.textbbox((0, 0), text, font=font)
                tw = tb[2] - tb[0]
                th = tb[3] - tb[1]
                ly1 = max(0, y1 - th - 12)
                draw.rectangle([x1, ly1, min(w - 1, x1 + tw + 14), ly1 + th + 10], fill=(255, 0, 0))
                draw.text((x1 + 7, ly1 + 5), text, font=font, fill=(255, 255, 255))
            except Exception:
                pass

        except Exception:
            continue

    return image




def stamp_image(image_base64, summary, check_type, product_type, market_type, mode, checked_time):
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

    check_type_en = str(check_type)
    if check_type_en == "ซอง":
        check_type_en = "POUCH"
    elif check_type_en == "กล่อง":
        check_type_en = "CARTON"

    x = max(20, int(w * 0.035))

    # Put stamp at bottom-left, no background box
    line_count = 4
    line_height_title = int(title_font.size * 1.25)
    line_height_body = int(body_font.size * 1.25)
    total_text_height = line_height_title + (line_count - 1) * line_height_body
    y = max(20, h - total_text_height - max(30, int(h * 0.035)))

    draw_text_with_shadow(draw, (x, y), title, title_font, color)
    y += int(title_font.size * 1.25)
    draw_text_with_shadow(draw, (x, y), line2, body_font, color)
    y += int(body_font.size * 1.25)
    draw_text_with_shadow(draw, (x, y), f"By Lot Checker | {checked_time}", body_font, (255, 255, 255))
    y += int(body_font.size * 1.25)
    draw_text_with_shadow(draw, (x, y), f"{check_type_en} | {mode} | {product_type} | {market_type}", body_font, (255, 255, 255))


    filename = f"{summary}_{now_thai().strftime('%Y%m%d_%H%M%S')}.jpg"
    output_path = os.path.join(STAMP_DIR, filename)
    image.save(output_path, quality=95)

    return filename


def read_lot_with_ai(image_base64, check_type, mode, product_type, market_type, expected_mfg, expected_line, expected_exp,
                     mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code):
    skip_exp = no_exp_required(product_type, market_type)

    if check_type == "carton":
        if market_type == "TH":
            prompt = f"""
Read ONLY the printed carton lot/batch number from the image.

This is Thailand carton format.

Expected format:
NNNNN 00 {expected_mfg} {building_no} {building_suffix}

Rules:
- NNNNN must be any 5 digits. Do not compare it with an expected value.
- The second field must be exactly 00.
- MFG date must be exactly {expected_mfg}.
- Building number is optional. If building number is selected, it must be exactly {building_no} and must be 1-6.
- If building number is blank/none, the carton code must not be judged NG because of missing building number.
- Suffix after building number must be exactly "{building_suffix}" if provided.
- Do not infer suffix from expected value.
- If suffix is unclear, broken, incomplete, smeared, faint, partially missing, or not clearly readable, return UNCLEAR.
- Only return QR if both Q and R are clearly visible.
- If only R is visible, return R.
- If only Q is visible, return Q.
- If unsure between QR and R, return UNCLEAR, not QR. If building number is blank/none, ignore suffix.
- Do not infer suffix from expected value.
- If suffix is unclear, broken, incomplete, smeared, partially missing, or not clearly readable, return it as UNCLEAR.
- Only return QR if both Q and R are clearly visible. If only R is visible, return R. If unsure, return UNCLEAR.
- If unsure between QR and R, return UNCLEAR, not QR.
- Only return N if N is clearly visible. If unsure, return UNCLEAR.
- Examples: 3 N means building 3 with suffix N. 3 QR means building 3 with suffix QR. Suffix must be separated by a space.
- Do not silently correct mistakes.
- Beware Dot Matrix OCR: 0 may look like 8, but return exactly what you see.

Return JSON only:
{{"lines":["carton lot exactly as seen"]}}
"""
        else:
            shipping_rule = f"Shipping mark must be visible and match: {shipping_mark}" if shipping_mark else "Shipping mark may be blank or vary."
            alpha_rule = f"The Prefix before MFG date must match: {carton_alpha_code}" if carton_alpha_code else "Alphabet code after running number may vary by D48 pattern."
            prompt = f"""
Read ONLY the printed carton batch/lot code from the image.

This is Export carton format based on D48 table.

Common format parts:
- Shipping Mark must be before the 5-digit Running No. Example: XR 00001 XR 080626. If visible code is 00001 XR 080626, Shipping Mark is missing.
- Running number must be exactly 5 digits as printed.
- CRITICAL: Never add leading zeros yourself. If the printed code is 0001, return 0001 exactly, do NOT convert it to 00001.
- If the running number is not exactly 5 digits, the result must be NG.
- Prefix is the code before MFG date. Example: 00001 XR 080626, Prefix is XR.
- MFG date DDMMYY must be {expected_mfg}.
- Building/category number is optional. If selected, it must be {building_no} {building_suffix}. Suffix must be separated by a space. If building number is blank/none, ignore building and suffix. Suffix after building number must be exactly "{building_suffix}" if provided.
- EXP date may be {expected_exp if expected_exp else "not required"}.
- Do not check K. The last number is Building No. 1-6, not K.
- Special rule: Prefix OL uses Shipping Mark "IMPORTER:ORGANIC LINE CO., LTD" and it can be printed directly attached to the date without a space. Other prefixes normally have spacing.

{shipping_rule}
{alpha_rule}

Return JSON only:
{{
  "lines": ["carton batch/lot exactly as seen"],
  "has_shipping_mark": true,
  "has_alpha_code": true,
  "has_mfg": true,
  "has_exp": true,
  "has_k": true,
  "abnormal_points": [
    {{
      "item": "Running No. / Shipping Mark / Prefix / MFG Date / Building No. / Suffix / EXP / MFG Word / EXP Word",
      "actual": "what is visible",
      "expected": "what should be printed",
      "problem": "Missing / Wrong / Unclear / Incomplete / Extra",
      "position_hint": "before Running No. / before MFG date / after Building No. / first line / second line"
    }}
  ]
}}

Rules:
- Do not silently correct mistakes.
- If shipping mark is not required or not specified, set has_shipping_mark to true.
- If Prefix is specified but it is not printed before MFG date, set has_alpha_code to false.
- If no EXP is printed and EXP is not required, set has_exp to true.
"""
    elif mode == "sachet":
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

Return JSON only:
{{"lines":["MFG line exactly as seen"],"time":"HH:MM exactly as seen"}}

Important: If the image does not show the word MFG, do not add MFG yourself. Return exactly what is printed.
"""
        elif product_type == "EPW" and market_type == "LAOS":
            prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPW Laos Export format. No Mix Code. EXP is required.

Expected:
MFG {expected_mfg} TT:TT
EXP {expected_exp}

Return JSON only:
{{"lines":["MFG line exactly as seen","EXP line exactly as seen"],"time":"HH:MM exactly as seen"}}

Important: If the image does not show the words MFG or EXP, do not add them yourself. Return exactly what is printed.
"""
        elif product_type == "EPW" and market_type == "EXPORT":
            prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPW Export format. No Mix Code and no EXP.

Expected:
MFG {expected_mfg} TT:TT

Return JSON only:
{{"lines":["MFG line exactly as seen"],"time":"HH:MM exactly as seen"}}

Important: If the image does not show the word MFG, do not add MFG yourself. Return exactly what is printed.
"""
        else:
            if skip_exp:
                prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPC Export format. EXP is NOT required.

Expected:
MFG {expected_mfg} {expected_line} TT:TT

Return JSON only:
{{"lines":["MFG line exactly as seen"],"time":"HH:MM exactly as seen"}}

Important: If the image does not show the word MFG, do not add MFG yourself. Return exactly what is printed.
"""
            else:
                prompt = f"""
Read ONLY printed lot code from the image.
This is Linapack EPC Thailand format.

Expected:
MFG {expected_mfg} {expected_line} TT:TT
EXP {expected_exp}

Return JSON only:
{{"lines":["MFG line exactly as seen","EXP line exactly as seen"],"time":"HH:MM exactly as seen"}}

Important: If the image does not show the words MFG or EXP, do not add them yourself. Return exactly what is printed.
"""

    prompt += """

STRICT INSPECTION MODE:
- Read ONLY what is clearly visible in the image.
- Do NOT infer, guess, complete, correct, or normalize any character from the expected value.
- Do NOT use expected values to decide unclear characters.
- If any character is unclear, broken, smeared, faint, incomplete, partially missing, hidden, or visually ambiguous, return "UNCLEAR" for that character/field.
- If the whole field is unclear, return "UNCLEAR".
- For suffix QR:
  - Return "QR" ONLY when both Q and R are clearly visible.
  - If Q is unclear, return "UNCLEAR R" or "UNCLEAR".
  - If R is unclear, return "Q UNCLEAR" or "UNCLEAR".
  - If only R is visible, return "R".
  - If only Q is visible, return "Q".
  - Never return "QR" just because expected suffix is QR.
- For Running No.:
  - Read exact number of digits as printed.
  - Never add leading zero.
  - 0001 must remain 0001, not 00001.
- For MFG/EXP:
  - Never add missing words MFG or EXP.
  - If MFG or EXP text is not clearly visible, return exactly what is visible or UNCLEAR.
- If confidence is not high, choose UNCLEAR, not the expected value.

Additional visual inspection requirement:
- Identify abnormal point if visible.
- Do not guess or correct characters.
- If a character/word is unclear, broken, smeared, missing, or incomplete, mark it as UNCLEAR.
- Return abnormal_points only for visible abnormal items.
- position_hint must describe where it is on the lot code, such as "before Running No.", "before MFG date", "after Building No.", "MFG line", or "EXP line".
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


def build_abnormal_points(details):
    abnormal_points = []
    for d in (details or []):
        if str(d.get("status","")).upper() == "NG":
            abnormal_points.append({
                "item": d.get("item",""),
                "actual": d.get("actual",""),
                "expected": d.get("expected",""),
                "problem": "Wrong",
                "position_hint": d.get("item","")
            })
    return abnormal_points


def check_pouch_sachet(lines, product_type, market_type, expected_mfg, expected_line, expected_exp):
    details = []
    overall = True
    skip_exp = no_exp_required(product_type, market_type)
    lines = [normalize(x) for x in lines]

    for i in range(1, 7):
        actual = lines[i - 1] if i <= len(lines) else ""

        # Safety rule:
        # Pouch lot must contain the printed word MFG.
        # If this product/market requires EXP, it must also contain the printed word EXP.
        has_mfg_word = "MFG" in actual
        has_exp_word = "EXP" in actual

        if skip_exp:
            expected = f"MFG {expected_mfg} {expected_line} {i}"
            status = "PASS" if (expected in actual and has_mfg_word) else "NG"
            expected_show = expected + " / ต้องมีคำว่า MFG / ไม่ตรวจ EXP"
        else:
            expected = f"MFG {expected_mfg} {expected_line} {i} EXP {expected_exp}"
            status = "PASS" if (actual == expected and has_mfg_word and has_exp_word) else "NG"
            expected_show = expected + " / ต้องมีคำว่า MFG และ EXP"

        if status == "NG":
            overall = False

        details.append({
            "item": f"แถว {i}",
            "status": status,
            "actual": actual,
            "expected": expected_show
        })

    return overall, details

def extract_time(text):
    match = re.search(r"\b([0-2][0-9]:[0-5][0-9])\b", text)
    return match.group(1) if match else ""


def check_pouch_linapack(lines, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code, ai_time=""):
    details = []
    overall = True
    skip_exp = no_exp_required(product_type, market_type)

    lines = [normalize(x) for x in lines]
    all_text = " ".join(lines)

    mfg_line = lines[0] if len(lines) > 0 else ""
    exp_line = lines[1] if len(lines) > 1 else ""

    has_mfg_word = "MFG" in all_text
    has_exp_word = "EXP" in all_text

    if product_type == "EPW" and market_type == "TH":
        expected_mfg_part = f"MFG {expected_mfg} {mix_code}".upper()
    elif product_type == "EPW":
        expected_mfg_part = f"MFG {expected_mfg}".upper()
    else:
        expected_mfg_part = f"MFG {expected_mfg} {expected_line}".upper()

    expected_exp_part = f"EXP {expected_exp}".upper() if expected_exp else ""
    time_found = ai_time or extract_time(all_text)

    # Safety rule:
    # Pouch/Linapack must contain the printed word MFG.
    # If this product/market requires EXP, it must also contain the printed word EXP.
    mfg_ok = (expected_mfg_part in mfg_line) and has_mfg_word
    time_ok = bool(time_found)
    exp_ok = True if skip_exp else ((expected_exp_part in exp_line or expected_exp_part in all_text) and has_exp_word)

    if not mfg_ok:
        overall = False
    details.append({
        "item": "MFG / Line / Mix",
        "status": "PASS" if mfg_ok else "NG",
        "actual": mfg_line,
        "expected": expected_mfg_part + " TT:TT / ต้องมีคำว่า MFG"
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
            "expected": "ไม่ตรวจวันหมดอายุ"
        })
    else:
        if not exp_ok:
            overall = False
        details.append({
            "item": "EXP",
            "status": "PASS" if exp_ok else "NG",
            "actual": exp_line,
            "expected": expected_exp_part + " / ต้องมีคำว่า EXP"
        })

    # Extra explicit warning rows for missing printed words
    if not has_mfg_word:
        overall = False
        details.append({
            "item": "MFG word",
            "status": "NG",
            "actual": all_text,
            "expected": "ต้องมีคำว่า MFG บนซอง"
        })

    if not skip_exp and not has_exp_word:
        overall = False
        details.append({
            "item": "EXP word",
            "status": "NG",
            "actual": all_text,
            "expected": "ต้องมีคำว่า EXP บนซอง"
        })

    return overall, details

def parse_th_carton_fields(text):
    text = normalize(text)
    parts = text.split()
    if len(parts) < 4:
        return "", "", "", ""
    return parts[0], parts[1], parts[2], parts[3]



def clean_lot_token(token):
    """Keep only A-Z and 0-9 for carton parsing."""
    return re.sub(r"[^A-Z0-9]", "", str(token).upper())


def lot_tokens(text):
    text = normalize(text)
    tokens = [clean_lot_token(t) for t in text.split()]
    return [t for t in tokens if t]


def shipping_mark_before_running_ok(all_text, shipping_mark):
    """
    Shipping Mark = text before Running No.
    Example:
      XR 00001 XR 080626 3 QR  -> Shipping Mark XR PASS
      00001 XR 080626 3 QR     -> Shipping Mark XR NG
    Blank shipping mark = not required.
    """
    shipping_mark = str(shipping_mark or "").strip().upper()
    if not shipping_mark:
        return True

    tokens = lot_tokens(all_text)
    if not tokens:
        return False

    expected_compact = clean_lot_token(shipping_mark)
    text_norm = normalize(all_text).upper()

    # OL special: allow importer text before OL/date pattern
    if expected_compact in ["OL", "OD"] or "ORGANICLINE" in re.sub(r"[^A-Z0-9]", "", shipping_mark.upper()):
        return ("IMPORTER" in text_norm and "ORGANIC" in text_norm) or bool(re.search(r"\bOL\d{6}\b|\bOL\s*\d{6}\b", text_norm))

    for i, token in enumerate(tokens):
        if not re.fullmatch(r"\d{5}", token):
            continue

        # Simple shipping mark such as XR, AKC, TG, KC must be immediately before Running No.
        if i > 0 and tokens[i - 1] == expected_compact:
            return True

        # Compact case like XR00001 as one token may not be split here.
        if i == 0:
            continue

    # Multi-word shipping mark: compare compact text before first running no.
    compact_expected = re.sub(r"[^A-Z0-9]", "", shipping_mark.upper())
    if compact_expected:
        compact_all = re.sub(r"[^A-Z0-9]", "", text_norm)
        m = re.search(r"\d{5}", compact_all)
        if m:
            before_running = compact_all[:m.start()]
            return before_running.endswith(compact_expected)

    # Compact simple shipping mark + 5-digit running, e.g. XR00001
    compact_all2 = re.sub(r"[^A-Z0-9]", "", text_norm)
    if re.search(rf"{re.escape(expected_compact)}\d{{5}}", compact_all2):
        return True

    return False


def prefix_before_mfg_ok(all_text, expected_prefix, expected_mfg):
    """
    Prefix = code before MFG date.
    Example:
      00001 XR 080626 3 QR -> Prefix XR PASS
      00001 080626 3 QR    -> Prefix XR NG
    """
    expected_prefix = clean_lot_token(expected_prefix)
    expected_mfg = clean_lot_token(expected_mfg)

    if not expected_prefix:
        return True

    if expected_prefix == "OD":
        expected_prefix = "OL"

    tokens = lot_tokens(all_text)
    if not tokens:
        return False

    # OL special can be compact as OL250526
    if expected_prefix == "OL":
        compact = re.sub(r"[^A-Z0-9]", "", normalize(all_text).upper())
        return bool(re.search(rf"OL{re.escape(expected_mfg)}", compact)) or ("OL" in tokens)

    for i, token in enumerate(tokens):
        # XR 080626
        if token == expected_mfg and i > 0 and tokens[i - 1] == expected_prefix:
            return True

        # XR080626 compact
        if re.fullmatch(rf"{re.escape(expected_prefix)}{re.escape(expected_mfg)}", token):
            return True

    return False


def extract_export_running_no(all_text, carton_alpha_code=""):
    """
    Extract export carton running number exactly.
    Normal export cartons require exactly 5 digits.
    OL pattern has no separate Running No.
    """
    code = clean_lot_token(carton_alpha_code)
    if code in ["OL", "OD"]:
        return "", True

    tokens = lot_tokens(all_text)

    # Prefer the first numeric token with 4-5 digits because it is usually Running No.
    # Date is 6 digits, so it will not be confused here.
    for token in tokens:
        if re.fullmatch(r"\d{4,5}", token):
            return token, bool(re.fullmatch(r"\d{5}", token))

    # Compact case, e.g. XR00001XR080626
    compact = re.sub(r"[^A-Z0-9]", "", normalize(all_text).upper())
    m = re.search(r"(?<!\d)(\d{4,5})(?!\d)", compact)
    if m:
        run = m.group(1)
        return run, bool(re.fullmatch(r"\d{5}", run))

    return "", False


def running_no_present(all_text, carton_alpha_code=""):
    run, ok = extract_export_running_no(all_text, carton_alpha_code)
    return ok


def building_suffix_strict_ok(all_text, building_no, building_suffix):
    """
    Strict check for Building No. + Suffix.
    If suffix is selected, AI must read exact suffix clearly.
    Example: expected 3 QR -> only exact "3 QR" passes.
    "3 R", "3 Q", "3 UNCLEAR", "3 ?", smeared or unclear must be NG.
    """
    building_no = str(building_no or "").strip().upper()
    building_suffix = str(building_suffix or "").strip().upper()
    text = normalize(all_text)

    if not building_no:
        return True, "ไม่ตรวจเลขอาคาร"

    expected = f"{building_no} {building_suffix}".strip().upper()

    # Anything unclear must fail when we are checking building/suffix.
    if "UNCLEAR" in text or "?" in text or "UNKNOWN" in text:
        return False, expected if expected else building_no

    if building_suffix:
        # Need exact separated suffix, e.g. "3 QR"
        ok_exact = re.search(rf"\b{re.escape(building_no)}\s+{re.escape(building_suffix)}\b", text) is not None

        # Special safety for QR:
        # If expected QR but AI reads only Q or only R after building, must NG.
        if building_suffix == "QR":
            ok_exact = re.search(rf"\b{re.escape(building_no)}\s+QR\b", text) is not None
            only_q_or_r = re.search(rf"\b{re.escape(building_no)}\s+[QR]\b", text) is not None
            if only_q_or_r and not ok_exact:
                return False, expected

        return ok_exact, expected

    # ไม่มี suffix ตรวจแค่เลขอาคาร
    ok = re.search(rf"\b{re.escape(building_no)}\b", text) is not None
    return ok, building_no


def extract_carton_actual_fields(all_text, expected_mfg="", carton_alpha_code="", shipping_mark="", building_no="", building_suffix=""):
    """
    Return only the real field value for each carton check row.
    Example visible: XR 00001 IR 080626 3 Q
    shipping_mark -> XR
    running_no -> 00001
    prefix -> IR
    mfg -> 080626
    building_suffix -> 3 Q
    """
    text = normalize(all_text)
    tokens = lot_tokens(text)

    result = {
        "shipping_mark": "",
        "running_no": "",
        "prefix": "",
        "mfg": "",
        "building_suffix": "",
        "exp": "",
    }

    expected_mfg = clean_lot_token(expected_mfg)
    expected_prefix = clean_lot_token(carton_alpha_code)

    run_index = None
    for i, t in enumerate(tokens):
        if re.fullmatch(r"\d{4,5}", t):
            result["running_no"] = t
            run_index = i
            break

    if run_index is not None and run_index > 0:
        result["shipping_mark"] = tokens[run_index - 1]

    mfg_index = None
    for i, t in enumerate(tokens):
        if expected_mfg and t == expected_mfg:
            result["mfg"] = t
            mfg_index = i
            break

    if mfg_index is None:
        for i, t in enumerate(tokens):
            if re.fullmatch(r"\d{6}", t):
                result["mfg"] = t
                mfg_index = i
                break

    if mfg_index is not None and mfg_index > 0:
        result["prefix"] = tokens[mfg_index - 1]

    if mfg_index is not None and mfg_index + 1 < len(tokens):
        b = tokens[mfg_index + 1]
        if mfg_index + 2 < len(tokens):
            result["building_suffix"] = f"{b} {tokens[mfg_index + 2]}"
        else:
            result["building_suffix"] = b

    for i, t in enumerate(tokens):
        if t == "EXP" and i + 1 < len(tokens):
            result["exp"] = tokens[i + 1]
            break

    if expected_prefix in ["OL", "OD"]:
        compact = re.sub(r"[^A-Z0-9]", "", text.upper())
        m = re.search(r"OL(\d{6})", compact)
        if m:
            result["prefix"] = "OL"
            result["mfg"] = m.group(1)

    return result


def check_carton(lines, market_type, expected_mfg, expected_exp, building_no, building_suffix, shipping_mark, carton_alpha_code, ai_json):
    details = []
    overall = True
    lines = [normalize(x) for x in lines]
    all_text = " ".join(lines)
    actual = lines[0] if lines else ""
    field_actual = extract_carton_actual_fields(
        all_text,
        expected_mfg,
        carton_alpha_code,
        shipping_mark,
        building_no,
        building_suffix
    )

    if market_type == "TH":
        run_no, sales_code, mfg_code, building_code = parse_th_carton_fields(actual)

        if building_no:
            if building_suffix:
                expected_building_full = f"{building_no} {building_suffix}".upper()
            else:
                expected_building_full = building_no
            # Rebuild visible building field from the remaining tokens so suffix like "3 QR" can be checked strictly.
            parts = normalize(actual).split()
            building_visible = " ".join(parts[3:5]) if len(parts) >= 5 else (parts[3] if len(parts) >= 4 else "")
            building_ok, building_expected = building_suffix_strict_ok(building_visible, building_no, building_suffix)
            building_ok = building_ok and building_no in ["1", "2", "3", "4", "5", "6"]
            building_code = building_visible
        else:
            expected_building_full = ""
            building_ok = True
            building_expected = "ไม่ตรวจเลขอาคาร"
            building_code = building_code.upper() if building_code else ""

        checks = [
            ("Running No. 5 digits", bool(re.fullmatch(r"\d{5}", run_no)), run_no, "ตัวเลข 5 หลัก เช่น 00004"),
            ("Thailand sales code", sales_code == "00", sales_code, "00"),
            ("MFG date", mfg_code == expected_mfg, mfg_code, expected_mfg),
            ("Building No. + Suffix", building_ok, building_code, building_expected),
        ]

        for item, ok, actual_value, expected_value in checks:
            if not ok:
                overall = False
            details.append({
                "item": item,
                "status": "PASS" if ok else "NG",
                "actual": actual_value,
                "expected": expected_value
            })

        # Do not auto-correct 0/8. Show warning as NG if not exact.
        if "8" in run_no or sales_code == "08":
            details.append({
                "item": "OCR Warning",
                "status": "WARN",
                "actual": actual,
                "expected": "Dot Matrix may confuse 0 and 8. Do not auto-correct."
            })

        return overall, details

    # Do not trust AI boolean alone for carton key positions.
    # Shipping Mark = before Running No.
    # Prefix = before MFG Date.
    has_shipping_mark = shipping_mark_before_running_ok(all_text, shipping_mark)
    has_alpha_code = prefix_before_mfg_ok(all_text, carton_alpha_code, expected_mfg)
    has_mfg = expected_mfg in all_text
    has_exp = bool(ai_json.get("has_exp", False))

    if expected_exp:
        has_exp = has_exp or (expected_exp in all_text)
    else:
        has_exp = True

    # OL pattern has no separate Running No.
    actual_run_no, run_ok = extract_export_running_no(all_text, carton_alpha_code)

    building_ok, expected_building_full = building_suffix_strict_ok(all_text, building_no, building_suffix)

    checks = [
        ("Shipping Mark before Running No.", has_shipping_mark, field_actual.get("shipping_mark") or "NOT FOUND", shipping_mark or "ไม่ต้องมี Shipping Mark"),
        ("Running No.", run_ok, actual_run_no or field_actual.get("running_no") or "NOT FOUND", "ตัวเลข 5 หลัก เช่น 00001"),
        ("Prefix before MFG date", has_alpha_code, field_actual.get("prefix") or "NOT FOUND", carton_alpha_code or "ไม่บังคับ Prefix"),
        ("MFG date", has_mfg, field_actual.get("mfg") or "NOT FOUND", expected_mfg),
        ("Building No. + Suffix", building_ok, field_actual.get("building_suffix") or "NOT FOUND", expected_building_full or "ไม่ตรวจเลขอาคาร / ถ้าเลือก QR ต้องอ่านได้ 3 QR ชัดเจนเท่านั้น"),
        ("EXP", has_exp, field_actual.get("exp") or ("ไม่ต้องมี EXP" if not expected_exp else "NOT FOUND"), expected_exp if expected_exp else "ไม่ต้องมี EXP"),
    ]

    for item, ok, actual_value, expected_value in checks:
        if not ok:
            overall = False
        details.append({
            "item": item,
            "status": "PASS" if ok else "NG",
            "actual": actual_value,
            "expected": expected_value
        })

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

        check_type = data.get("checkType", "pouch").strip().lower()
        mode = data.get("mode", "sachet").strip().lower()
        product_type = data.get("productType", "EPC").strip().upper()
        market_type = data.get("marketType", "TH").strip().upper()
        expected_mfg = data.get("mfg", "").strip()
        expected_line = data.get("line", "").strip().upper()
        expected_exp = data.get("exp", "").strip()
        mix_code = data.get("mixCode", "").strip().upper()
        image_data = data.get("image", "")

        building_no = data.get("buildingNo", "").strip()
        building_suffix = data.get("buildingSuffix", "").strip().upper()
        if not building_no:
            building_suffix = ""
        shipping_mark = data.get("shippingMark", "").strip().upper()
        carton_alpha_code = data.get("cartonAlphaCode", "").strip().upper()

        # Carton lot does not separate Laos. Treat Laos as normal Export for carton mode.
        if check_type == "carton" and market_type == "LAOS":
            market_type = "EXPORT"

        if not expected_mfg:
            return jsonify({"error": "กรุณาเลือกวันที่ผลิต"}), 400

        if not image_data:
            return jsonify({"error": "กรุณาอัปโหลดรูปหรือถ่ายรูปก่อน"}), 400

        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY"}), 500

        # EXP is locked by system. Do not trust editable/browser-submitted value.
        auto_exp = calculate_exp(product_type, market_type, expected_mfg)
        expected_exp = auto_exp if auto_exp else ""

        skip_exp = no_exp_required(product_type, market_type)

        if check_type == "pouch" and not skip_exp and not expected_exp:
            return jsonify({"error": "กรุณากรอก EXP หรือเลือกประเภทงานที่ไม่ต้องมี EXP"}), 400

        if check_type == "carton":
            if building_no and building_no not in ["1", "2", "3", "4", "5", "6"]:
                return jsonify({"error": "เลขอาคารต้องเป็น 1-6"}), 400
            if building_suffix and not re.fullmatch(r"[A-Z0-9]{1,5}", building_suffix):
                return jsonify({"error": "Suffix ต้องเป็นตัวอักษร/ตัวเลข 1-5 ตัว เช่น N หรือ QR"}), 400

        image_base64 = image_data.split(",", 1)[1] if "," in image_data else image_data

        raw_ai = read_lot_with_ai(
            image_base64,
            check_type,
            mode,
            product_type,
            market_type,
            expected_mfg,
            expected_line,
            expected_exp,
            mix_code,
            building_no,
            building_suffix,
            shipping_mark,
            carton_alpha_code
        )

        result_json = json.loads(clean_json_text(raw_ai))
        lines = result_json.get("lines", [])

        if check_type == "carton":
            overall, details = check_carton(
                lines,
                market_type,
                expected_mfg,
                expected_exp,
                building_no,
                building_suffix,
                shipping_mark,
                carton_alpha_code,
                result_json
            )
            mode_name = "Carton"
            check_type_name = "CARTON"
        elif mode == "sachet":
            overall, details = check_pouch_sachet(
                lines,
                product_type,
                market_type,
                expected_mfg,
                expected_line,
                expected_exp
            )
            mode_name = "Sachet"
            check_type_name = "POUCH"
        else:
            ai_time = result_json.get("time", "")
            overall, details = check_pouch_linapack(
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
            check_type_name = "POUCH"

        summary = "PASS" if overall else "NG"
        checked_time = now_thai().strftime("%Y-%m-%d %H:%M:%S")

        # Abnormal points are generated from real validation result.
        abnormal_points = build_abnormal_points(details) if summary == "NG" else []

        stamped_filename = stamp_image(
            image_data,
            summary,
            check_type_name,
            product_type,
            market_type,
            mode_name,
            checked_time
        )

        return jsonify({
            "summary": summary,
            "checkType": check_type_name,
            "mode": mode_name,
            "productType": product_type,
            "marketType": market_type,
            "expectedExp": expected_exp if expected_exp else "ไม่ใช้ EXP",
            "lines": lines,
            "details": details,
            "abnormalPoints": abnormal_points,
            "time": checked_time,
            "stampedImageUrl": f"/stamped/{stamped_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
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
<title>IP ONE Lot Checker</title>
<link rel="icon" type="image/png" href="data:image/png;base64,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">
<link rel="apple-touch-icon" href="data:image/png;base64,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">
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
    content:"";
    display:none;
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

.header-logo {
    display:flex;
    align-items:center;
    justify-content:center;
    gap:18px;
    margin:4px 0 10px;
}
.header-logo img {
    width:82px;
    height:auto;
    object-fit:contain;
}
.header-logo h1 {
    margin:0;
    text-align:left;
}
.header-logo p {
    margin:4px 0 0;
    color:var(--muted);
    font-size:14px;
    letter-spacing:0.4px;
}
@media (max-width:640px) {
    .header-logo { gap:10px; }
    .header-logo img { width:64px; }
    .header-logo h1 { font-size:24px; }
}


/* ===== Single-page dashboard layout ===== */
.step-tabs { display:none !important; }
.step-page, .step-page.active { display:block !important; animation:none !important; }
#page1, #page2, #page3 { margin-top:16px; }
#page1 {
    display:grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap:14px;
    background:white;
    padding:16px;
    border-radius:18px;
    border:1px solid var(--border);
}
#page1 > .info, #page1 > #pouchHeader, #page1 > #pouchSection, #page1 > #cartonSection, #page1 > #autoExpInfo, #page1 > #linkedLotInfo { grid-column:1 / -1; }
#pouchHeader {
    display:grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap:12px;
}
#pouchHeader label, #pouchHeader select { margin-top:0; }
#pouchSection, #cartonSection {
    display:grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap:14px;
}
#sachetBox, #linapackBox, #cartonTHBox, #cartonExportBox { margin-top:0; }
#page1 > label { margin-top:0; }
#page1 > input, #page1 > select { margin-top:0; }
#page1 .nav-row { display:none !important; }
#page2 {
    display:grid !important;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap:14px;
}
#page2 h3, #page2 p, #page2 input, #page2 button, #page2 img { margin-top:8px; }
#page2 > hr { display:none; }
#page2 > h3:nth-of-type(1), #page2 > p:nth-of-type(1), #fileInputPouch, #page2 button[onclick="setCaptureTarget('pouch')"], #previewPouch {
    grid-column:1;
}
#page2 > h3:nth-of-type(2), #page2 > p:nth-of-type(2), #fileInputCarton, #page2 button[onclick="setCaptureTarget('carton')"], #previewCarton {
    grid-column:2;
}
#page2 > h3:nth-of-type(3), #captureTargetText, #page2 button[onclick="startCamera()"], #video, #page2 button[onclick="captureImage()"], #canvas, #page2 .nav-row {
    grid-column:1 / -1;
}
#page2 .nav-row { grid-template-columns:1fr; }
#page2 .nav-row .btn-secondary { display:none !important; }
#page3 .nav-row { display:none !important; }
#page3 {
    background:white;
    padding:16px;
    border-radius:18px;
    border:1px solid var(--border);
}
#detail img { max-height:420px; object-fit:contain; background:#f8fafc; }
@media (max-width:900px) {
    #page1, #page2, #pouchHeader, #pouchSection, #cartonSection { grid-template-columns:1fr !important; }
    #page2 > h3:nth-of-type(1), #page2 > p:nth-of-type(1), #fileInputPouch, #page2 button[onclick="setCaptureTarget('pouch')"], #previewPouch,
    #page2 > h3:nth-of-type(2), #page2 > p:nth-of-type(2), #fileInputCarton, #page2 button[onclick="setCaptureTarget('carton')"], #previewCarton { grid-column:1 / -1; }
}



/* ===== Horizontal compact UI override ===== */
body { padding:8px; background:#eef3f8; }
.box {
    max-width:1540px;
    padding:10px;
    border-radius:16px;
    box-shadow:0 10px 28px rgba(15,23,42,.12);
}
.header-logo {
    justify-content:flex-start;
    background:#071f38;
    color:white;
    padding:10px 14px;
    border-radius:14px;
    margin:0 0 10px;
}
.header-logo img { width:54px; background:white; border-radius:10px; padding:4px; margin-top:0; border:0; }
.header-logo h1 { font-size:24px; color:white; letter-spacing:.3px; }
.header-logo p { color:#cbd5e1; font-size:12px; margin-top:0; }

label { font-size:13px; margin-top:6px; }
input, select { font-size:14px; padding:8px 10px; border-radius:10px; margin-top:4px; }
button { font-size:14px; padding:9px 10px; border-radius:10px; margin-top:6px; box-shadow:none; }
h3 { font-size:16px; margin:4px 0; }
.small { font-size:12px; margin:4px 0; }
.info, .warn { padding:8px 10px; border-radius:10px; margin-top:6px; font-size:13px; }
.pass, .ng { font-size:30px; padding:12px; border-radius:14px; margin-top:8px; }
table { margin-top:8px; border-radius:10px; }
th, td { font-size:12px; padding:6px 7px; }
hr { margin:8px 0; }

.step-tabs { display:none !important; }
.step-page, .step-page.active { display:block !important; animation:none !important; }
#page1, #page2, #page3 {
    margin-top:8px;
    background:#fff;
    border:1px solid var(--border);
    border-radius:14px;
    padding:10px;
}

#page1 {
    display:grid !important;
    grid-template-columns: 1.05fr 1.05fr .9fr .9fr 1fr 1fr;
    gap:8px 10px;
    align-items:end;
}
#page1 > .info:first-of-type { display:none !important; }
#page1 > label, #page1 > input, #page1 > select { margin:0; }
#page1 > label { align-self:end; }
#pouchHeader {
    grid-column:1 / span 2;
    display:grid !important;
    grid-template-columns:1fr 1fr;
    gap:8px;
    padding:0 !important;
    border:0 !important;
    background:transparent !important;
    margin:0 !important;
}
#pouchHeader label { margin:0; }
#pouchHeader select { margin:4px 0 0; }
#pouchSection {
    grid-column:1 / span 3;
    display:grid !important;
    grid-template-columns:1fr;
    gap:8px;
    padding:8px !important;
    margin:0 !important;
    border-radius:12px !important;
}
#cartonSection {
    grid-column:4 / span 3;
    display:grid !important;
    grid-template-columns:1fr;
    gap:8px;
    padding:8px !important;
    margin:0 !important;
    border-radius:12px !important;
}
#sachetBox, #linapackBox, #cartonTHBox, #cartonExportBox {
    padding:8px !important;
    border-radius:12px !important;
    margin:0 !important;
}
#linapackBox, #cartonTHBox, #cartonExportBox {
    display:grid;
    grid-template-columns:repeat(3, minmax(0,1fr));
    gap:6px 8px;
    align-items:end;
}
#mixCodeBox { display:grid; grid-template-columns:1fr 1fr; gap:6px; grid-column:span 2; }
#mixCodeBox .small, #linapackHint, #cartonTHBox .small, #cartonExportBox .small { display:none; }
#autoExpInfo, #linkedLotInfo { grid-column:1 / -1; margin:0; }
#page1 .nav-row { display:none !important; }

#page2 {
    display:grid !important;
    grid-template-columns: 1fr 1fr 300px;
    gap:10px;
    align-items:start;
}
#page2 > h3:nth-of-type(1), #page2 > p:nth-of-type(1), #fileInputPouch, #page2 button[onclick="setCaptureTarget('pouch')"], #previewPouch { grid-column:1; }
#page2 > h3:nth-of-type(2), #page2 > p:nth-of-type(2), #fileInputCarton, #page2 button[onclick="setCaptureTarget('carton')"], #previewCarton { grid-column:2; }
#page2 > h3:nth-of-type(3), #captureTargetText, #page2 button[onclick="startCamera()"], #video, #page2 button[onclick="captureImage()"], #canvas { grid-column:3; }
#page2 > hr { display:none; }
#page2 h3, #page2 p, #page2 input, #page2 button, #page2 img, #page2 video { margin-top:4px; }
#previewPouch, #previewCarton, #video {
    height:250px;
    max-height:250px;
    object-fit:contain;
    background:#0f172a;
    border-radius:12px;
}
#page2 .nav-row {
    grid-column:1 / -1;
    display:grid !important;
    grid-template-columns:1fr;
    margin-top:0;
}
#page2 .nav-row .btn-secondary { display:none !important; }
#page2 .nav-row .btn-success { font-size:18px; padding:12px; }

#page3 { padding:10px; }
#page3 .nav-row { display:none !important; }
#result { margin-top:0; }
#detail { display:grid; grid-template-columns: 1.05fr 1.05fr .9fr; gap:10px; align-items:start; }
#detail > img, #detail .download { max-width:100%; }
#detail img { max-height:260px; object-fit:contain; background:#f8fafc; border-radius:12px; }
pre { max-height:240px; font-size:12px; padding:8px; border-radius:10px; }
.download { font-size:14px; padding:10px; border-radius:10px; margin-top:8px; }

@media (max-width:1100px) {
    #page1 { grid-template-columns:repeat(2, minmax(0,1fr)); }
    #pouchHeader, #pouchSection, #cartonSection, #autoExpInfo, #linkedLotInfo { grid-column:1 / -1; }
    #page2 { grid-template-columns:1fr 1fr; }
    #page2 > h3:nth-of-type(3), #captureTargetText, #page2 button[onclick="startCamera()"], #video, #page2 button[onclick="captureImage()"], #canvas { grid-column:1 / -1; }
    #detail { grid-template-columns:1fr; }
}
@media (max-width:720px) {
    .box { padding:8px; }
    .header-logo h1 { font-size:20px; }
    #page1, #page2, #linapackBox, #cartonTHBox, #cartonExportBox, #mixCodeBox { grid-template-columns:1fr !important; }
    #page2 > * { grid-column:1 / -1 !important; }
    #previewPouch, #previewCarton, #video { height:220px; max-height:220px; }
}


/* ===== Label row + input row compact form ===== */
#page1 {
    grid-template-columns: 1fr 1fr !important;
    gap:8px !important;
    align-items:start !important;
}
.compact-mode-info, #pouchHeader, #autoExpInfo, #linkedLotInfo { grid-column:1 / -1 !important; }
.section-card {
    background:#f8fafc !important;
    border:1px solid #e2e8f0 !important;
    border-radius:12px !important;
    padding:8px !important;
    margin:0 !important;
}
.section-title {
    font-weight:800;
    font-size:13px;
    color:#0f172a;
    margin:0 0 6px;
}
.config-grid {
    display:grid !important;
    gap:4px 8px !important;
    align-items:end !important;
    padding:0 !important;
    margin:0 !important;
    background:transparent !important;
    border:0 !important;
}
.config-grid.grid-2 { grid-template-columns:repeat(2, minmax(0,1fr)) !important; }
.config-grid.grid-3 { grid-template-columns:repeat(3, minmax(0,1fr)) !important; }
.config-grid.grid-5 { grid-template-columns:repeat(5, minmax(0,1fr)) !important; }
.config-grid.no-pad { padding:0 !important; }
.config-grid label {
    margin:0 !important;
    font-size:12px !important;
    line-height:1.1 !important;
    color:#475569 !important;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}
.config-grid input, .config-grid select {
    margin:0 !important;
    height:34px !important;
    font-size:13px !important;
    padding:6px 8px !important;
    min-width:0 !important;
}
.full-span { grid-column:1 / -1 !important; }
#pouchSection, #cartonSection { display:block !important; }
#sachetBox, #linapackBox, #cartonTHBox, #cartonExportBox { padding:0 !important; border:0 !important; background:transparent !important; }
#mixCodeBox { margin-top:6px !important; }
#mixCodeBox .small, #linapackHint, #cartonTHBox .small, #cartonExportBox .small { display:none !important; }
#autoExpInfo, #linkedLotInfo { font-size:12px !important; padding:6px 8px !important; }
@media (max-width:1100px) {
    #page1 { grid-template-columns:1fr !important; }
    .config-grid.grid-5 { grid-template-columns:repeat(3, minmax(0,1fr)) !important; }
}
@media (max-width:720px) {
    .config-grid.grid-2, .config-grid.grid-3, .config-grid.grid-5 { grid-template-columns:1fr !important; }
}


/* ===== Photo cards same-row layout override ===== */
#page2.photo-grid {
    display:grid !important;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 280px !important;
    gap:10px !important;
    align-items:start !important;
}
#page2.photo-grid > * { grid-column:auto !important; }
.photo-card {
    background:#ffffff;
    border:1px solid var(--border);
    border-radius:14px;
    padding:10px;
    min-height:100%;
}
.photo-card h3 {
    margin:0 0 6px !important;
    font-size:16px !important;
    line-height:1.2 !important;
}
.photo-card .small {
    margin:0 0 8px !important;
    min-height:32px;
    font-size:12px !important;
}
.photo-card input,
.photo-card button,
.photo-card img,
.photo-card video,
.photo-card .info {
    margin-top:6px !important;
}
#previewPouch, #previewCarton, #video {
    width:100% !important;
    height:230px !important;
    max-height:230px !important;
    object-fit:contain !important;
    background:#0f172a !important;
    border-radius:12px !important;
}
#page2.photo-grid .camera-card { grid-column:3 !important; }
#page2.photo-grid .check-row {
    grid-column:1 / -1 !important;
    display:grid !important;
    grid-template-columns:1fr !important;
    margin-top:0 !important;
}
#page2.photo-grid .check-row .btn-secondary { display:none !important; }
#page2.photo-grid .check-row .btn-success {
    font-size:18px !important;
    padding:12px !important;
    margin-top:0 !important;
}
@media (max-width:1100px) {
    #page2.photo-grid { grid-template-columns:1fr 1fr !important; }
    #page2.photo-grid .camera-card { grid-column:1 / -1 !important; }
}
@media (max-width:720px) {
    #page2.photo-grid { grid-template-columns:1fr !important; }
    #page2.photo-grid > * { grid-column:1 / -1 !important; }
}


/* ===== Final spacing refinement: make compact form easier to read ===== */
#page1 {
    gap:12px !important;
}
.section-card {
    padding:12px !important;
}
.section-title {
    margin:0 0 10px !important;
    line-height:1.35 !important;
}
.config-grid {
    gap:10px 12px !important;
}
.config-grid label {
    line-height:1.35 !important;
    padding-bottom:2px !important;
}
.config-grid input,
.config-grid select {
    height:38px !important;
    padding:7px 10px !important;
}
#mixCodeBox {
    margin-top:10px !important;
}
#autoExpInfo,
#linkedLotInfo {
    font-size:13px !important;
    padding:10px 12px !important;
    line-height:1.6 !important;
}
#page2.photo-grid {
    gap:12px !important;
}
.photo-card {
    padding:12px !important;
}
.photo-card h3 {
    margin-bottom:8px !important;
}
.photo-card .small {
    margin-bottom:10px !important;
    line-height:1.45 !important;
}

</style>
</head>
<body>

<div class="box">
<div class="header-logo">
    <img src="data:image/png;base64,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" alt="IP One Logo">
    <div>
        <h1>IP ONE LOT CHECKER</h1>
        <p>AI Lot Verification System</p>
    </div>
</div>

<div class="step-tabs">
    <button id="tab1" onclick="goPage(1)">1 ตั้งค่า</button>
    <button id="tab2" onclick="goPage(2)">2 รูปภาพ</button>
    <button id="tab3" onclick="goPage(3)">3 ผลตรวจ</button>
</div>

<div id="page1" class="step-page active">

<input type="hidden" id="checkType" value="both">
<div class="info compact-mode-info"><b>โหมดตรวจรวม:</b> ตรวจล็อตซองและล็อตกล่องพร้อมกัน โดยใช้ MFG เดียวกันเป็นตัวกลาง</div>

<div id="pouchHeader" class="config-grid grid-5">
    <label>ประเภทไลน์</label>
    <label>ประเภทผลิตภัณฑ์</label>
    <label>ประเภทงาน</label>
    <label>วันที่ผลิต (MFG)</label>
    <label>MFG ที่ใช้ตรวจ</label>

    <select id="mode" onchange="changeMode()">
        <option value="sachet">Sachet</option>
        <option value="linapack">Linapack</option>
    </select>
    <select id="productType" onchange="changeProduct()">
        <option value="EPC">EPC</option>
        <option value="EPW">EPW</option>
    </select>
    <select id="marketType" onchange="changeProduct()">
        <option value="TH">งานไทย</option>
        <option value="EXPORT">งานต่างประเทศ</option>
        <option id="marketLaosOption" value="LAOS">งานต่างประเทศ ลาว</option>
    </select>
    <input type="date" id="mfgDate" onchange="updateMFGFromDate()">
    <input id="mfg" value="" readonly>
</div>

<div id="pouchSection" class="section-card">
    <div class="section-title">ข้อมูลล็อตซอง</div>
    <div id="sachetBox" class="config-grid grid-2">
        <label>Sachet Code</label>
        <label>EXP</label>

        <input id="sachetLine" value="MS11" placeholder="เช่น MS11">
        <input id="sachetExp" value="" placeholder="Auto Calculated" readonly>

        <p class="small full-span">Sachet: MFG 080626 MS11 1 EXP 080927 ถึง MS11 6</p>
    </div>

    <div id="linapackBox" class="config-grid grid-2" style="display:none;">
        <label>เครื่อง Linapack</label>
        <label>EXP</label>

        <select id="lpMachine" onchange="updateExpectedLinkedLots()">
            <option value="LP1">LP1</option><option value="LP2">LP2</option><option value="LP3">LP3</option>
            <option value="LP4">LP4</option><option value="LP5">LP5</option><option value="LP6">LP6</option>
            <option value="LP7" selected>LP7</option><option value="LP8">LP8</option><option value="LP9">LP9</option>
        </select>
        <input id="linapackExp" value="" placeholder="Auto Calculated" readonly>

        <div id="mixCodeBox" class="full-span" style="display:none;">
            <div class="config-grid grid-2 no-pad">
                <label>วันที่ผสม</label>
                <label>รหัสวันที่ผสม / Mix Code</label>
                <input type="date" id="mixDate" onchange="updateMixCodeFromDate()">
                <input id="mixCode" value="" placeholder="Auto เช่น 18F" readonly>
            </div>
            <p class="small">เลือกวันที่จากปฏิทิน ระบบจะแปลงเดือนเป็น A-L อัตโนมัติ เช่น 18 มิถุนายน = 18F</p>
        </div>

        <p id="linapackHint" class="small full-span"></p>
    </div>
</div>

<div id="cartonSection" class="section-card">
    <div class="section-title">ข้อมูลล็อตกล่อง</div>
    <div id="cartonTHBox" class="config-grid grid-2">
        <label>เลขอาคาร</label>
        <label>Suffix หลังเลขอาคาร</label>

        <select id="buildingNo" onchange="updateExpectedLinkedLots()">
            <option value="">ไม่มี</option><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option>
            <option value="4">4</option><option value="5">5</option><option value="6">6</option>
        </select>
        <input id="buildingSuffixTH" value="" placeholder="เว้นว่างได้ เช่น N หรือ QR" oninput="updateExpectedLinkedLots()">

        <p class="small full-span">กล่องงานไทย: ระบบจะตรวจรูปแบบ <b>00001 00 080626 3</b></p>
    </div>

    <div id="cartonExportBox" class="config-grid grid-5" style="display:none;">
        <label>Prefix</label>
        <label>Shipping Mark</label>
        <label>เลขอาคาร</label>
        <label>Suffix หลังเลขอาคาร</label>
        <label>EXP สำหรับ Pattern ที่มี EXP</label>

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
        <input id="shippingMark" value="" placeholder="ระบบเติมจาก Prefix อัตโนมัติ" readonly>
        <select id="buildingNoExport" onchange="updateExpectedLinkedLots()">
            <option value="">ไม่มี</option><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option>
            <option value="4">4</option><option value="5">5</option><option value="6">6</option>
        </select>
        <input id="buildingSuffixExport" value="" placeholder="เว้นว่างได้ เช่น N หรือ QR" oninput="updateExpectedLinkedLots()">
        <input id="cartonExp" value="" placeholder="Auto Calculated" readonly>

        <p class="small full-span">กล่องต่างประเทศ: ตรวจ Prefix / Shipping Mark / Running No. / MFG / EXP ตาม Pattern</p>
    </div>
</div>

<div id="autoExpInfo" class="info"></div>
<div id="linkedLotInfo" class="info"></div>

<div class="nav-row">
    
</div>
</div>

<div id="page2" class="step-page photo-grid">
    <div class="photo-card pouch-card">
        <h3>รูปที่ 1: ซอง</h3>
        <p class="small">ถ่าย/อัปโหลดรูปล็อตบนซองให้เห็น MFG / Mix Code / Machine / Time / EXP</p>
        <input type="file" id="fileInputPouch" accept="image/*">
        <button onclick="setCaptureTarget('pouch')">เลือกถ่ายรูปซอง</button>
        <img id="previewPouch" style="display:none;">
    </div>

    <div class="photo-card carton-card">
        <h3>รูปที่ 2: กล่อง</h3>
        <p class="small">ถ่าย/อัปโหลดรูปล็อตบนกล่อง เช่น 00001 00 240626 3</p>
        <input type="file" id="fileInputCarton" accept="image/*">
        <button onclick="setCaptureTarget('carton')">เลือกถ่ายรูปกล่อง</button>
        <img id="previewCarton" style="display:none;">
    </div>

    <div class="photo-card camera-card">
        <h3>ถ่ายจากกล้อง</h3>
        <p id="captureTargetText" class="info">เลือกก่อนว่าจะถ่ายรูปซองหรือรูปกล่อง</p>
        <button onclick="startCamera()">เปิดกล้อง</button>
        <video id="video" autoplay playsinline></video>
        <button onclick="captureImage()">ถ่ายรูปตามที่เลือก</button>
        <canvas id="canvas" style="display:none;"></canvas>
    </div>

    <div class="nav-row check-row">
        <button class="btn-secondary" onclick="goPage(1)">ย้อนกลับ</button>
        <button class="btn-success" onclick="sendCheck()">ตรวจสอบล็อตซอง + กล่อง</button>
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
let pouchImageData = "";
let cartonImageData = "";
let captureTarget = "pouch";

function goPage(page) {
    // Single-page layout: keep every section visible.
    for (let i = 1; i <= 3; i++) {
        const pageEl = document.getElementById("page" + i);
        if (pageEl) pageEl.classList.add("active");
    }
    const target = document.getElementById(page === 2 ? "page2" : (page === 3 ? "page3" : "page1"));
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
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
    const todayText = `${yyyy}-${mm}-${dd}`;
    document.getElementById("mfgDate").value = todayText;

    const mixDate = document.getElementById("mixDate");
    if (mixDate && !mixDate.value) {
        mixDate.value = todayText;
    }

    updateMFGFromDate();
    updateMixCodeFromDate();
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
    updateExpectedLinkedLots();
}

const MIX_MONTH_CODES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"];

function updateMixCodeFromDate() {
    const mixDateInput = document.getElementById("mixDate");
    const mixCodeInput = document.getElementById("mixCode");
    if (!mixDateInput || !mixCodeInput) return;

    const dateValue = mixDateInput.value;
    if (!dateValue) {
        mixCodeInput.value = "";
        return;
    }

    const parts = dateValue.split("-");
    const day = parts[2];
    const monthIndex = parseInt(parts[1], 10) - 1;
    const monthCode = MIX_MONTH_CODES[monthIndex] || "";
    mixCodeInput.value = day + monthCode;
    updateExpectedLinkedLots();
}


function addMonthsYY(ddmmyy, months) {
    if (!ddmmyy || ddmmyy.length !== 6) return "";
    const dd = parseInt(ddmmyy.slice(0,2), 10);
    const mm = parseInt(ddmmyy.slice(2,4), 10) - 1;
    const yy = 2000 + parseInt(ddmmyy.slice(4,6), 10);
    const d = new Date(yy, mm, dd);
    d.setMonth(d.getMonth() + months);
    const outDD = String(d.getDate()).padStart(2, "0");
    const outMM = String(d.getMonth() + 1).padStart(2, "0");
    const outYY = String(d.getFullYear()).slice(-2);
    return outDD + outMM + outYY;
}

function addYearsYY(ddmmyy, years) {
    if (!ddmmyy || ddmmyy.length !== 6) return "";
    const dd = parseInt(ddmmyy.slice(0,2), 10);
    const mm = parseInt(ddmmyy.slice(2,4), 10);
    const yy = 2000 + parseInt(ddmmyy.slice(4,6), 10) + years;
    return String(dd).padStart(2, "0") + String(mm).padStart(2, "0") + String(yy).slice(-2);
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

    try {
        const cartonExp = document.getElementById("cartonExp");
        if (cartonExp) cartonExp.value = (market === "TH") ? "" : (document.getElementById("linapackExp").value || document.getElementById("sachetExp").value || "");
    } catch(e) {}

    // LINAPACK_RULE_EXP_FIX
    try {
        const product = document.getElementById("productType").value;
        const market = document.getElementById("marketType").value;
        const mfg = document.getElementById("mfg").value;
        const linapackExp = document.getElementById("linapackExp");

        if (product === "EPC" && market === "TH") {
            linapackExp.value = addMonthsYY(mfg, 15);
            linapackExp.disabled = false;
        } else if (product === "EPW" && market === "LAOS") {
            linapackExp.value = addYearsYY(mfg, 3);
            linapackExp.disabled = false;
        } else {
            linapackExp.value = "";
            linapackExp.disabled = true;
        }
    } catch(e) {}
}


function buildExpectedPouchLot() {
    const mode = document.getElementById("mode").value;
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mfg = document.getElementById("mfg").value.trim();
    if (!/^\d{6}$/.test(mfg)) return "-";

    if (mode === "sachet") {
        const line = document.getElementById("sachetLine").value.trim().toUpperCase() || "MS11";
        const exp = document.getElementById("sachetExp").value.trim();
        return exp ? `MFG ${mfg} ${line} 1 EXP ${exp}` : `MFG ${mfg} ${line} 1`;
    }

    const machine = document.getElementById("lpMachine").value.trim().toUpperCase();
    const mixCode = document.getElementById("mixCode").value.trim().toUpperCase();
    const exp = document.getElementById("linapackExp").value.trim();
    const needMix = (product === "EPW" && (market === "TH" || market === "LAOS"));
    let line1 = `MFG ${mfg}`;
    if (needMix && mixCode) line1 += ` ${mixCode}`;
    line1 += ` ${machine} เวลา`;
    if (exp) return `${line1}<br>EXP ${exp}`;
    return line1;
}

function buildExpectedCartonLot() {
    const market = document.getElementById("marketType").value;
    const mfg = document.getElementById("mfg").value.trim();
    if (!/^\d{6}$/.test(mfg)) return "-";

    if (market === "TH") {
        const building = document.getElementById("buildingNo").value.trim();
        const suffix = document.getElementById("buildingSuffixTH").value.trim().toUpperCase();
        const buildingFull = building ? `${building}${suffix ? " " + suffix : ""}` : "";
        return `00001 00 ${mfg}${buildingFull ? " " + buildingFull : ""}`;
    }

    const prefix = document.getElementById("cartonPrefix").value;
    const shipping = document.getElementById("shippingMark").value.trim().toUpperCase();
    const building = document.getElementById("buildingNoExport").value.trim();
    const suffix = document.getElementById("buildingSuffixExport").value.trim().toUpperCase();
    const exp = document.getElementById("cartonExp").value.trim();
    const buildingFull = building ? `${building}${suffix ? " " + suffix : ""}` : "";
    const shipPart = shipping ? shipping + " " : "";
    return `${shipPart}00001 ${prefix} ${mfg}${buildingFull ? " " + buildingFull : ""}${exp ? " EXP " + exp : ""}`;
}

function updateExpectedLinkedLots() {
    const box = document.getElementById("linkedLotInfo");
    if (!box) return;
    const mfg = document.getElementById("mfg").value.trim();
    if (!/^\d{6}$/.test(mfg)) {
        box.innerHTML = "Lot ซองและ Lot กล่องจะเชื่อมกันหลังเลือกวันที่ผลิต";
        return;
    }
    const pouchLot = buildExpectedPouchLot();
    const cartonLot = buildExpectedCartonLot();
    box.innerHTML = `<b>ข้อมูลที่เชื่อมโยงกันจาก MFG เดียวกัน</b><br>` +
                    `ซองที่ควรเป็น: <b>${pouchLot}</b><br>` +
                    `กล่องที่ควรเป็น: <b>${cartonLot}</b><br>` +
                    `<span class="small">ระบบใช้ MFG เดียวกันตรวจทั้งซองและกล่อง ถ้าซองเป็น ${mfg} กล่องต้องเป็น ${mfg} เช่นกัน</span>`;
}

function changeCheckType() {
    document.getElementById("checkType").value = "both";
    document.getElementById("pouchHeader").style.display = "block";
    document.getElementById("pouchSection").style.display = "block";
    document.getElementById("cartonSection").style.display = "block";
    const laosOption = document.getElementById("marketLaosOption");
    if (laosOption) laosOption.style.display = "block";
    changeProduct();
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
    const cartonTHBox = document.getElementById("cartonTHBox");
    const cartonExportBox = document.getElementById("cartonExportBox");
    const linapackExp = document.getElementById("linapackExp");
    const sachetExp = document.getElementById("sachetExp");
    const hint = document.getElementById("linapackHint");

    const noExp = !(
        (product === "EPC" && market === "TH") ||
        (product === "EPW" && market === "LAOS")
    );

    sachetExp.disabled = noExp;
    linapackExp.disabled = noExp;

    cartonTHBox.style.display = market === "TH" ? "block" : "none";
    cartonExportBox.style.display = (market === "EXPORT" || market === "LAOS") ? "block" : "none";
    if (market === "EXPORT" || market === "LAOS") updateShippingMarkByPrefix();

    if (mode === "linapack") {
        const needMix = (product === "EPW" && (market === "TH" || market === "LAOS"));
        mixCodeBox.style.display = needMix ? "block" : "none";
        if (needMix) updateMixCodeFromDate();

        if (product === "EPC" && market === "TH") {
            hint.innerHTML = "EPC ไทย: ตรวจ MFG + เลขเครื่อง + เวลา + EXP อายุ 1 ปี 3 เดือน";
        } else if (product === "EPC" && market === "EXPORT") {
            hint.innerHTML = "EPC ต่างประเทศ: ตรวจ MFG + เลขเครื่อง + เวลา ไม่มี EXP";
        } else if (product === "EPW" && market === "TH") {
            hint.innerHTML = "EPW ไทย: ตรวจ MFG + วันผสม + เลขเครื่อง + เวลา ไม่มี EXP";
        } else if (product === "EPW" && market === "EXPORT") {
            hint.innerHTML = "EPW ต่างประเทศ: ตรวจ MFG + เลขเครื่อง + เวลา ไม่มี EXP";
        } else if (product === "EPW" && market === "LAOS") {
            hint.innerHTML = "EPW ลาว: ตรวจ MFG + วันผสม + เลขเครื่อง + เวลา + EXP อายุ 3 ปี";
        } else {
            hint.innerHTML = "";
        }
    }

    document.getElementById("result").innerHTML = "";
    document.getElementById("detail").innerHTML = "";
    autoExp();
    updateExpectedLinkedLots();
}

function setImage(kind, dataUrl) {
    if (kind === "carton") {
        cartonImageData = dataUrl;
        const preview = document.getElementById("previewCarton");
        preview.src = dataUrl;
        preview.style.display = "block";
    } else {
        pouchImageData = dataUrl;
        const preview = document.getElementById("previewPouch");
        preview.src = dataUrl;
        preview.style.display = "block";
    }
}

function setCaptureTarget(kind) {
    captureTarget = kind === "carton" ? "carton" : "pouch";
    document.getElementById("captureTargetText").innerHTML = captureTarget === "carton"
        ? "ตอนนี้เลือก: ถ่ายรูปกล่อง"
        : "ตอนนี้เลือก: ถ่ายรูปซอง";
}

document.getElementById("fileInputPouch").addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) { setImage("pouch", event.target.result); };
    reader.readAsDataURL(file);
});

document.getElementById("fileInputCarton").addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) { setImage("carton", event.target.result); };
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

    if (!video.videoWidth) {
        document.getElementById("result").innerHTML = '<div class="ng">กรุณาเปิดกล้องก่อน</div>';
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const captured = canvas.toDataURL("image/jpeg", 0.9);
    setImage(captureTarget, captured);
}

async function sendCheck() {
    const resultDiv = document.getElementById("result");
    const detailDiv = document.getElementById("detail");

    if (!pouchImageData || !cartonImageData) {
        resultDiv.innerHTML = '<div class="ng">กรุณาถ่าย/อัปโหลดให้ครบทั้งรูปซองและรูปกล่อง</div>';
        return;
    }

    const checkType = "both";
    const mode = document.getElementById("mode").value;
    const productType = document.getElementById("productType").value;
    const marketType = document.getElementById("marketType").value;

    let payload = {
        checkType: checkType,
        mode: mode,
        productType: productType,
        marketType: marketType,
        mfg: document.getElementById("mfg").value,
        pouchImage: pouchImageData,
        cartonImage: cartonImageData,
        image: pouchImageData,
        buildingNo: marketType === "TH" ? document.getElementById("buildingNo").value : document.getElementById("buildingNoExport").value,
        buildingSuffix: marketType === "TH" ? document.getElementById("buildingSuffixTH").value : document.getElementById("buildingSuffixExport").value,
        shippingMark: (marketType === "EXPORT" || marketType === "LAOS") ? document.getElementById("shippingMark").value : "",
        cartonAlphaCode: (marketType === "EXPORT" || marketType === "LAOS") ? document.getElementById("cartonPrefix").value : ""
    };

    if (mode === "sachet") {
        payload.line = document.getElementById("sachetLine").value;
        payload.exp = document.getElementById("sachetExp").value;
        payload.mixCode = "";
    } else {
        payload.line = document.getElementById("lpMachine").value;
        payload.exp = document.getElementById("linapackExp").value;
        updateMixCodeFromDate();
        const needMix = (productType === "EPW" && (marketType === "TH" || marketType === "LAOS"));
        if (needMix && !document.getElementById("mixCode").value) {
            resultDiv.innerHTML = '<div class="ng">กรุณาเลือกวันที่ผสม</div>';
            goPage(1);
            return;
        }
        payload.mixCode = document.getElementById("mixCode").value;
    }


    resultDiv.innerHTML = '<div class="warn">กำลังตรวจสอบ...</div>';
    goPage(3);
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
        html += `<p><b>โหมด:</b> ${data.checkType}</p>`;
        if (data.expectedPouchLot) html += `<p><b>Lot ซองที่ควรเป็น:</b> ${data.expectedPouchLot}</p>`;
        if (data.expectedCartonLot) html += `<p><b>Lot กล่องที่ควรเป็น:</b> ${data.expectedCartonLot}</p>`;
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

window.onload = function() {
    setTodayDefault();
    updateShippingMarkByPrefix();
    changeCheckType();
    updateExpectedLinkedLots();
    goPage(1);
};
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




def has_unclear_text(value):
    """Return True when OCR/AI is not confident. In strict inspection, unclear text must be NG."""
    raw = normalize(value)
    return (
        "?" in raw
        or "UNCLEAR" in raw
        or "UNKNOWN" in raw
        or "NOT CLEAR" in raw
        or "NOT READABLE" in raw
    )

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


def exp_date_plus_years(ddmmyy, years):
    try:
        d = datetime.strptime(str(ddmmyy), "%d%m%y")
        try:
            new_d = d.replace(year=d.year + int(years))
        except ValueError:
            # handles 29 Feb -> 28 Feb on non-leap year
            new_d = d.replace(month=2, day=28, year=d.year + int(years))
        return new_d.strftime("%d%m%y")
    except Exception:
        return str(ddmmyy or "")

def exp_date_plus_days(ddmmyy, days):
    try:
        d = datetime.strptime(str(ddmmyy), "%d%m%y")
        return (d + timedelta(days=int(days))).strftime("%d%m%y")
    except Exception:
        return str(ddmmyy or "")

def exp_date_plus_months(ddmmyy, months):
    try:
        d = datetime.strptime(str(ddmmyy), "%d%m%y")
        month = d.month - 1 + int(months)
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, monthrange(year, month)[1])
        return datetime(year, month, day).strftime("%d%m%y")
    except Exception:
        return str(ddmmyy or "")


def exp_date_plus_years(ddmmyy, years):
    try:
        d = datetime.strptime(str(ddmmyy), "%d%m%y")
        try:
            new_d = d.replace(year=d.year + int(years))
        except ValueError:
            new_d = d.replace(month=2, day=28, year=d.year + int(years))
        return new_d.strftime("%d%m%y")
    except Exception:
        return str(ddmmyy or "")


def linapack_requires_mix(product_type, market_type):
    product_type = str(product_type or "").upper()
    market_type = str(market_type or "").upper()
    return product_type == "EPW" and market_type in ["TH", "LAOS"]


def linapack_requires_exp(product_type, market_type):
    product_type = str(product_type or "").upper()
    market_type = str(market_type or "").upper()
    if product_type == "EPC" and market_type == "TH":
        return True
    if product_type == "EPW" and market_type == "LAOS":
        return True
    return False


def expected_linapack_exp(product_type, market_type, expected_mfg):
    product_type = str(product_type or "").upper()
    market_type = str(market_type or "").upper()
    if product_type == "EPC" and market_type == "TH":
        return exp_date_plus_months(expected_mfg, 15)
    if product_type == "EPW" and market_type == "LAOS":
        return exp_date_plus_years(expected_mfg, 3)
    return ""

def no_exp_required(product_type, market_type):
    """
    True = ไม่ต้องมี EXP
    False = ต้องมี EXP

    Linapack rules:
    EPC TH      : MFG DDMMYY เลขเครื่อง เวลา + EXP DDMMYY อายุ 1 ปี 3 เดือน
    EPC EXPORT  : MFG DDMMYY เลขเครื่อง เวลา
    EPW TH      : MFG DDMMYY วันผสม เลขเครื่อง เวลา
    EPW EXPORT  : MFG DDMMYY เลขเครื่อง เวลา
    EPW LAOS    : MFG DDMMYY วันผสม เลขเครื่อง เวลา + EXP DDMMYY อายุ 3 ปี
    """
    return not linapack_requires_exp(product_type, market_type)


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




def _open_base64_image(image_base64):
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    image_bytes = base64.b64decode(image_base64)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _resize_to_fit(image, max_w, max_h):
    w, h = image.size
    scale = min(max_w / w, max_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return image.resize((new_w, new_h), Image.LANCZOS)


def stamp_image(image_base64, summary, check_type, product_type, market_type, mode, checked_time, carton_image_base64=None):
    """
    Create stamped evidence image.
    - Single mode: stamp one image as before.
    - POUCH + CARTON mode: create one report image that contains BOTH pouch and carton photos.
    """
    if carton_image_base64:
        pouch_img = _open_base64_image(image_base64)
        carton_img = _open_base64_image(carton_image_base64)

        canvas_w = 1800
        header_h = 155
        footer_h = 170
        gap = 30
        margin = 40
        panel_w = (canvas_w - (margin * 2) - gap) // 2
        image_max_h = 920

        pouch_resized = _resize_to_fit(pouch_img, panel_w, image_max_h)
        carton_resized = _resize_to_fit(carton_img, panel_w, image_max_h)
        image_area_h = max(pouch_resized.height, carton_resized.height) + 76
        canvas_h = header_h + image_area_h + footer_h + margin

        image = Image.new("RGB", (canvas_w, canvas_h), (245, 248, 252))
        draw = ImageDraw.Draw(image)

        title_font = get_font(56)
        body_font = get_font(30)
        label_font = get_font(34)

        if summary == "PASS":
            title = "LOT CHECK PASS"
            line2 = "POUCH + CARTON VERIFIED"
            color = (0, 150, 0)
        else:
            title = "LOT CHECK NG"
            line2 = "POUCH + CARTON VERIFICATION FAILED"
            color = (220, 0, 0)

        # Header
        draw.rectangle([0, 0, canvas_w, header_h], fill=(12, 37, 64))
        draw.text((margin, 30), title, font=title_font, fill=color)
        draw.text((margin, 96), line2, font=body_font, fill=(255, 255, 255))
        time_text = f"By Lot Checker | {checked_time}"
        tb = draw.textbbox((0, 0), time_text, font=body_font)
        draw.text((canvas_w - margin - (tb[2] - tb[0]), 56), time_text, font=body_font, fill=(255, 255, 255))

        # Panels
        y0 = header_h + 30
        left_x = margin
        right_x = margin + panel_w + gap
        panel_h = image_area_h - 20
        for x, label in [(left_x, "POUCH / รูปซอง"), (right_x, "CARTON / รูปกล่อง")]:
            draw.rounded_rectangle([x, y0, x + panel_w, y0 + panel_h], radius=22, fill=(255, 255, 255), outline=(215, 225, 235), width=3)
            draw.text((x + 22, y0 + 20), label, font=label_font, fill=(20, 40, 60))

        pouch_x = left_x + (panel_w - pouch_resized.width) // 2
        carton_x = right_x + (panel_w - carton_resized.width) // 2
        img_y = y0 + 72
        image.paste(pouch_resized, (pouch_x, img_y))
        image.paste(carton_resized, (carton_x, img_y))

        # Footer stamp
        footer_y = header_h + image_area_h + 10
        draw.rectangle([0, footer_y, canvas_w, canvas_h], fill=(12, 37, 64))
        draw_text_with_shadow(draw, (margin, footer_y + 28), title, title_font, color)
        draw_text_with_shadow(draw, (margin, footer_y + 96), f"POUCH + CARTON | {mode} | {product_type} | {market_type}", body_font, (255, 255, 255))
    else:
        image = _open_base64_image(image_base64)

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
    """
    OCR-only prompt.

    IMPORTANT CHANGE:
    Do NOT send expected MFG/EXP/Line/Prefix values to the vision model.
    If expected values are included in the prompt, the model tends to "correct" what it sees
    (example: actual 220026 may be guessed/corrected as expected 220626).

    The model must only transcribe visible text. Verification is done later by Python logic.
    """

    if check_type == "both":
        prompt = """
You are an OCR transcriber for a factory lot check image.
The image may show pouch lot code, carton lot code, or both in the same photo.
Read ONLY the printed lot/batch/MFG/EXP text visible in the image.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits.

Return JSON only:
{
  "lines": ["every visible pouch/carton lot line exactly as seen"],
  "time": "HH:MM exactly as seen if visible"
}
"""
    elif check_type == "carton":
        if market_type == "TH":
            prompt = """
You are an OCR transcriber for a factory carton lot code.
Read ONLY the printed lot/batch text visible in the image.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits.

Likely Thailand carton visual pattern:
- Running No. digits
- sales code digits
- MFG date digits
- optional building number and optional suffix

Return JSON only:
{"lines":["carton lot exactly as seen"]}
"""
        else:
            prompt = """
You are an OCR transcriber for an export carton lot/batch code.
Read ONLY the printed lot/batch text visible in the image.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits.

Likely export carton visual parts may include:
- Shipping mark before running number
- Running number
- Prefix before date
- MFG date
- optional building number and suffix
- optional EXP date

Return JSON only:
{
  "lines": ["carton batch/lot exactly as seen"],
  "has_shipping_mark": true,
  "has_alpha_code": true,
  "has_mfg": true,
  "has_exp": true,
  "has_k": true,
  "abnormal_points": []
}
"""
    elif mode == "sachet":
        prompt = """
You are an OCR transcriber for sachet lot code rows.
Read ONLY the printed lot code rows visible in the image.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits or words.

Return JSON only:
{"lines":["line 1 exactly as seen","line 2 exactly as seen","line 3 exactly as seen","line 4 exactly as seen","line 5 exactly as seen","line 6 exactly as seen"]}
"""
    else:
        prompt = """
You are an OCR transcriber for a pouch / Linapack lot code.
Read ONLY the printed MFG/EXP lot text visible in the image.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits, times, line codes, MFG, or EXP.

Return JSON only:
{"lines":["first printed line exactly as seen","second printed line exactly as seen if visible"],"time":"HH:MM exactly as seen if visible"}
"""

    prompt += """

STRICT OCR / NO GUESSING MODE:
- Your job is VISUAL TRANSCRIPTION ONLY.
- Never infer from the correct pattern.
- Never infer from expected values.
- Never repair a date to look correct.
- Never normalize a date.
- Never change one digit into another because it looks more likely.
- Never add missing digits.
- Never remove extra digits.
- Never add leading zero.
- Never remove leading zero.

CRITICAL DIGIT RULES:
- Read every digit one by one from left to right.
- If the image shows 220026, return 220026 exactly. Do NOT return 220626.
- If the image shows 2200626, return 2200626 exactly. Do NOT return 220626.
- If the image shows 220626, return 220626 only when every digit is clearly visible as 2 2 0 6 2 6.
- If the middle digit is unclear between 0 and 6, return 220?26 or UNCLEAR, not 220626.
- If a digit is broken, faint, smeared, or ambiguous, use ? for that digit.

CHARACTER RULES:
- If a character looks like IR, return IR. Do not change it to XR.
- If a character looks like O, return O. Do not change it to Q.
- If only R is visible, return R. Do not change it to QR.
- Return QR only when both Q and R are clearly visible.
- If Q or R is unclear, return Q? / ?R / UNCLEAR.

WORD RULES:
- Never add missing words MFG or EXP.
- If MFG or EXP text is not clearly visible, return exactly what is visible or UNCLEAR.

TIME RULES:
- If the printed time is 25:15, return "time":"25:15" exactly. Do not correct it.
- Do not convert invalid time into a valid time.

UNCLEAR RULE:
- If confidence is not high, choose ? or UNCLEAR instead of the most likely correct value.
- The safest output for unclear text is UNCLEAR, not a guessed correction.

OUTPUT RULE:
- Return JSON only.
- Do not explain.
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



def digits_hamming_distance(a, b):
    a = str(a or "").strip()
    b = str(b or "").strip()
    if len(a) != len(b):
        return 999
    return sum(1 for x, y in zip(a, b) if x != y)


def same_date_with_one_unclear_digit(actual, expected):
    actual = str(actual or "").strip()
    expected = str(expected or "").strip()
    return (
        re.fullmatch(r"\d{6}", actual or "") is not None
        and re.fullmatch(r"\d{6}", expected or "") is not None
        and digits_hamming_distance(actual, expected) == 1
    )


def extract_best_time_from_text(text, ai_time=""):
    txt = normalize(" ".join([str(text or ""), str(ai_time or "")]))
    m = re.search(r"\b([01]\d|2[0-3]):[0-5]\d\b", txt)
    return m.group(0) if m else ""


def compare_char_by_char(actual, expected):
    """
    Compare each character position. Return (ok, diff_text).
    This is used to show exactly which character is wrong.
    """
    actual = str(actual or "").strip().upper()
    expected = str(expected or "").strip().upper()

    if actual == expected:
        return True, ""

    max_len = max(len(actual), len(expected))
    diffs = []
    for i in range(max_len):
        a = actual[i] if i < len(actual) else "∅"
        e = expected[i] if i < len(expected) else "∅"
        if a != e:
            diffs.append(f"pos {i+1}: อ่านได้ '{a}' ควรเป็น '{e}'")

    return False, "; ".join(diffs)


def parse_linapack_lot_fields(line):
    """
    Parse printed Linapack lot into separate fields:
    MFG / DDMMYY / mix_or_line / machine / time

    Examples:
      MFG 230626 22F LP4 07:45
      MFG 230626 LP4 07:45
    """
    text = normalize(line)
    tokens = text.split()

    result = {
        "mfg_word": "",
        "mfg_date": "",
        "mix_code": "",
        "machine": "",
        "time": "",
        "raw": text,
    }

    if not tokens:
        return result

    # MFG word
    for i, t in enumerate(tokens):
        if t == "MFG":
            result["mfg_word"] = "MFG"
            if i + 1 < len(tokens):
                result["mfg_date"] = tokens[i + 1]
            # after date can be mix code or machine
            if i + 2 < len(tokens):
                if re.fullmatch(r"LP\d{1,2}", tokens[i + 2]):
                    result["machine"] = tokens[i + 2]
                else:
                    result["mix_code"] = tokens[i + 2]
            if i + 3 < len(tokens):
                if re.fullmatch(r"LP\d{1,2}", tokens[i + 3]):
                    result["machine"] = tokens[i + 3]
            break

    # fallback date
    if not result["mfg_date"]:
        for t in tokens:
            if re.fullmatch(r"\d{6}|\d{5}\?|\d{4}\?\d|\d{3}\?\d{2}|\d{2}\?\d{3}|\d\?\d{4}|\?\d{5}", t):
                result["mfg_date"] = t
                break

    # machine
    if not result["machine"]:
        for t in tokens:
            if re.fullmatch(r"LP\d{1,2}", t):
                result["machine"] = t
                break

    # time
    time_match = re.search(r"\b([0-2]?\d:[0-5]\d)\b", text)
    if time_match:
        result["time"] = time_match.group(1)

    return result


def append_field_check(details, item, actual, expected, overall_ref=None, allow_blank_expected=False):
    """
    Append one field check with character-by-character comparison.
    Returns True/False.
    """
    actual = str(actual or "").strip().upper()
    expected = str(expected or "").strip().upper()

    if allow_blank_expected and not expected:
        ok = True
        expected_show = "ไม่ตรวจ"
    else:
        ok, diff = compare_char_by_char(actual, expected)
        expected_show = expected if ok else f"{expected} | {diff}"

    details.append({
        "item": item,
        "status": "PASS" if ok else "NG",
        "actual": actual if actual else "NOT FOUND",
        "expected": expected_show
    })
    return ok


def parse_pouch_lot_fields(line, exp_line=""):
    """
    Parse pouch/sachet/linapack lot fields:
    MFG / DDMMYY / machine_or_mix / time / EXP / expiry date
    """
    text = normalize(line)
    exp_text = normalize(exp_line)
    tokens = text.split()

    result = {
        "mfg_word": "",
        "mfg_date": "",
        "mix_code": "",
        "machine": "",
        "time": "",
        "exp_word": "",
        "exp_date": "",
        "raw": text,
        "exp_raw": exp_text,
    }

    # MFG
    if "MFG" in tokens:
        idx = tokens.index("MFG")
        result["mfg_word"] = "MFG"
        if idx + 1 < len(tokens):
            result["mfg_date"] = tokens[idx + 1]
        if idx + 2 < len(tokens):
            v = tokens[idx + 2]
            if re.fullmatch(r"(LP|MS)\d{1,2}", v):
                result["machine"] = v
            else:
                result["mix_code"] = v
        if idx + 3 < len(tokens):
            v = tokens[idx + 3]
            if re.fullmatch(r"(LP|MS)\d{1,2}", v):
                result["machine"] = v

    # fallback date
    if not result["mfg_date"]:
        m = re.search(r"\b\d{6}\b", text)
        if m:
            result["mfg_date"] = m.group(0)

    # fallback machine
    if not result["machine"]:
        m = re.search(r"\b(?:LP|MS)\d{1,2}\b", text)
        if m:
            result["machine"] = m.group(0)

    # time
    m = re.search(r"\b([0-2]?\d:[0-5]\d)\b", text)
    if m:
        result["time"] = m.group(1)

    # EXP line
    exp_source = exp_text if exp_text else text
    exp_tokens = exp_source.split()
    if "EXP" in exp_tokens:
        idx = exp_tokens.index("EXP")
        result["exp_word"] = "EXP"
        if idx + 1 < len(exp_tokens):
            result["exp_date"] = exp_tokens[idx + 1]
    else:
        # fallback: if EXP appears joined or date exists in exp line
        if "EXP" in exp_source:
            result["exp_word"] = "EXP"
        m = re.search(r"\b\d{6}\b", exp_source)
        if m:
            result["exp_date"] = m.group(0)

    return result


def check_time_field(actual_time):
    actual_time = str(actual_time or "").strip()
    if not actual_time:
        return False
    m = re.fullmatch(r"([0-2]?\d):([0-5]\d)", actual_time)
    if not m:
        return False
    return 0 <= int(m.group(1)) <= 23 and 0 <= int(m.group(2)) <= 59

def check_pouch_sachet(lines, product_type, market_type, expected_mfg, expected_line, expected_exp):
    """
    Field-by-field Sachet verification:
    - MFG
    - วันผลิต DDMMYY
    - เลขเครื่อง/รหัสเครื่อง
    - เวลา (ถ้ามีในภาพ)
    - EXP
    - วันหมดอายุ
    """
    details = []
    overall = True
    skip_exp = no_exp_required(product_type, market_type)
    lines = [normalize(x) for x in lines]

    # Sachet usually has 6 lanes/rows
    for i in range(1, 7):
        actual_line = lines[i - 1] if i <= len(lines) else ""
        fields = parse_pouch_lot_fields(actual_line)

        expected_machine = str(expected_line or "").strip().upper()
        # If sachet expected_line is like MS11, row may be MS11 + lane no. in the same line.
        # Keep machine check as prefix-compatible only for lane number at the end.
        machine_actual = fields.get("machine", "")

        row_ok = True

        checks = []
        checks.append(("แถว %s - MFG" % i, fields.get("mfg_word"), "MFG"))
        checks.append(("แถว %s - วันผลิต" % i, fields.get("mfg_date"), expected_mfg))
        checks.append(("แถว %s - เลขเครื่อง" % i, machine_actual, expected_machine))

        # Lane number check
        lane_actual = str(i) if re.search(rf"\b{i}\b", actual_line) else ""
        checks.append(("แถว %s - เลขแถว" % i, lane_actual, str(i)))

        for item, actual, expected in checks:
            ok = append_field_check(details, item, actual, expected)
            if not ok:
                row_ok = False
                overall = False

        # เวลา: ถ้าระบบอ่านเวลาได้ ให้ตรวจว่า valid; ถ้าไม่มี ไม่บังคับสำหรับ Sachet
        actual_time = fields.get("time")
        if actual_time:
            time_ok = check_time_field(actual_time)
            if not time_ok:
                overall = False
            details.append({
                "item": "แถว %s - เวลา" % i,
                "status": "PASS" if time_ok else "NG",
                "actual": actual_time,
                "expected": "เวลา valid 00:00-23:59"
            })

        # EXP / วันหมดอายุ
        if skip_exp:
            exp_ok = "EXP" not in actual_line
            if not exp_ok:
                overall = False
            details.append({
                "item": "แถว %s - EXP" % i,
                "status": "PASS" if exp_ok else "NG",
                "actual": "พบ EXP" if not exp_ok else "ไม่ต้องมี EXP",
                "expected": "ไม่ควรมี EXP"
            })
        else:
            exp_word_ok = append_field_check(details, "แถว %s - EXP" % i, fields.get("exp_word"), "EXP")
            exp_date_ok = append_field_check(details, "แถว %s - วันหมดอายุ" % i, fields.get("exp_date"), expected_exp)
            if not exp_word_ok or not exp_date_ok:
                overall = False

    return overall, details

def is_valid_time_hhmm(value):
    """
    Valid time must be 00:00 - 23:59 only.
    24:00, 25:15, 29:59 are invalid.
    """
    value = str(value or "").strip()
    return re.fullmatch(r"([01][0-9]|2[0-3]):[0-5][0-9]", value) is not None


def extract_time(text):
    match = re.search(r"\b(([01][0-9]|2[0-3]):[0-5][0-9])\b", text)
    return match.group(1) if match else ""


def check_pouch_linapack(lines, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code, ai_time=""):
    """
    Linapack field-by-field verification with fixed master rules.
    """
    details = []
    overall = True

    product_type = str(product_type or "").upper()
    market_type = str(market_type or "").upper()

    lines = [normalize(x) for x in lines]
    all_text = " ".join(lines)

    mfg_line = lines[0] if len(lines) > 0 else ""
    exp_line = lines[1] if len(lines) > 1 else ""

    fields = parse_pouch_lot_fields(mfg_line, exp_line)

    require_mix = linapack_requires_mix(product_type, market_type)
    require_exp = linapack_requires_exp(product_type, market_type)

    expected_exp_calc = expected_linapack_exp(product_type, market_type, expected_mfg)
    if expected_exp_calc:
        expected_exp = expected_exp_calc
        # LINAPACK_RULE_EXPECTED_EXP_OVERRIDE
        try:
            if str(mode).lower() == "linapack":
                expected_exp = expected_linapack_exp(product_type, market_type, expected_mfg)
        except Exception:
            pass

    if not append_field_check(details, "MFG", fields.get("mfg_word"), "MFG"):
        overall = False

    if not append_field_check(details, "วันผลิต", fields.get("mfg_date"), expected_mfg):
        overall = False

    if require_mix:
        if not append_field_check(details, "วันผสม", fields.get("mix_code"), mix_code):
            overall = False
    else:
        actual_mix = str(fields.get("mix_code") or "").strip().upper()
        if actual_mix:
            details.append({
                "item": "วันผสม",
                "status": "NG",
                "actual": actual_mix,
                "expected": "ไม่ต้องมีวันผสม"
            })
            overall = False
        else:
            details.append({
                "item": "วันผสม",
                "status": "PASS",
                "actual": "ไม่ต้องมี",
                "expected": "ไม่ตรวจ"
            })

    if not append_field_check(details, "เลขเครื่อง", fields.get("machine"), expected_line):
        overall = False

    actual_time = fields.get("time") or extract_best_time_from_text(all_text, ai_time)
    time_ok = check_time_field(actual_time)
    if not time_ok:
        overall = False
    details.append({
        "item": "เวลา",
        "status": "PASS" if time_ok else "NG",
        "actual": actual_time if actual_time else "NOT FOUND",
        "expected": "เวลา valid 00:00-23:59 เช่น 07:45"
    })

    has_exp = "EXP" in all_text
    if require_exp:
        if not append_field_check(details, "EXP", fields.get("exp_word"), "EXP"):
            overall = False
        if not append_field_check(details, "วันหมดอายุ", fields.get("exp_date"), expected_exp):
            overall = False
    else:
        exp_ok = not has_exp
        details.append({
            "item": "EXP",
            "status": "PASS" if exp_ok else "NG",
            "actual": "พบ EXP" if has_exp else "ไม่ต้องมี EXP",
            "expected": "ไม่ควรมี EXP"
        })
        details.append({
            "item": "วันหมดอายุ",
            "status": "PASS" if exp_ok else "NG",
            "actual": fields.get("exp_date") if has_exp else "ไม่ต้องมี",
            "expected": "ไม่ตรวจ"
        })
        if not exp_ok:
            overall = False

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

    Rules:
    - If building_no is blank: do not check building/suffix.
    - If building_suffix is selected, exact "building suffix" is required, e.g. "3 QR".
    - If building_suffix is blank, only the building number is allowed.
      Example expected "3":
        "3"    = PASS
        "3 QR" = NG because QR is extra
        "3 N"  = NG because N is extra
    """
    building_no = str(building_no or "").strip().upper()
    building_suffix = str(building_suffix or "").strip().upper()
    text = normalize(all_text)

    if not building_no:
        return True, "ไม่ตรวจเลขอาคาร"

    expected = f"{building_no} {building_suffix}".strip().upper()

    if "UNCLEAR" in text or "UNKNOWN" in text or "?" in text:
        return False, expected

    # Tokenize only visible building field / lot text
    tokens = lot_tokens(text)

    # Find building number token
    building_indexes = [i for i, t in enumerate(tokens) if t == building_no]
    if not building_indexes:
        return False, expected

    # Use the last building occurrence because building is usually at the end of lot code
    idx = building_indexes[-1]

    if building_suffix:
        # Must have exact suffix after building number
        if idx + 1 >= len(tokens):
            return False, expected

        actual_suffix = tokens[idx + 1]
        ok = actual_suffix == building_suffix

        # Safety for QR: must be QR exactly, not Q/R/UNCLEAR
        if building_suffix == "QR" and actual_suffix != "QR":
            return False, expected

        return ok, expected

    # No suffix expected:
    # If anything alphabetic appears immediately after building number, it is extra and must be NG.
    if idx + 1 < len(tokens):
        next_token = tokens[idx + 1]
        if re.fullmatch(r"[A-Z]+", next_token):
            return False, building_no

    return True, building_no


def extract_carton_actual_fields(all_text, expected_mfg="", carton_alpha_code="", shipping_mark="", building_no="", building_suffix=""):
    """
    Extract only the actual value for each carton field from the OCR/GPT text.
    This prevents the UI from showing the whole lot line in every row.
    Example: XR 00001 XR 130626 3 QR
      shipping_mark = XR
      running_no = 00001
      prefix = XR
      mfg = 130626
      building_suffix = 3 QR
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

    # Running No. = first 4-5 digit token. MFG date is 6 digits, so it is ignored here.
    run_index = None
    for i, token in enumerate(tokens):
        if re.fullmatch(r"\d{4,5}", token):
            result["running_no"] = token
            run_index = i
            break

    # Shipping Mark = token before Running No.
    if run_index is not None and run_index > 0:
        result["shipping_mark"] = tokens[run_index - 1]

    # MFG date = expected MFG if found, otherwise first 6 digit token
    mfg_index = None
    for i, token in enumerate(tokens):
        if expected_mfg and token == expected_mfg:
            result["mfg"] = token
            mfg_index = i
            break

    if mfg_index is None:
        for i, token in enumerate(tokens):
            if re.fullmatch(r"\d{6}", token):
                result["mfg"] = token
                mfg_index = i
                break

    # Prefix = token before MFG date
    if mfg_index is not None and mfg_index > 0:
        result["prefix"] = tokens[mfg_index - 1]

    # Building + suffix = token(s) after MFG date.
    # If there is an extra suffix such as QR, show it so the user sees why it is NG.
    if mfg_index is not None and mfg_index + 1 < len(tokens):
        building = tokens[mfg_index + 1]
        if mfg_index + 2 < len(tokens):
            next_token = tokens[mfg_index + 2]
            # Show suffix if alphabetic, e.g. 3 QR or 3 N
            if re.fullmatch(r"[A-Z]+", next_token):
                result["building_suffix"] = f"{building} {next_token}"
            else:
                result["building_suffix"] = building
        else:
            result["building_suffix"] = building

    # EXP = token after EXP word if present
    for i, token in enumerate(tokens):
        if token == "EXP" and i + 1 < len(tokens):
            result["exp"] = tokens[i + 1]
            break

    # OL special pattern may be OL130626 etc.
    if expected_prefix in ["OL", "OD"]:
        compact = re.sub(r"[^A-Z0-9]", "", text.upper())
        m = re.search(r"OL(\d{6})", compact)
        if m:
            result["prefix"] = "OL"
            result["mfg"] = m.group(1)

    return result



def format_char_diff(actual, expected):
    """
    แสดงตำแหน่งที่ผิดแบบอ่านง่าย เช่น pos 3: อ่านได้ 0 ควรเป็น 6
    """
    ok, diff = compare_char_by_char(actual, expected)
    return ok, diff


def strict_field_status(actual, expected):
    actual = str(actual or "").strip().upper()
    expected = str(expected or "").strip().upper()
    ok, diff = format_char_diff(actual, expected)
    expected_show = expected if ok else f"{expected} | {diff}"
    return ok, actual if actual else "NOT FOUND", expected_show


def append_carton_field_check(details, item, actual, expected):
    ok, actual_show, expected_show = strict_field_status(actual, expected)
    details.append({
        "item": item,
        "status": "PASS" if ok else "NG",
        "actual": actual_show,
        "expected": expected_show
    })
    return ok

def check_carton(lines, market_type, expected_mfg, expected_exp, building_no, building_suffix, shipping_mark, carton_alpha_code, ai_json):
    """
    Carton verification แบบแยก field และเทียบทีละตัวอักษร
    เพื่อแสดงชัดเจนว่าตัวเลข/ตัวอักษรตำแหน่งไหนผิด
    """
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

    # ----------------------------
    # CARTON TH
    # รูปแบบ: 00045 00 220626 5 หรือ 00045 00 220626 5 QR
    # ----------------------------
    if market_type == "TH":
        run_no, sales_code, mfg_code, building_code = parse_th_carton_fields(actual)

        # กรณีมี suffix ต่อท้ายเลขอาคาร เช่น 5 QR ให้ดึงมาทั้งก้อน ไม่ใช่แค่ 5
        parts = normalize(actual).split()
        if len(parts) >= 5:
            building_visible = " ".join(parts[3:5])
        elif len(parts) >= 4:
            building_visible = parts[3]
        else:
            building_visible = building_code

        if building_no:
            expected_building_full = f"{building_no} {building_suffix}".strip().upper()
        else:
            expected_building_full = ""

        # Running No.
        ok = append_carton_field_check(details, "Running No. 5 digits", run_no, "00000" if not run_no else run_no)
        # ต้องเป็นตัวเลข 5 หลักด้วย
        if not re.fullmatch(r"\d{5}", run_no or ""):
            overall = False
            details[-1]["status"] = "NG"
            details[-1]["expected"] = "ตัวเลข 5 หลัก เช่น 00045 | ความยาว/รูปแบบผิด"
        elif not ok:
            overall = False

        # Thailand sales code
        if not append_carton_field_check(details, "Thailand sales code", sales_code, "00"):
            overall = False

        # MFG date แสดงตำแหน่งที่ผิด เช่น 2200626 vs 220626
        if not append_carton_field_check(details, "MFG date", mfg_code, expected_mfg):
            overall = False

        # Building No. + Suffix
        if building_no:
            if not append_carton_field_check(details, "Building No. + Suffix", building_visible, expected_building_full):
                overall = False
        else:
            # ถ้าเลือกไม่มีเลขอาคาร แต่ OCR อ่านเจอค่าหลังวันที่ ถือว่า NG
            no_building_ok = not building_visible
            details.append({
                "item": "Building No. + Suffix",
                "status": "PASS" if no_building_ok else "NG",
                "actual": building_visible if building_visible else "ไม่มี",
                "expected": "ไม่มีเลขอาคาร"
            })
            if not no_building_ok:
                overall = False

        return overall, details

    # ----------------------------
    # CARTON EXPORT / LAOS
    # แยกตรวจ: Shipping Mark / Running / Prefix / MFG / Building+Suffix / EXP
    # ----------------------------
    expected_building_full = f"{building_no} {building_suffix}".strip().upper() if building_no else ""

    # Shipping Mark before Running No.
    if shipping_mark:
        if not append_carton_field_check(details, "Shipping Mark before Running No.", field_actual.get("shipping_mark"), shipping_mark):
            overall = False
    else:
        details.append({
            "item": "Shipping Mark before Running No.",
            "status": "PASS",
            "actual": "ไม่ต้องมี",
            "expected": "ไม่ตรวจ"
        })

    # Running No.
    actual_run_no, run_format_ok = extract_export_running_no(all_text, carton_alpha_code)
    expected_run_display = "ตัวเลข 5 หลัก"
    if carton_alpha_code in ["OL", "OD"]:
        details.append({
            "item": "Running No.",
            "status": "PASS",
            "actual": "OL/OD ไม่ต้องมี Running No.",
            "expected": "ไม่ตรวจ"
        })
    else:
        # ถ้ามี actual ให้ตรวจ format และแสดงค่า actual
        run_actual_show = actual_run_no or field_actual.get("running_no") or ""
        run_ok = re.fullmatch(r"\d{5}", run_actual_show or "") is not None
        details.append({
            "item": "Running No.",
            "status": "PASS" if run_ok else "NG",
            "actual": run_actual_show if run_actual_show else "NOT FOUND",
            "expected": expected_run_display if run_ok else expected_run_display + " | ความยาว/รูปแบบผิด"
        })
        if not run_ok:
            overall = False

    # Prefix before MFG date
    if carton_alpha_code:
        if not append_carton_field_check(details, "Prefix before MFG date", field_actual.get("prefix"), carton_alpha_code):
            overall = False
    else:
        details.append({
            "item": "Prefix before MFG date",
            "status": "PASS",
            "actual": "ไม่บังคับ",
            "expected": "ไม่ตรวจ"
        })

    # MFG Date
    if not append_carton_field_check(details, "MFG date", field_actual.get("mfg"), expected_mfg):
        overall = False

    # Building No. + Suffix
    if building_no:
        if not append_carton_field_check(details, "Building No. + Suffix", field_actual.get("building_suffix"), expected_building_full):
            overall = False
    else:
        details.append({
            "item": "Building No. + Suffix",
            "status": "PASS",
            "actual": "ไม่ตรวจเลขอาคาร",
            "expected": "ไม่ตรวจ"
        })

    # EXP
    if expected_exp:
        if not append_carton_field_check(details, "EXP", field_actual.get("exp"), expected_exp):
            overall = False
    else:
        # ถ้าไม่ต้องมี EXP แต่ OCR อ่านเจอ EXP date ต้อง NG
        actual_exp = field_actual.get("exp")
        exp_ok = not actual_exp
        details.append({
            "item": "EXP",
            "status": "PASS" if exp_ok else "NG",
            "actual": actual_exp if actual_exp else "ไม่ต้องมี EXP",
            "expected": "ไม่ต้องมี EXP" if exp_ok else "ไม่ควรมี EXP"
        })
        if not exp_ok:
            overall = False

    return overall, details

def index():
    return HTML


@app.route("/stamped/<filename>")
def stamped_file(filename):
    return send_from_directory(STAMP_DIR, filename)




@app.route("/")
def index():
    return HTML



@app.route("/health")
def health():
    return jsonify({"status": "ok"})

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
        # EPW LAOS FORCE EXP 3 YEARS: MFG 230626 -> EXP 230629
        try:
            if str(product_type).upper() == "EPW" and str(market_type).upper() == "LAOS":
                expected_exp = exp_date_plus_years(expected_mfg, 3)
        except Exception:
            pass
        mix_code = data.get("mixCode", "").strip().upper()
        pouch_image_data = data.get("pouchImage", "")
        carton_image_data = data.get("cartonImage", "")
        image_data = data.get("image", "")  # fallback for old clients

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

        if check_type == "both":
            if not pouch_image_data or not carton_image_data:
                return jsonify({"error": "กรุณาถ่าย/อัปโหลดรูปซองและรูปกล่องให้ครบ"}), 400
        elif not image_data:
            return jsonify({"error": "กรุณาอัปโหลดรูปหรือถ่ายรูปก่อน"}), 400

        if not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY"}), 500

        # EXP is locked by system. Do not trust editable/browser-submitted value.
        auto_exp = calculate_exp(product_type, market_type, expected_mfg)
        expected_exp = auto_exp if auto_exp else ""

        skip_exp = no_exp_required(product_type, market_type)

        if check_type in ["pouch", "both"] and not skip_exp and not expected_exp:
            return jsonify({"error": "กรุณากรอก EXP หรือเลือกประเภทงานที่ไม่ต้องมี EXP"}), 400

        if check_type in ["carton", "both"]:
            if building_no and building_no not in ["1", "2", "3", "4", "5", "6"]:
                return jsonify({"error": "เลขอาคารต้องเป็น 1-6"}), 400
            if building_suffix and not re.fullmatch(r"[A-Z0-9]{1,5}", building_suffix):
                return jsonify({"error": "Suffix ต้องเป็นตัวอักษร/ตัวเลข 1-5 ตัว เช่น N หรือ QR"}), 400

        if check_type == "both":
            pouch_base64 = pouch_image_data.split(",", 1)[1] if "," in pouch_image_data else pouch_image_data
            carton_base64 = carton_image_data.split(",", 1)[1] if "," in carton_image_data else carton_image_data

            raw_pouch_ai = read_lot_with_ai(
                pouch_base64, "pouch", mode, product_type, market_type, expected_mfg, expected_line,
                expected_exp, mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code
            )
            pouch_json = json.loads(clean_json_text(raw_pouch_ai))
            pouch_lines = pouch_json.get("lines", [])

            carton_market_type = "EXPORT" if market_type == "LAOS" else market_type
            raw_carton_ai = read_lot_with_ai(
                carton_base64, "carton", mode, product_type, carton_market_type, expected_mfg, expected_line,
                expected_exp, mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code
            )
            carton_json = json.loads(clean_json_text(raw_carton_ai))
            carton_lines = carton_json.get("lines", [])

            if mode == "sachet":
                pouch_overall, pouch_details = check_pouch_sachet(
                    pouch_lines, product_type, market_type, expected_mfg, expected_line, expected_exp
                )
                mode_name = "Sachet + Carton"
            else:
                ai_time = pouch_json.get("time", "")
                pouch_overall, pouch_details = check_pouch_linapack(
                    pouch_lines, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code, ai_time
                )
                mode_name = "Linapack + Carton"

            carton_overall, carton_details = check_carton(
                carton_lines, carton_market_type, expected_mfg, expected_exp, building_no, building_suffix,
                shipping_mark, carton_alpha_code, carton_json
            )

            details = []
            for d in pouch_details:
                d = dict(d)
                d["item"] = "ซอง - " + str(d.get("item", ""))
                details.append(d)
            for d in carton_details:
                d = dict(d)
                d["item"] = "กล่อง - " + str(d.get("item", ""))
                details.append(d)

            overall = bool(pouch_overall and carton_overall)
            check_type_name = "POUCH + CARTON"
            lines = {"pouch": pouch_lines, "carton": carton_lines}
            image_data = pouch_image_data
        else:
            image_base64 = image_data.split(",", 1)[1] if "," in image_data else image_data
            raw_ai = read_lot_with_ai(
                image_base64, check_type, mode, product_type, market_type, expected_mfg, expected_line,
                expected_exp, mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code
            )
            result_json = json.loads(clean_json_text(raw_ai))
            lines = result_json.get("lines", [])

        if check_type != "both" and check_type == "carton":
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
        elif check_type != "both" and mode == "sachet":
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
        elif check_type != "both":
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
            checked_time,
            carton_image_data if check_type == "both" else None
        )

        if mode == "sachet":
            expected_pouch_lot = f"MFG {expected_mfg} {expected_line} 1" + (f" EXP {expected_exp}" if expected_exp else "")
        else:
            line1 = f"MFG {expected_mfg}"
            if mix_code:
                line1 += f" {mix_code}"
            line1 += f" {expected_line} เวลา"
            expected_pouch_lot = line1 + (f" / EXP {expected_exp}" if expected_exp else "")

        if market_type == "TH":
            expected_carton_lot = f"00001 00 {expected_mfg} {building_no}{(' ' + building_suffix) if building_suffix else ''}".strip()
        else:
            expected_carton_lot = f"00001 {carton_alpha_code} {expected_mfg}".strip()

        return jsonify({
            "summary": summary,
            "checkType": check_type_name,
            "mode": mode_name,
            "productType": product_type,
            "marketType": market_type,
            "expectedExp": expected_exp if expected_exp else "ไม่ใช้ EXP",
            "expectedPouchLot": expected_pouch_lot,
            "expectedCartonLot": expected_carton_lot,
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
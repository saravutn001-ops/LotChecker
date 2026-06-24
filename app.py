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
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
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


/* ===== Requested compact header/carton cleanup ===== */
.config-grid.grid-4 { grid-template-columns:repeat(4, minmax(0,1fr)) !important; }
.config-grid.grid-9 { grid-template-columns:repeat(9, minmax(0,1fr)) !important; }
#pouchSection { display:none !important; }
.hidden-field { display:none !important; }
#pouchHeader.section-card { grid-column:1 / -1 !important; }
#pouchHeader .section-title { margin-bottom:10px !important; }
@media (max-width:1200px) { .config-grid.grid-9 { grid-template-columns:repeat(5, minmax(0,1fr)) !important; } }
@media (max-width:800px) { .config-grid.grid-4, .config-grid.grid-9 { grid-template-columns:1fr !important; } }



/* ===== FINAL CLEAN LEFT-ALIGNED LAYOUT FIX ===== */
#page1 {
    display:flex !important;
    flex-direction:column !important;
    gap:10px !important;
    align-items:stretch !important;
}
.compact-mode-info { display:none !important; }
#pouchHeader.section-card,
#cartonSection.section-card {
    display:block !important;
    width:100% !important;
    grid-column:auto !important;
}
#pouchHeader .config-grid,
#cartonSection .config-grid {
    width:100% !important;
    justify-content:start !important;
    align-items:end !important;
    gap:8px 12px !important;
}
#pouchHeader .config-grid {
    grid-template-columns:repeat(var(--lot-cols, 6), minmax(120px, 1fr)) !important;
}
#cartonTHBox.config-grid,
#cartonExportBox.config-grid {
    grid-template-columns:repeat(4, minmax(170px, 1fr)) !important;
}
#cartonTHBox.config-grid:not(.hidden-market),
#cartonExportBox.config-grid:not(.hidden-market) {
    display:grid !important;
}
#cartonTHBox.hidden-market,
#cartonExportBox.hidden-market {
    display:none !important;
}
#pouchHeader .config-grid label,
#cartonSection .config-grid label {
    font-size:12px !important;
    line-height:1.35 !important;
    margin:0 0 2px 0 !important;
    white-space:normal !important;
    overflow:visible !important;
    text-overflow:clip !important;
}
#pouchHeader .config-grid input,
#pouchHeader .config-grid select,
#cartonSection .config-grid input,
#cartonSection .config-grid select {
    height:38px !important;
    font-size:13px !important;
    padding:7px 10px !important;
    margin:0 !important;
}
#autoExpInfo, #linkedLotInfo {
    width:100% !important;
    line-height:1.55 !important;
    padding:9px 12px !important;
}
#cartonTHBox .small,
#cartonExportBox .small {
    display:none !important;
}
@media (max-width:1200px) {
    #pouchHeader .config-grid { grid-template-columns:repeat(3, minmax(0, 1fr)) !important; }
    #cartonTHBox.config-grid, #cartonExportBox.config-grid { grid-template-columns:repeat(2, minmax(0, 1fr)) !important; }
}
@media (max-width:720px) {
    #pouchHeader .config-grid,
    #cartonTHBox.config-grid,
    #cartonExportBox.config-grid { grid-template-columns:1fr !important; }
}


/* ===== Carton market visibility fix: TH shows only 00 prefix, Export shows selectable prefix ===== */
#cartonSection .hidden-market { display:none !important; }
#cartonTHBox:not(.hidden-market),
#cartonExportBox:not(.hidden-market) {
    display:grid !important;
    grid-template-columns:repeat(4, minmax(170px, 1fr)) !important;
}
#cartonSection { gap:8px !important; }
#cartonTHBox, #cartonExportBox { margin-top:0 !important; }

.camera-action-row {
    display:grid;
    grid-template-columns:repeat(3, minmax(0, 1fr));
    gap:8px;
}
.camera-action-row button {
    margin-top:0 !important;
}
#capturePouchBtn, #captureCartonBtn {
    background:linear-gradient(135deg, #16a34a, #15803d) !important;
}



/* ===== Modern result page UI ===== */
#page3.result-dashboard {
    background:#f8fafc !important;
    border:1px solid var(--border) !important;
    border-radius:16px !important;
    padding:12px !important;
}
#result { margin:0 !important; }
.result-hero {
    display:grid;
    grid-template-columns: 1.1fr 1fr;
    gap:12px;
    align-items:stretch;
    margin-bottom:12px;
}
.result-status-card,
.result-meta-card,
.result-card {
    background:#ffffff;
    border:1px solid #dbe4ef;
    border-radius:16px;
    padding:14px;
    box-shadow:0 8px 22px rgba(15,23,42,.06);
}
.result-status-card.pass-card { border-left:8px solid #16a34a; }
.result-status-card.ng-card { border-left:8px solid #dc2626; }
.result-title {
    font-size:36px;
    font-weight:900;
    line-height:1;
    margin:0 0 6px;
    letter-spacing:.3px;
}
.result-title.pass-text { color:#16a34a; }
.result-title.ng-text { color:#dc2626; }
.result-subtitle {
    font-size:15px;
    color:#475569;
    margin:0;
    font-weight:700;
}
.result-meta-grid {
    display:grid;
    grid-template-columns:repeat(2, minmax(0,1fr));
    gap:8px;
}
.meta-item {
    background:#f1f5f9;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:8px 10px;
}
.meta-label {
    font-size:11px;
    color:#64748b;
    font-weight:800;
    margin-bottom:4px;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}
.meta-value {
    font-size:14px;
    color:#0f172a;
    font-weight:800;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}
.result-actions {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin:10px 0 0;
}
.result-actions a {
    margin:0 !important;
}
.result-section-title {
    font-size:16px;
    font-weight:900;
    color:#0f172a;
    margin:0 0 10px;
}
.result-main-grid {
    display:grid;
    grid-template-columns: minmax(620px, 1.65fr) minmax(360px, .85fr);
    gap:14px;
    align-items:start;
}
.result-image-card img {
    width:100%;
    height:auto !important;
    max-height:720px !important;
    object-fit:contain;
    background:#0f172a;
    border-radius:14px;
    margin:0 !important;
    display:block;
}
.result-table table { margin-top:0 !important; }
.result-table th,
.result-table td { font-size:13px !important; padding:8px 9px !important; }
.result-ok-box {
    background:#ecfdf5;
    border:1px solid #bbf7d0;
    color:#047857;
    font-weight:900;
    padding:14px;
    border-radius:12px;
    text-align:center;
}
.result-ng-note {
    background:#fff7ed;
    border:1px solid #fed7aa;
    color:#9a3412;
    font-size:12px;
    font-weight:800;
    padding:8px 10px;
    border-radius:10px;
    margin-bottom:8px;
}
.result-json {
    margin-top:12px;
}
.result-json details {
    background:#fff;
    border:1px solid #dbe4ef;
    border-radius:14px;
    padding:10px;
}
.result-json summary {
    cursor:pointer;
    font-weight:900;
    color:#0f172a;
}
.result-json pre {
    max-height:260px !important;
    margin-top:10px;
}
@media (max-width:1000px) {
    .result-hero, .result-main-grid { grid-template-columns:1fr; }
}
@media (max-width:640px) {
    .result-meta-grid, .result-actions { grid-template-columns:1fr; }
    .result-title { font-size:30px; }
}



/* ===== Result popup modal override ===== */
.result-popup-overlay {
    position:fixed;
    inset:0;
    background:rgba(15,23,42,.72);
    z-index:9999;
    display:none;
    align-items:center;
    justify-content:center;
    padding:18px;
}
.result-popup-overlay.show { display:flex; }
.result-popup {
    width:min(1180px, 96vw);
    max-height:94vh;
    overflow:auto;
    background:#ffffff;
    border-radius:24px;
    box-shadow:0 28px 80px rgba(0,0,0,.35);
    border:1px solid #dbe4ef;
}
.result-popup-header {
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:14px;
    padding:18px 22px;
    background:#071f38;
    color:white;
    position:sticky;
    top:0;
    z-index:1;
}
.result-popup-title {
    font-size:40px;
    font-weight:900;
    line-height:1;
}
.result-popup-subtitle {
    font-size:16px;
    margin-top:6px;
    color:#dbeafe;
    font-weight:700;
}
.result-popup-close {
    width:auto !important;
    min-width:44px;
    padding:8px 12px !important;
    margin:0 !important;
    background:#111827 !important;
    color:white !important;
    border:1px solid rgba(255,255,255,.25) !important;
    border-radius:12px !important;
    font-size:22px !important;
    box-shadow:none !important;
}
.result-popup-body { padding:18px 22px 22px; }
.result-popup-meta {
    display:grid;
    grid-template-columns:repeat(4, minmax(0,1fr));
    gap:10px;
    margin-bottom:14px;
}
.result-popup-image-wrap {
    display:flex;
    justify-content:center;
    align-items:center;
    background:#f8fafc;
    border:1px solid #dbe4ef;
    border-radius:18px;
    padding:12px;
}
.result-popup-image-wrap img {
    width:auto !important;
    max-width:100% !important;
    max-height:68vh !important;
    object-fit:contain !important;
    margin:0 !important;
    border-radius:14px !important;
    background:#0f172a !important;
}
.result-popup-bottom {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:12px;
    margin-top:14px;
    align-items:start;
}
.result-popup-lot-box {
    background:#eef6ff;
    border:1px solid #bfdbfe;
    border-radius:14px;
    padding:12px 14px;
}
.result-popup-lot-title {
    font-size:12px;
    color:#475569;
    font-weight:800;
    margin-bottom:4px;
}
.result-popup-lot-value {
    font-size:18px;
    color:#0f172a;
    font-weight:900;
    word-break:break-word;
}
.result-popup-ng-box {
    grid-column:1 / -1;
    background:#fff7ed;
    border:1px solid #fed7aa;
    border-radius:14px;
    padding:12px;
}
.result-popup-ok-box {
    grid-column:1 / -1;
    background:#ecfdf5;
    border:1px solid #bbf7d0;
    color:#047857;
    font-size:20px;
    font-weight:900;
    padding:16px;
    border-radius:14px;
    text-align:center;
}
.result-popup-actions {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:14px;
}
.result-popup-actions a { margin:0 !important; }

.result-popup-actions button.download {
    border:0 !important;
    cursor:pointer;
    width:100% !important;
    text-align:center !important;
}

.result-popup-ng-box table { margin-top:8px !important; }
.result-popup-ng-box th, .result-popup-ng-box td { font-size:13px !important; padding:8px 9px !important; }
@media (max-width:900px) {
    .result-popup-meta, .result-popup-bottom, .result-popup-actions { grid-template-columns:1fr; }
    .result-popup-title { font-size:32px; }
    .result-popup-image-wrap img { max-height:58vh !important; }
}



/* ===== Larger camera preview when camera is active ===== */
#page2.photo-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(360px, .85fr) !important;
}
#page2.photo-grid .camera-card {
    transition: all .18s ease-in-out;
}
#page2.photo-grid .camera-card.camera-active {
    grid-column:1 / -1 !important;
    display:grid !important;
    grid-template-columns: 1fr 1fr;
    gap:10px 14px;
    align-items:start;
}
#page2.photo-grid .camera-card.camera-active h3,
#page2.photo-grid .camera-card.camera-active .camera-action-row,
#page2.photo-grid .camera-card.camera-active #openCameraBtn {
    grid-column:1 / -1;
}
#page2.photo-grid .camera-card.camera-active #video {
    grid-column:1 / -1;
    width:100% !important;
    height:min(62vh, 620px) !important;
    max-height:620px !important;
    object-fit:contain !important;
    border-radius:16px !important;
    background:#07111f !important;
    border:2px solid #0b63ce !important;
}
#page2.photo-grid .camera-card.camera-active .camera-action-row {
    max-width:720px;
    justify-self:center;
    width:100%;
}
@media (max-width:1100px) {
    #page2.photo-grid { grid-template-columns:1fr 1fr !important; }
    #page2.photo-grid .camera-card.camera-active #video { height:min(58vh, 560px) !important; }
}
@media (max-width:720px) {
    #page2.photo-grid .camera-card.camera-active { grid-template-columns:1fr !important; }
    #page2.photo-grid .camera-card.camera-active #video { height:70vh !important; }
}



/* ===== Full screen camera modal ===== */
.camera-card #openCameraBtn {
    min-height:44px !important;
    font-size:16px !important;
}
.camera-overlay {
    position:fixed;
    inset:0;
    z-index:99999;
    background:#000;
    display:none;
    flex-direction:column;
}
.camera-live-wrap {
    position:relative;
    flex:1;
    width:100vw;
    height:calc(100vh - 88px);
    background:#000;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
}
.camera-overlay #video {
    width:100vw !important;
    height:calc(100vh - 88px) !important;
    max-height:none !important;
    object-fit:contain !important;
    background:#000 !important;
    border:0 !important;
    border-radius:0 !important;
    margin:0 !important;
}
.scan-guide {
    position:absolute;
    left:20%;
    top:40%;
    width:60%;
    height:20%;
    border:4px solid rgba(34,197,94,.95);
    border-radius:14px;
    box-shadow:0 0 0 9999px rgba(0,0,0,.08);
    pointer-events:none;
}
.camera-toolbar {
    height:88px;
    width:100%;
    background:#111827;
    border-top:1px solid rgba(255,255,255,.16);
    display:grid;
    grid-template-columns:repeat(3, minmax(0, 260px));
    gap:14px;
    align-items:center;
    justify-content:center;
    padding:12px 16px;
}
.camera-toolbar button {
    margin:0 !important;
    height:58px !important;
    font-size:20px !important;
    border-radius:16px !important;
}
@media (max-width:720px) {
    .camera-live-wrap, .camera-overlay #video { height:calc(100vh - 76px) !important; }
    .camera-toolbar { height:76px; grid-template-columns:1fr 1fr 1fr; gap:8px; padding:8px; }
    .camera-toolbar button { height:54px !important; font-size:15px !important; padding:8px !important; }
    .scan-guide { left:12%; width:76%; height:22%; }
}

/* ===== Capture success toast ===== */
.capture-toast {
    position:fixed;
    top:18px;
    left:50%;
    transform:translateX(-50%) translateY(-10px);
    min-width:260px;
    max-width:92vw;
    padding:13px 22px;
    border-radius:14px;
    background:#16a34a;
    color:#ffffff;
    font-weight:800;
    font-size:16px;
    text-align:center;
    z-index:1000000;
    box-shadow:0 12px 30px rgba(0,0,0,.25);
    opacity:0;
    pointer-events:none;
    transition:opacity .18s ease, transform .18s ease;
}
.capture-toast.show {
    opacity:1;
    transform:translateX(-50%) translateY(0);
}
.capture-toast.info { background:#2563eb; }
.capture-toast.error { background:#dc2626; }
.capture-time {
    display:block;
    margin-top:6px;
    color:#64748b;
    font-size:12px;
    font-weight:700;
}


/* ===== Mobile app UI + PASS/NG status color override ===== */
.result-popup-header.popup-pass {
    background:linear-gradient(135deg, #15803d, #16a34a) !important;
}
.result-popup-header.popup-ng {
    background:linear-gradient(135deg, #991b1b, #dc2626) !important;
}
.result-popup-header .result-popup-title,
.result-popup-header .result-popup-subtitle {
    color:#ffffff !important;
}
.result-popup-ng-box {
    background:#fee2e2 !important;
    border:1px solid #fca5a5 !important;
    color:#7f1d1d !important;
}
.result-popup-ng-box .result-section-title,
.result-popup-ng-box th,
.result-popup-ng-box td {
    color:#7f1d1d !important;
}
.result-popup-ok-box {
    background:#dcfce7 !important;
    border:1px solid #86efac !important;
    color:#166534 !important;
}
.result-status-card.pass-card {
    background:#f0fdf4 !important;
    border-color:#86efac !important;
}
.result-status-card.ng-card {
    background:#fef2f2 !important;
    border-color:#fca5a5 !important;
}

@media (max-width: 768px) {
    html, body {
        width:100%;
        overflow-x:hidden;
        background:#eef3f8 !important;
    }
    body { padding:6px !important; }
    .box {
        width:100% !important;
        max-width:none !important;
        padding:8px !important;
        border-radius:16px !important;
        box-shadow:none !important;
    }
    .header-logo {
        padding:10px !important;
        border-radius:14px !important;
        gap:10px !important;
        margin-bottom:8px !important;
        position:relative !important;
        top:auto !important;
    }
    .header-logo img { width:48px !important; }
    .header-logo h1 {
        font-size:20px !important;
        line-height:1.1 !important;
        white-space:normal !important;
    }
    .header-logo p { font-size:11px !important; }

    #page1, #page2, #page3 {
        display:block !important;
        padding:8px !important;
        border-radius:14px !important;
        margin-top:8px !important;
    }
    .section-card, #pouchHeader, #pouchSection, #cartonSection, .photo-card, .result-card, .result-status-card, .result-meta-card {
        border-radius:14px !important;
        padding:10px !important;
        margin-bottom:8px !important;
    }
    .section-title {
        font-size:16px !important;
        margin-bottom:10px !important;
    }

    .config-grid,
    .config-grid.grid-2,
    .config-grid.grid-3,
    .config-grid.grid-4,
    .config-grid.grid-5,
    .config-grid.grid-9,
    #pouchHeader .config-grid,
    #cartonSection .config-grid {
        display:grid !important;
        grid-template-columns:1fr !important;
        gap:8px !important;
    }
    .config-grid label {
        font-size:13px !important;
        line-height:1.25 !important;
        white-space:normal !important;
        overflow:visible !important;
        text-overflow:clip !important;
        margin-top:4px !important;
    }
    .config-grid input,
    .config-grid select,
    input,
    select {
        width:100% !important;
        height:44px !important;
        min-height:44px !important;
        font-size:16px !important;
        padding:9px 10px !important;
        border-radius:12px !important;
    }
    .info, .warn {
        font-size:14px !important;
        line-height:1.55 !important;
        padding:10px 12px !important;
        border-radius:12px !important;
        word-break:break-word !important;
    }

    #page2.photo-grid {
        display:grid !important;
        grid-template-columns:1fr !important;
        gap:8px !important;
    }
    #page2.photo-grid > *,
    #page2.photo-grid .camera-card,
    #page2.photo-grid .check-row {
        grid-column:1 / -1 !important;
    }
    .photo-card h3 {
        font-size:17px !important;
        margin-bottom:6px !important;
    }
    .photo-card .small {
        min-height:0 !important;
        font-size:13px !important;
        line-height:1.45 !important;
    }
    #previewPouch, #previewCarton {
        height:260px !important;
        max-height:260px !important;
        width:100% !important;
        object-fit:contain !important;
        border-radius:12px !important;
    }
    .capture-time { font-size:13px !important; }
    button, .download {
        width:100% !important;
        min-height:48px !important;
        font-size:16px !important;
        border-radius:12px !important;
    }
    #page2 .check-row .btn-success {
        min-height:56px !important;
        font-size:18px !important;
    }

    .result-hero,
    .result-main-grid,
    .result-meta-grid,
    .result-actions {
        grid-template-columns:1fr !important;
    }
    .result-title { font-size:38px !important; }
    .result-subtitle { font-size:14px !important; line-height:1.4 !important; }
    .result-meta-card { display:none !important; }
    #detail { display:block !important; }
    #detail .result-card {
        padding:10px !important;
    }
    #detail .result-section-title {
        font-size:16px !important;
    }

    .result-popup-overlay {
        padding:0 !important;
        align-items:stretch !important;
        justify-content:stretch !important;
    }
    .result-popup {
        width:100vw !important;
        height:100vh !important;
        max-height:100vh !important;
        border-radius:0 !important;
        border:0 !important;
    }
    .result-popup-header {
        padding:14px 12px !important;
        align-items:center !important;
    }
    .result-popup-title { font-size:34px !important; }
    .result-popup-subtitle {
        font-size:13px !important;
        line-height:1.35 !important;
    }
    .result-popup-close {
        min-width:44px !important;
        height:44px !important;
        font-size:24px !important;
    }
    .result-popup-body { padding:10px !important; }
    .result-popup-meta { display:none !important; }
    .result-popup-image-wrap {
        padding:8px !important;
        border-radius:14px !important;
    }
    .result-popup-image-wrap img {
        width:100% !important;
        max-height:46vh !important;
        border-radius:12px !important;
    }
    .result-popup-bottom,
    .result-popup-actions {
        grid-template-columns:1fr !important;
        gap:8px !important;
        margin-top:8px !important;
    }
    .result-popup-lot-box {
        padding:10px !important;
        border-radius:12px !important;
    }
    .result-popup-lot-value {
        font-size:15px !important;
        line-height:1.35 !important;
    }
    .result-popup-ng-box,
    .result-popup-ok-box {
        padding:12px !important;
        border-radius:12px !important;
        font-size:16px !important;
        overflow-x:auto !important;
    }
    .result-popup-ng-box table {
        min-width:520px !important;
    }
    .result-json details {
        border-radius:12px !important;
    }
    .result-json pre {
        max-height:220px !important;
        font-size:11px !important;
    }

    .camera-toolbar {
        height:auto !important;
        grid-template-columns:1fr !important;
        padding:8px !important;
        gap:8px !important;
    }
    .camera-toolbar button {
        height:52px !important;
        font-size:16px !important;
    }
    .camera-live-wrap, .camera-overlay #video {
        height:calc(100vh - 188px) !important;
    }
}



/* ===== Polished mobile app layout v2 ===== */
:root{
    --app-blue:#0b63ce;
    --app-blue2:#1d4ed8;
    --app-navy:#08233f;
    --app-soft:#f8fbff;
}
.mobile-field{min-width:0;}
.mobile-file-btn{display:none;}
.upload-placeholder{display:none;}
.mobile-bottom-nav{display:none;}
@media (max-width: 920px){
    html,body{background:#edf4fb!important;overflow-x:hidden!important;-webkit-text-size-adjust:100%;}
    body{padding:10px 8px 88px!important;margin:0!important;}
    .box{width:100%!important;max-width:560px!important;margin:0 auto!important;padding:10px!important;border-radius:18px!important;box-shadow:0 16px 44px rgba(15,23,42,.10)!important;border:0!important;background:#ffffff!important;}
    .header-logo{height:auto!important;min-height:76px!important;padding:13px 16px!important;border-radius:16px!important;background:linear-gradient(135deg,#06213d,#0b3b70)!important;align-items:center!important;gap:12px!important;margin:0 0 10px!important;box-shadow:0 10px 22px rgba(11,59,112,.22)!important;}
    .header-logo img{width:54px!important;height:54px!important;border-radius:12px!important;background:#fff!important;padding:4px!important;object-fit:contain!important;margin:0!important;}
    .header-logo h1{font-size:22px!important;line-height:1.05!important;letter-spacing:.2px!important;color:#fff!important;}
    .header-logo p{font-size:12px!important;color:#dbeafe!important;margin-top:4px!important;}
    #page1,#page2,#page3{display:block!important;background:#fff!important;border:1px solid #dbe6f3!important;border-radius:18px!important;padding:14px!important;margin:10px 0!important;box-shadow:0 8px 20px rgba(15,23,42,.04)!important;}
    .section-card,#pouchHeader,#cartonSection,#pouchSection,.photo-card,.camera-card{background:#fff!important;border:1px solid #dbe6f3!important;border-radius:18px!important;padding:14px!important;margin:0 0 12px!important;box-shadow:0 6px 18px rgba(15,23,42,.035)!important;}
    .section-title{font-size:19px!important;font-weight:900!important;color:#172033!important;margin:0 0 14px!important;display:flex!important;align-items:center!important;gap:8px!important;}
    #pouchHeader .section-title::before{content:"⚙️";font-size:18px;}
    #cartonSection .section-title::before{content:"📦";font-size:18px;}
    .config-grid,.config-grid.grid-2,.config-grid.grid-3,.config-grid.grid-4,.config-grid.grid-5,.config-grid.grid-9{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:13px 12px!important;align-items:stretch!important;}
    .mobile-field{display:flex!important;flex-direction:column!important;gap:7px!important;min-width:0!important;}
    .mobile-field label{margin:0!important;font-size:13px!important;font-weight:800!important;color:#334155!important;line-height:1.25!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;}
    .mobile-field input,.mobile-field select{width:100%!important;height:48px!important;min-height:48px!important;margin:0!important;padding:0 14px!important;border-radius:13px!important;border:1px solid #d6e1ee!important;background:#fbfdff!important;font-size:16px!important;color:#0f172a!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.65)!important;}
    .mobile-field input[readonly],.mobile-field input:disabled{background:#f1f5f9!important;color:#334155!important;font-weight:700!important;}
    .full-span,.config-grid .small{grid-column:1/-1!important;}
    #autoExpInfo,#linkedLotInfo{border-radius:14px!important;border:1px solid #bfdbfe!important;background:linear-gradient(180deg,#eff6ff,#f8fbff)!important;color:#1d4ed8!important;padding:12px 14px!important;margin:10px 0!important;font-size:17px!important;line-height:1.55!important;font-weight:700!important;}
    #linkedLotInfo{font-size:16px!important;}
    #linkedLotInfo b,#autoExpInfo b{font-weight:900!important;}
    #page2.photo-grid{display:grid!important;grid-template-columns:1fr 1fr!important;gap:12px!important;align-items:stretch!important;}
    #page2.photo-grid .photo-card{margin:0!important;padding:12px!important;border-radius:17px!important;}
    #page2.photo-grid .camera-card,#page2.photo-grid .check-row{grid-column:1/-1!important;}
    .photo-card h3{font-size:16px!important;margin:0 0 7px!important;color:#172033!important;font-weight:900!important;}
    .photo-card .small{font-size:13px!important;line-height:1.38!important;margin:0 0 10px!important;color:#64748b!important;min-height:38px!important;}
    .photo-card input[type=file]{position:absolute!important;left:-9999px!important;width:1px!important;height:1px!important;opacity:0!important;}
    .mobile-file-btn{display:flex!important;align-items:center!important;justify-content:center!important;gap:7px!important;height:46px!important;border-radius:13px!important;background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;color:#fff!important;font-size:15px!important;font-weight:900!important;margin-top:10px!important;box-shadow:0 8px 16px rgba(37,99,235,.18)!important;}
    .mobile-file-btn::before{content:"📷";}
    .upload-placeholder{display:flex!important;align-items:center!important;justify-content:center!important;height:126px!important;border:1.5px dashed #cbd5e1!important;border-radius:14px!important;background:linear-gradient(180deg,#f8fbff,#ffffff)!important;color:#2563eb!important;font-size:48px!important;margin:10px 0 0!important;}
    .upload-placeholder::before{content:"🖼️+";}
    #previewPouch,#previewCarton{width:100%!important;height:160px!important;max-height:160px!important;object-fit:contain!important;border-radius:14px!important;background:#0f172a!important;margin:10px 0 0!important;border:1px solid #dbe6f3!important;}
    .capture-time{font-size:12px!important;color:#64748b!important;font-weight:800!important;margin-top:7px!important;}
    .camera-card h3::before{content:"📸 ";}
    .camera-card .small{font-size:14px!important;color:#64748b!important;line-height:1.45!important;}
    #openCameraBtn, .check-row .btn-success, button[onclick="sendCheck()"]{height:58px!important;border-radius:15px!important;font-size:18px!important;font-weight:900!important;box-shadow:0 10px 20px rgba(37,99,235,.18)!important;}
    #openCameraBtn{background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;}
    .check-row .btn-success, button[onclick="sendCheck()"]{background:linear-gradient(135deg,#16a34a,#15803d)!important;box-shadow:0 12px 22px rgba(22,163,74,.20)!important;}
    .check-row .btn-success::before, button[onclick="sendCheck()"]::before{content:"🔍 ";}
    #page3{padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;}
    #result,#detail{margin:0!important;}
    .pass,.ng{border-radius:18px!important;padding:18px!important;margin:10px 0!important;font-size:36px!important;line-height:1.1!important;text-align:left!important;box-shadow:0 8px 20px rgba(15,23,42,.05)!important;}
    .pass{background:#ecfdf5!important;color:#15803d!important;border:1px solid #86efac!important;}
    .ng{background:#fef2f2!important;color:#dc2626!important;border:1px solid #fca5a5!important;}
    .result-popup-overlay{padding:10px!important;align-items:center!important;}
    .result-popup{width:100%!important;max-width:520px!important;max-height:92vh!important;border-radius:20px!important;overflow:auto!important;}
    .result-popup-header{padding:18px!important;border-radius:20px 20px 0 0!important;}
    .result-popup-title{font-size:28px!important;}
    .result-popup-body{padding:14px!important;}
    .result-popup-evidence img{max-height:360px!important;width:100%!important;object-fit:contain!important;border-radius:14px!important;}
    .result-popup-ng-box,.result-popup-ok-box,.result-popup-summary{border-radius:16px!important;padding:14px!important;}
    .result-popup-ng-box table{font-size:13px!important;word-break:break-word!important;}
    .result-popup-ng-box th,.result-popup-ng-box td{padding:8px!important;}
    .result-status-strip,.result-popup-status-strip,.ai-status-strip{background:#16a34a!important;color:#fff!important;border-radius:14px!important;padding:12px!important;font-weight:900!important;text-align:center!important;}
    .ng-status,.popup-ng .result-status-strip,.result-popup-header.popup-ng + * .ai-status-strip{background:#dc2626!important;color:#fff!important;}
    .mobile-bottom-nav{position:fixed!important;left:8px!important;right:8px!important;bottom:8px!important;height:70px!important;background:rgba(255,255,255,.96)!important;backdrop-filter:blur(12px)!important;border:1px solid #dbe6f3!important;border-radius:22px!important;box-shadow:0 -8px 28px rgba(15,23,42,.12)!important;display:grid!important;grid-template-columns:repeat(4,1fr)!important;z-index:9000!important;overflow:hidden!important;}
    .mobile-bottom-nav button{margin:0!important;background:transparent!important;color:#475569!important;box-shadow:none!important;border-radius:0!important;height:100%!important;font-size:12px!important;display:flex!important;flex-direction:column!important;gap:3px!important;align-items:center!important;justify-content:center!important;padding:4px!important;}
    .mobile-bottom-nav button:first-child{color:#2563eb!important;background:#eff6ff!important;font-weight:900!important;}
    .mobile-bottom-nav .nav-ico{font-size:25px!important;line-height:1!important;}
}
@media (max-width:430px){
    body{padding:7px 5px 84px!important;}
    .box{padding:8px!important;border-radius:16px!important;}
    .header-logo{padding:11px!important;}
    .header-logo h1{font-size:19px!important;}
    .header-logo img{width:48px!important;height:48px!important;}
    #page1,#page2{padding:10px!important;border-radius:16px!important;}
    .section-card,#pouchHeader,#cartonSection,#pouchSection,.photo-card,.camera-card{padding:11px!important;border-radius:16px!important;}
    .config-grid,.config-grid.grid-2,.config-grid.grid-3,.config-grid.grid-4,.config-grid.grid-5,.config-grid.grid-9{gap:11px 10px!important;}
    .mobile-field label{font-size:12px!important;}
    .mobile-field input,.mobile-field select{height:45px!important;min-height:45px!important;font-size:14px!important;padding:0 10px!important;}
    #page2.photo-grid{grid-template-columns:1fr 1fr!important;gap:9px!important;}
    .photo-card .small{font-size:12px!important;min-height:50px!important;}
    .upload-placeholder{height:104px!important;font-size:38px!important;}
    #previewPouch,#previewCarton{height:130px!important;max-height:130px!important;}
    .mobile-file-btn{height:44px!important;font-size:13px!important;}
}



/* ===== TRUE MOBILE APP UI OVERRIDE v2 ===== */
:root{--app-blue:#0b2340;--app-blue2:#0f4db8;--app-green:#159947;--app-red:#dc2626;--app-soft:#f4f8fd;}
html{background:#eef5fb;}
body{background:#eef5fb!important;padding:0!important;margin:0!important;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif!important;color:#0f172a!important;}
.box{width:100%!important;max-width:980px!important;margin:0 auto!important;padding:10px!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;border:0!important;}
.header-logo{position:sticky;top:0;z-index:50;justify-content:flex-start!important;background:linear-gradient(135deg,#08213b,#0b3e84)!important;color:#fff!important;border-radius:18px!important;padding:12px 14px!important;margin:0 0 10px!important;box-shadow:0 8px 24px rgba(8,33,59,.18)!important;}
.header-logo img{width:54px!important;height:54px!important;object-fit:contain!important;background:#fff!important;border-radius:12px!important;padding:4px!important;margin:0!important;border:0!important;}
.header-logo h1{font-size:24px!important;line-height:1.05!important;margin:0!important;color:white!important;letter-spacing:.2px!important;}
.header-logo p{font-size:13px!important;color:#dbeafe!important;margin:3px 0 0!important;}
.step-tabs,.compact-mode-info,#page1 .nav-row,#page3 .nav-row{display:none!important;}
.step-page,.step-page.active{display:block!important;animation:none!important;}
#page1,#page2,#page3{background:transparent!important;border:0!important;padding:0!important;margin:0!important;border-radius:0!important;}
.mobile-card,.section-card,.photo-card,.camera-card,#autoExpInfo,#linkedLotInfo,#result > *, .result-card{background:rgba(255,255,255,.98)!important;border:1px solid #dbe6f3!important;border-radius:18px!important;box-shadow:0 8px 22px rgba(15,23,42,.06)!important;padding:16px!important;margin:10px 0!important;}
.section-title{font-size:20px!important;font-weight:900!important;line-height:1.2!important;color:#172033!important;margin:0 0 14px!important;}
.mobile-field-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:12px!important;align-items:stretch!important;}
.setup-field-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important;}
.carton-field-grid{grid-template-columns:repeat(4,minmax(0,1fr))!important;}
.field-card{min-width:0!important;display:flex!important;flex-direction:column!important;gap:7px!important;background:transparent!important;padding:0!important;margin:0!important;}
.field-card label{font-size:13px!important;line-height:1.25!important;color:#334155!important;font-weight:800!important;margin:0!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;}
.field-card input,.field-card select,#page1 input,#page1 select{width:100%!important;height:48px!important;border:1px solid #d6e0ec!important;border-radius:13px!important;background:#fff!important;color:#0f172a!important;font-size:16px!important;font-weight:600!important;padding:0 12px!important;margin:0!important;box-shadow:0 2px 8px rgba(15,23,42,.03)!important;}
.field-card input[readonly],#page1 input[readonly]{background:#f1f5f9!important;color:#334155!important;}
#autoExpInfo,#linkedLotInfo{background:#eef6ff!important;border-color:#bfdbfe!important;color:#1d4ed8!important;font-size:17px!important;line-height:1.55!important;font-weight:700!important;}
#linkedLotInfo b,#linkedLotInfo strong{font-weight:900!important;}
#page2.photo-grid{display:grid!important;grid-template-columns:1fr 1fr!important;gap:12px!important;align-items:stretch!important;margin-top:8px!important;}
#page2.photo-grid > *{grid-column:auto!important;}
.photo-card{margin:0!important;display:flex!important;flex-direction:column!important;}
.photo-card h3{font-size:18px!important;font-weight:900!important;margin:0 0 6px!important;color:#172033!important;}
.photo-card .small{font-size:15px!important;line-height:1.45!important;color:#64748b!important;margin:0 0 12px!important;min-height:0!important;font-weight:600!important;}
.photo-card input[type=file]{height:44px!important;border:1px dashed #cbd5e1!important;border-radius:13px!important;background:#f8fbff!important;padding:10px!important;font-size:14px!important;margin:0 0 10px!important;}
#previewPouch,#previewCarton{width:100%!important;height:260px!important;max-height:none!important;object-fit:contain!important;background:#0f172a!important;border-radius:16px!important;border:1px solid #cbd5e1!important;margin:0!important;}
.capture-time{display:block!important;color:#64748b!important;font-size:13px!important;font-weight:800!important;margin-top:8px!important;}
.camera-card{grid-column:1 / -1!important;margin:12px 0 0!important;}
.camera-card h3{font-size:18px!important;margin:0 0 6px!important;}
.camera-card .small{font-size:15px!important;line-height:1.4!important;color:#64748b!important;margin:0 0 12px!important;}
button,#openCameraBtn,.btn-success{height:56px!important;border-radius:15px!important;font-size:18px!important;font-weight:900!important;box-shadow:0 8px 16px rgba(37,99,235,.18)!important;margin-top:8px!important;}
#openCameraBtn{background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;}
.check-row{grid-column:1 / -1!important;display:block!important;margin:12px 0!important;}
.check-row .btn-secondary{display:none!important;}
.check-row .btn-success{background:linear-gradient(135deg,#16a34a,#15803d)!important;width:100%!important;height:62px!important;font-size:19px!important;}
.camera-overlay{position:fixed!important;inset:0!important;background:#000!important;z-index:99999!important;display:none!important;flex-direction:column!important;padding:0!important;}
.camera-overlay.show{display:flex!important;}
.camera-live-wrap{position:relative!important;flex:1!important;min-height:0!important;display:flex!important;align-items:center!important;justify-content:center!important;background:#000!important;}
#video{width:100vw!important;height:100%!important;max-height:none!important;object-fit:contain!important;background:#000!important;border:0!important;border-radius:0!important;margin:0!important;}
.camera-toolbar{display:grid!important;grid-template-columns:1fr 1fr 1fr!important;gap:8px!important;padding:10px!important;background:#111827!important;padding-bottom:calc(10px + env(safe-area-inset-bottom))!important;}
.camera-toolbar button{height:54px!important;margin:0!important;font-size:15px!important;border-radius:14px!important;}
.scan-guide{position:absolute!important;left:12%!important;right:12%!important;top:42%!important;height:18%!important;border:4px solid #22c55e!important;border-radius:18px!important;box-shadow:0 0 0 9999px rgba(0,0,0,.12)!important;pointer-events:none!important;}
#page3.result-dashboard{margin-top:8px!important;}
#result .result-popup-inline,#result .result-shell{background:#fff!important;border-radius:18px!important;border:1px solid #dbe6f3!important;box-shadow:0 8px 22px rgba(15,23,42,.08)!important;}
.status-strip,.ng-list-card{border-radius:16px!important;overflow:hidden!important;}
.mobile-bottom-nav{display:none!important;}
@media (max-width:768px){
    body{padding:0!important;padding-bottom:92px!important;}
    .box{padding:8px!important;max-width:none!important;}
    .header-logo{border-radius:14px!important;padding:10px 12px!important;margin-bottom:8px!important;}
    .header-logo img{width:44px!important;height:44px!important;border-radius:10px!important;}
    .header-logo h1{font-size:20px!important;}
    .header-logo p{font-size:11px!important;}
    .mobile-card,.section-card,.photo-card,.camera-card,#autoExpInfo,#linkedLotInfo{border-radius:14px!important;padding:12px!important;margin:8px 0!important;}
    .section-title{font-size:18px!important;margin-bottom:12px!important;}
    .setup-field-grid,.carton-field-grid,.mobile-field-grid{grid-template-columns:1fr!important;gap:10px!important;}
    .field-card label{font-size:13px!important;}
    .field-card input,.field-card select,#page1 input,#page1 select{height:46px!important;font-size:16px!important;border-radius:12px!important;}
    #autoExpInfo,#linkedLotInfo{font-size:16px!important;padding:12px!important;}
    #page2.photo-grid{grid-template-columns:1fr!important;gap:10px!important;}
    .photo-card{padding:14px!important;}
    .photo-card h3{font-size:17px!important;}
    .photo-card .small{font-size:15px!important;}
    #previewPouch,#previewCarton{height:300px!important;border-radius:14px!important;}
    .camera-card{grid-column:1!important;}
    #openCameraBtn,.check-row .btn-success{height:58px!important;font-size:18px!important;border-radius:14px!important;}
    #page3{display:none!important;}
    .mobile-bottom-nav{position:fixed!important;left:10px!important;right:10px!important;bottom:10px!important;height:70px!important;background:rgba(255,255,255,.96)!important;backdrop-filter:blur(14px)!important;border:1px solid #dbe6f3!important;border-radius:22px!important;box-shadow:0 -8px 28px rgba(15,23,42,.14)!important;display:grid!important;grid-template-columns:repeat(4,1fr)!important;z-index:9000!important;overflow:hidden!important;}
    .mobile-bottom-nav button{height:100%!important;margin:0!important;background:transparent!important;color:#475569!important;box-shadow:none!important;border-radius:0!important;font-size:11px!important;display:flex!important;flex-direction:column!important;gap:4px!important;align-items:center!important;justify-content:center!important;padding:4px!important;}
    .mobile-bottom-nav button:first-child{color:#2563eb!important;background:#eff6ff!important;font-weight:900!important;}
    .mobile-bottom-nav .nav-ico{font-size:24px!important;line-height:1!important;}
}
@media (max-width:420px){
    #previewPouch,#previewCarton{height:260px!important;}
    .field-card input,.field-card select,#page1 input,#page1 select{font-size:15px!important;}
    #autoExpInfo,#linkedLotInfo{font-size:15px!important;}
}



/* ===== FINAL MOBILE COMPLETENESS FIX: no clipping, visible upload buttons ===== */
.static-mobile-file-btn{display:none;}
.static-upload-placeholder{display:none;}
@media (max-width: 768px){
    *{box-sizing:border-box!important;}
    html,body{width:100%!important;max-width:100%!important;overflow-x:hidden!important;background:#eef5fb!important;}
    body{padding:0!important;padding-bottom:92px!important;}
    .box{width:100%!important;max-width:100%!important;margin:0!important;padding:8px!important;overflow:hidden!important;}
    .header-logo{position:relative!important;top:auto!important;margin:0 0 8px!important;width:100%!important;}

    #page1,#page2{width:100%!important;max-width:100%!important;overflow:hidden!important;}
    #pouchHeader,#cartonSection,.photo-card,.camera-card,#autoExpInfo,#linkedLotInfo{
        width:100%!important;max-width:100%!important;overflow:hidden!important;
    }

    .setup-field-grid{
        display:grid!important;
        grid-template-columns:repeat(2,minmax(0,1fr))!important;
        gap:12px!important;
    }
    .carton-field-grid,
    #cartonTHBox,
    #cartonExportBox{
        display:grid!important;
        grid-template-columns:repeat(2,minmax(0,1fr))!important;
        gap:12px!important;
        width:100%!important;
        max-width:100%!important;
        overflow:visible!important;
    }
    #cartonTHBox.hidden-market,
    #cartonExportBox.hidden-market{display:none!important;}

    .field-card{min-width:0!important;width:100%!important;}
    .field-card label{font-size:13px!important;line-height:1.25!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;}
    .field-card input,.field-card select,#page1 input,#page1 select{
        width:100%!important;max-width:100%!important;min-width:0!important;height:48px!important;
        font-size:16px!important;border-radius:14px!important;padding:0 12px!important;
    }

    #autoExpInfo,#linkedLotInfo{
        font-size:16px!important;line-height:1.55!important;padding:13px 14px!important;word-break:break-word!important;
    }

    #page2.photo-grid{display:grid!important;grid-template-columns:1fr!important;gap:10px!important;}
    #page2.photo-grid>*{grid-column:1/-1!important;}
    .photo-card{padding:14px!important;border-radius:18px!important;}
    .photo-card h3{font-size:18px!important;margin-bottom:6px!important;}
    .photo-card .small{font-size:15px!important;line-height:1.45!important;min-height:0!important;margin-bottom:12px!important;}

    .photo-card input[type=file]{
        position:absolute!important;left:-9999px!important;width:1px!important;height:1px!important;opacity:0!important;
    }
    .static-mobile-file-btn,.mobile-file-btn{
        display:flex!important;align-items:center!important;justify-content:center!important;gap:8px!important;
        width:100%!important;height:52px!important;border-radius:15px!important;
        background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;color:#fff!important;
        font-size:16px!important;font-weight:900!important;margin:12px 0 0!important;
        box-shadow:0 8px 18px rgba(37,99,235,.20)!important;
    }
    .static-upload-placeholder,.upload-placeholder{
        display:flex!important;align-items:center!important;justify-content:center!important;
        width:100%!important;height:150px!important;border:1.5px dashed #cbd5e1!important;
        border-radius:16px!important;background:linear-gradient(180deg,#f8fbff,#ffffff)!important;
        color:#2563eb!important;font-size:46px!important;margin:12px 0 0!important;
    }
    #previewPouch:not([style*="display:none"])+.capture-time,
    #previewCarton:not([style*="display:none"])+.capture-time{display:block!important;}
    #previewPouch,#previewCarton{
        width:100%!important;height:260px!important;max-height:260px!important;object-fit:contain!important;
        background:#0f172a!important;border-radius:16px!important;margin-top:12px!important;
    }
    #previewPouch[style*="display:none"],#previewCarton[style*="display:none"]{display:none!important;}

    .camera-card{padding:14px!important;}
    #openCameraBtn,.check-row .btn-success,button[onclick="sendCheck()"]{
        width:100%!important;height:60px!important;font-size:18px!important;border-radius:16px!important;
    }
}
@media (max-width: 430px){
    .setup-field-grid,.carton-field-grid,#cartonTHBox,#cartonExportBox{grid-template-columns:1fr!important;}
    .field-card input,.field-card select,#page1 input,#page1 select{height:50px!important;font-size:16px!important;}
    #previewPouch,#previewCarton{height:240px!important;}
}



/* ===== FINAL FIX 2026-06-24: mobile fields complete + remove light-blue info panels ===== */
#autoExpInfo,
#linkedLotInfo{
    display:none !important;
}

/* make carton lot fields never overflow/cut off */
#cartonSection,
#cartonTHBox,
#cartonExportBox,
.carton-field-grid{
    overflow:visible !important;
    max-width:100% !important;
}

#cartonTHBox,
#cartonExportBox,
.carton-field-grid{
    display:grid !important;
    grid-template-columns:repeat(4,minmax(0,1fr)) !important;
    gap:14px !important;
}

#cartonTHBox.hidden-market,
#cartonExportBox.hidden-market{
    display:none !important;
}

#cartonSection .field-card,
#cartonSection .field-card input,
#cartonSection .field-card select{
    min-width:0 !important;
    width:100% !important;
    max-width:100% !important;
}

@media (max-width:768px){
    html, body{
        width:100% !important;
        max-width:100% !important;
        overflow-x:hidden !important;
    }
    .box{
        width:100% !important;
        max-width:100% !important;
        overflow:visible !important;
        padding:8px !important;
    }

    /* all setup fields one per row on phone, so no value is cut */
    .setup-field-grid,
    #pouchHeader .mobile-field-grid,
    #cartonTHBox,
    #cartonExportBox,
    .carton-field-grid{
        display:grid !important;
        grid-template-columns:1fr !important;
        gap:14px !important;
        width:100% !important;
        max-width:100% !important;
        overflow:visible !important;
    }

    #cartonTHBox.hidden-market,
    #cartonExportBox.hidden-market{
        display:none !important;
    }

    .field-card{
        width:100% !important;
        max-width:100% !important;
        min-width:0 !important;
        overflow:visible !important;
    }

    .field-card label{
        display:block !important;
        width:100% !important;
        white-space:normal !important;
        overflow:visible !important;
        text-overflow:clip !important;
        font-size:15px !important;
        line-height:1.35 !important;
        margin-bottom:7px !important;
    }

    .field-card input,
    .field-card select,
    #page1 input,
    #page1 select{
        display:block !important;
        width:100% !important;
        max-width:100% !important;
        min-width:0 !important;
        height:54px !important;
        font-size:17px !important;
        padding:0 14px !important;
        border-radius:16px !important;
    }

    #cartonSection{
        padding:16px !important;
        border-radius:22px !important;
    }

    #cartonSection .section-title{
        font-size:22px !important;
        margin-bottom:16px !important;
    }

    /* remove the light-blue formula/linked-info blocks completely */
    #autoExpInfo,
    #linkedLotInfo{
        display:none !important;
    }

    /* image cards remain full width and show upload button clearly */
    #page2.photo-grid{
        display:grid !important;
        grid-template-columns:1fr !important;
        gap:14px !important;
    }
    #page2.photo-grid > *{
        grid-column:1 / -1 !important;
        width:100% !important;
        max-width:100% !important;
    }
    .photo-card{
        width:100% !important;
        max-width:100% !important;
        overflow:visible !important;
    }
}


/* ===== HARD MOBILE FINAL FIX: no cut-off, no blue panels, full-width cards ===== */
#autoExpInfo, #linkedLotInfo { display:none !important; height:0 !important; padding:0 !important; margin:0 !important; border:0 !important; overflow:hidden !important; }

@media (max-width: 920px) {
  html, body {
    width:100% !important;
    max-width:100% !important;
    margin:0 !important;
    padding:0 !important;
    overflow-x:hidden !important;
    background:#eef5fb !important;
  }
  * { box-sizing:border-box !important; }
  .box {
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    margin:0 !important;
    padding:8px !important;
    border-radius:0 !important;
    overflow-x:hidden !important;
  }
  .header-logo {
    width:100% !important;
    max-width:100% !important;
    margin:0 0 10px 0 !important;
    padding:10px !important;
    border-radius:14px !important;
  }
  .header-logo img { width:44px !important; min-width:44px !important; }
  .header-logo h1 { font-size:20px !important; line-height:1.1 !important; }
  .header-logo p { font-size:11px !important; }

  #page1,
  #pouchHeader,
  #cartonSection,
  #pouchSection,
  #page2,
  #page3,
  .section-card,
  .photo-card,
  .camera-card {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    overflow:visible !important;
    margin-left:0 !important;
    margin-right:0 !important;
  }

  #page1, #page2, #page3 {
    padding:0 !important;
    background:transparent !important;
    border:0 !important;
  }

  #pouchHeader,
  #cartonSection,
  .photo-card,
  .camera-card {
    background:#ffffff !important;
    border:1px solid #dbe7f3 !important;
    border-radius:18px !important;
    padding:14px !important;
    margin:0 0 12px 0 !important;
    box-shadow:0 4px 12px rgba(15,23,42,.04) !important;
  }

  .section-title {
    display:block !important;
    width:100% !important;
    font-size:21px !important;
    line-height:1.25 !important;
    margin:0 0 14px 0 !important;
    color:#0f172a !important;
    white-space:normal !important;
  }

  .setup-field-grid,
  .carton-field-grid,
  #pouchHeader .mobile-field-grid,
  #cartonTHBox,
  #cartonExportBox,
  .mobile-field-grid,
  .config-grid,
  .config-grid.grid-2,
  .config-grid.grid-3,
  .config-grid.grid-4,
  .config-grid.grid-5,
  .config-grid.grid-9 {
    display:grid !important;
    grid-template-columns:1fr !important;
    gap:12px !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    overflow:visible !important;
  }
  #cartonTHBox.hidden-market,
  #cartonExportBox.hidden-market,
  .hidden-market { display:none !important; }

  .field-card,
  .mobile-field {
    display:flex !important;
    flex-direction:column !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    gap:7px !important;
    margin:0 !important;
    padding:0 !important;
    overflow:visible !important;
  }
  .field-card label,
  .mobile-field label,
  #page1 label {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    margin:0 !important;
    padding:0 !important;
    font-size:14px !important;
    line-height:1.35 !important;
    font-weight:800 !important;
    color:#334155 !important;
    white-space:normal !important;
    overflow:visible !important;
    text-overflow:clip !important;
  }
  .field-card input,
  .field-card select,
  .mobile-field input,
  .mobile-field select,
  #page1 input,
  #page1 select {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    height:52px !important;
    min-height:52px !important;
    margin:0 !important;
    padding:0 14px !important;
    border-radius:15px !important;
    border:1px solid #d5e1ee !important;
    background:#f8fbff !important;
    color:#1e293b !important;
    font-size:17px !important;
    font-weight:700 !important;
    overflow:visible !important;
  }

  #autoExpInfo, #linkedLotInfo { display:none !important; }
  .info:not(.compact-mode-info) { display:none !important; }
  .compact-mode-info { display:none !important; }

  #page2.photo-grid,
  #page2 {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    overflow:visible !important;
  }
  .photo-card h3 { font-size:22px !important; margin:0 0 8px 0 !important; }
  .photo-card .small { font-size:16px !important; line-height:1.45 !important; margin:0 0 10px 0 !important; color:#64748b !important; }
  .photo-card input[type="file"] { position:absolute !important; left:-9999px !important; opacity:0 !important; width:1px !important; height:1px !important; }
  .static-mobile-file-btn, .mobile-file-btn {
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    width:100% !important;
    height:56px !important;
    border-radius:16px !important;
    margin:12px 0 !important;
    background:linear-gradient(135deg,#2563eb,#1d4ed8) !important;
    color:white !important;
    font-size:18px !important;
    font-weight:900 !important;
  }
  .static-upload-placeholder, .upload-placeholder {
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    width:100% !important;
    height:180px !important;
    border:2px dashed #cbd5e1 !important;
    border-radius:18px !important;
    background:#ffffff !important;
    color:#2563eb !important;
    font-size:52px !important;
    margin:10px 0 0 !important;
  }
  #previewPouch, #previewCarton {
    display:block !important;
    width:100% !important;
    height:auto !important;
    max-height:360px !important;
    object-fit:contain !important;
    border-radius:16px !important;
    margin:12px 0 0 !important;
    background:#0f172a !important;
  }
  #previewPouch[style*="display:none"], #previewCarton[style*="display:none"] { display:none !important; }
  #openCameraBtn, button[onclick="sendCheck()"], .check-row .btn-success {
    width:100% !important;
    height:60px !important;
    border-radius:16px !important;
    font-size:18px !important;
    font-weight:900 !important;
    margin:8px 0 12px 0 !important;
  }
  .check-row { display:block !important; width:100% !important; }
  .check-row .btn-secondary { display:none !important; }
}



/* ===== ULTIMATE OVERRIDE: FORCE MOBILE-SAFE ONE COLUMN, NO CUT-OFF ===== */
html, body {
    width:100% !important;
    max-width:100% !important;
    overflow-x:hidden !important;
}
body {
    margin:0 !important;
    padding:8px !important;
    background:#eef5fb !important;
}
* {
    box-sizing:border-box !important;
}
.box,
#page1,
#page2,
#page3,
#pouchHeader,
#cartonSection,
#pouchSection,
.photo-card,
.camera-card,
.section-card,
.mobile-card {
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    overflow:visible !important;
}
.box {
    margin:0 auto !important;
    padding:8px !important;
    border-radius:18px !important;
}
#page1,
#page2,
#page3 {
    display:block !important;
    grid-template-columns:1fr !important;
    background:transparent !important;
    border:0 !important;
    padding:0 !important;
}
#pouchHeader,
#cartonSection,
.photo-card,
.camera-card {
    display:block !important;
    background:#fff !important;
    border:1px solid #dbe7f3 !important;
    border-radius:20px !important;
    padding:14px !important;
    margin:0 0 14px 0 !important;
    box-shadow:0 5px 16px rgba(15,23,42,.04) !important;
}
.section-title {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    font-size:21px !important;
    line-height:1.25 !important;
    margin:0 0 14px 0 !important;
    color:#0f172a !important;
    white-space:normal !important;
    overflow:visible !important;
    text-overflow:clip !important;
}
/* Force every form group to stack, even on iPhone/LINE browser that reports wide viewport */
.setup-field-grid,
.carton-field-grid,
.mobile-field-grid,
.config-grid,
.config-grid.grid-2,
.config-grid.grid-3,
.config-grid.grid-4,
.config-grid.grid-5,
.config-grid.grid-9,
#pouchHeader .mobile-field-grid,
#pouchHeader .config-grid,
#cartonSection .mobile-field-grid,
#cartonSection .config-grid,
#cartonTHBox,
#cartonExportBox {
    display:grid !important;
    grid-template-columns:1fr !important;
    gap:14px !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    overflow:visible !important;
}
#cartonTHBox.hidden-market,
#cartonExportBox.hidden-market,
.hidden-market {
    display:none !important;
}
.field-card,
.mobile-field,
#cartonSection .field-card,
#pouchHeader .field-card {
    display:flex !important;
    flex-direction:column !important;
    gap:7px !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    margin:0 !important;
    padding:0 !important;
    overflow:visible !important;
}
.field-card label,
.mobile-field label,
#page1 label,
#cartonSection label,
#pouchHeader label {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    margin:0 !important;
    padding:0 !important;
    font-size:15px !important;
    line-height:1.35 !important;
    font-weight:800 !important;
    color:#334155 !important;
    white-space:normal !important;
    overflow:visible !important;
    text-overflow:clip !important;
}
.field-card input,
.field-card select,
.mobile-field input,
.mobile-field select,
#page1 input,
#page1 select,
#cartonSection input,
#cartonSection select,
#pouchHeader input,
#pouchHeader select {
    display:block !important;
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    height:52px !important;
    min-height:52px !important;
    margin:0 !important;
    padding:0 14px !important;
    border-radius:16px !important;
    border:1px solid #d5e1ee !important;
    background:#f8fbff !important;
    color:#1e293b !important;
    font-size:17px !important;
    font-weight:700 !important;
    overflow:visible !important;
}
.field-card input[readonly],
#page1 input[readonly] {
    background:#f1f5f9 !important;
    color:#334155 !important;
}
/* Remove light-blue info panels completely */
#autoExpInfo,
#linkedLotInfo,
.info.compact-mode-info,
.info:not(.capture-toast) {
    display:none !important;
    height:0 !important;
    padding:0 !important;
    margin:0 !important;
    border:0 !important;
    overflow:hidden !important;
}
/* Photo upload cards */
#page2.photo-grid,
#page2 {
    display:block !important;
    grid-template-columns:1fr !important;
    gap:0 !important;
}
#page2.photo-grid > *,
#page2 > * {
    grid-column:1 / -1 !important;
    width:100% !important;
    max-width:100% !important;
}
.photo-card h3 {
    font-size:22px !important;
    line-height:1.25 !important;
    margin:0 0 8px 0 !important;
}
.photo-card .small {
    font-size:16px !important;
    line-height:1.45 !important;
    margin:0 0 10px 0 !important;
    color:#64748b !important;
}
.photo-card input[type="file"] {
    position:absolute !important;
    left:-9999px !important;
    opacity:0 !important;
    width:1px !important;
    height:1px !important;
}
.static-mobile-file-btn,
.mobile-file-btn {
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    width:100% !important;
    min-height:56px !important;
    border-radius:16px !important;
    margin:12px 0 !important;
    background:linear-gradient(135deg,#2563eb,#1d4ed8) !important;
    color:#fff !important;
    font-size:18px !important;
    font-weight:900 !important;
    text-align:center !important;
}
#previewPouch,
#previewCarton,
.static-upload-placeholder,
.upload-placeholder {
    display:flex !important;
    width:100% !important;
    max-width:100% !important;
    height:220px !important;
    max-height:220px !important;
    object-fit:contain !important;
    border-radius:18px !important;
    margin-top:10px !important;
    background:#fff !important;
}
button,
.download {
    width:100% !important;
    max-width:100% !important;
    min-height:56px !important;
    font-size:18px !important;
    font-weight:900 !important;
    border-radius:16px !important;
    white-space:normal !important;
}
@media (min-width: 921px) {
    .box { max-width:760px !important; }
}


/* Force hide Mix Date / Mix Code cards when product does not need mix code */
.mix-field.hidden-field { display:none !important; }



/* ===== HARD FIX: hide mix date/mix code for EPC ===== */
.mix-field.force-hidden,
.hidden-field.force-hidden,
body.product-epc .mix-field,
body.product-epc #mixDate,
body.product-epc #mixCode,
body.product-epc #mixDateHeaderLabel,
body.product-epc #mixCodeHeaderLabel {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    min-width: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    overflow: hidden !important;
}


/* ===== Clean bottom result card, no broken HTML text ===== */
.result-clean-card{
    background:#fff;
    border:1px solid #d7dee8;
    border-radius:18px;
    padding:18px;
    text-align:center;
    box-shadow:0 8px 22px rgba(15,23,42,.08);
    margin-top:14px;
}
.result-clean-card.result-clean-pass{border-left:8px solid #16a34a;}
.result-clean-card.result-clean-ng{border-left:8px solid #dc2626;}
.result-clean-title{font-size:34px;font-weight:900;line-height:1.1;}
.result-clean-pass .result-clean-title{color:#16a34a;}
.result-clean-ng .result-clean-title{color:#dc2626;}
.result-clean-subtitle{font-size:16px;color:#334155;font-weight:700;margin-top:8px;}
.result-reopen-btn{max-width:360px;margin:16px auto 0 !important;display:block;}
.result-popup-header.popup-pass{background:linear-gradient(135deg,#16a34a,#15803d) !important;}
.result-popup-header.popup-ng{background:linear-gradient(135deg,#dc2626,#991b1b) !important;}
.result-popup-actions .download{white-space:normal;}

@media (max-width: 820px){
  body{overflow-x:hidden !important;}
  .box{width:100% !important;max-width:100% !important;overflow:hidden !important;}
  #cartonSection, #cartonTHBox, #cartonExportBox, .section-card, .config-grid{
    width:100% !important; max-width:100% !important; overflow:visible !important;
  }
  #cartonTHBox .config-grid, #cartonExportBox .config-grid, #cartonSection .config-grid, .config-grid{
    display:grid !important; grid-template-columns:1fr !important; gap:12px !important;
  }
  #cartonTHBox *, #cartonExportBox *, #cartonSection *{min-width:0 !important;}
  input, select, button{max-width:100% !important;}
  .result-clean-title{font-size:30px;}
  .result-popup{align-items:flex-end !important;}
  .result-popup-content{width:100% !important;max-width:100% !important;max-height:92vh !important;border-radius:22px 22px 0 0 !important;}
}


/* ===== Final fixes: hide check-only fields, remove placeholders, show selected images ===== */
#mfg, #linapackExp { display:none !important; }
.static-upload-placeholder, .upload-placeholder { display:none !important; }
.mobile-file-btn { display:none !important; }
.static-mobile-file-btn {
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    width:100% !important;
    min-height:48px !important;
    border-radius:14px !important;
    background:linear-gradient(135deg,#2563eb,#1d4ed8) !important;
    color:#fff !important;
    font-size:15px !important;
    font-weight:900 !important;
    margin-top:10px !important;
    cursor:pointer !important;
}
#previewPouch, #previewCarton {
    display:none !important;
    width:100% !important;
    height:auto !important;
    max-height:360px !important;
    object-fit:contain !important;
    background:#0f172a !important;
    border-radius:16px !important;
    border:1px solid #cbd5e1 !important;
    margin-top:12px !important;
}
#previewPouch.has-image, #previewCarton.has-image { display:block !important; }
.photo-card input[type=file] {
    width:1px !important; height:1px !important; opacity:0 !important; position:absolute !important; left:-9999px !important;
}
@media (max-width: 768px) {
    #page1, #page2.photo-grid { display:block !important; width:100% !important; }
    .mobile-field-grid, .setup-field-grid, .carton-field-grid { display:block !important; width:100% !important; }
    .field-card, .photo-card { width:100% !important; margin:0 0 12px 0 !important; }
    .photo-card { padding:14px !important; }
    #previewPouch, #previewCarton { max-height:420px !important; }
}

</style>
</head>
<body>
<div id="captureToast" class="capture-toast"></div>

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

<div id="pouchHeader" class="section-card mobile-card setup-card">
    <div class="section-title">⚙️ ตั้งค่าข้อมูลการตรวจ</div>
    <div class="mobile-field-grid setup-field-grid">
        <div class="field-card">
            <label>ประเภทไลน์</label>
            <select id="mode" onchange="changeMode()">
                <option value="" selected disabled>เลือกประเภทไลน์</option>
                <option value="sachet">Sachet</option>
                <option value="linapack">Linapack</option>
            </select>
        </div>
        <div class="field-card">
            <label id="machineHeaderLabel">เครื่อง (MFG)</label>
            <select id="lpMachine" onchange="updateExpectedLinkedLots()">
                <option value="" selected disabled>เลือกเครื่อง</option>
                <option value="MS1">MS1</option><option value="MS2">MS2</option><option value="MS3">MS3</option>
                <option value="MS4">MS4</option><option value="MS5">MS5</option><option value="MS6">MS6</option>
                <option value="MS7">MS7</option><option value="MS8">MS8</option><option value="MS9">MS9</option>
                <option value="MS10">MS10</option><option value="MS11">MS11</option><option value="MS12">MS12</option>
                <option value="AS1">AS1</option><option value="AS2">AS2</option>
            </select>
        </div>
        <div class="field-card">
            <label>ประเภทผลิตภัณฑ์</label>
            <select id="productType" onchange="changeProduct()">
                <option value="" selected disabled>เลือกผลิตภัณฑ์</option>
                <option value="EPC">EPC</option>
                <option value="EPW">EPW</option>
            </select>
        </div>
        <div class="field-card">
            <label>ประเภทงาน</label>
            <select id="marketType" onchange="changeProduct()">
                <option value="" selected disabled>เลือกประเภทงาน</option>
                <option value="TH">งานไทย</option>
                <option value="EXPORT">งานต่างประเทศ</option>
                <option id="marketLaosOption" value="LAOS">งานต่างประเทศ ลาว</option>
            </select>
        </div>
        <div class="field-card">
            <label>วันที่ผลิต (MFG)</label>
            <input type="date" id="mfgDate" onchange="updateMFGFromDate()">
        </div>
        <input id="mfg" value="" type="hidden">
        <input id="linapackExp" value="" type="hidden">
        <div class="field-card mix-field">
            <label id="mixDateHeaderLabel">วันที่ผสม</label>
            <input type="date" id="mixDate" onchange="updateMixCodeFromDate()">
        </div>
        <div class="field-card mix-field">
            <label id="mixCodeHeaderLabel">Mix Code</label>
            <input id="mixCode" value="" placeholder="Auto เช่น 18F" readonly>
        </div>
    </div>
</div>

<div id="pouchSection" style="display:none;">
    <input id="sachetLine" value="MS11" type="hidden">
    <input id="sachetExp" value="" type="hidden">
    <p id="linapackHint" class="small full-span"></p>
</div>

<div id="cartonSection" class="section-card mobile-card carton-card-config">
    <div class="section-title">📦 ข้อมูลล็อตกล่อง</div>
    <div id="cartonTHBox" class="mobile-field-grid carton-field-grid">
        <div class="field-card">
            <label>Shipping Mark</label>
            <input value="-" readonly>
        </div>
        <div class="field-card">
            <label>Prefix</label>
            <input value="00" readonly>
        </div>
        <div class="field-card">
            <label>เลขอาคาร</label>
            <select id="buildingNo" onchange="updateExpectedLinkedLots()">
                <option value="">ไม่มี</option><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option>
                <option value="4">4</option><option value="5">5</option><option value="6">6</option>
            </select>
        </div>
        <div class="field-card">
            <label>Suffix หลังเลขอาคาร</label>
            <input id="buildingSuffixTH" value="" placeholder="เช่น N หรือ QR" oninput="updateExpectedLinkedLots()">
        </div>
    </div>

    <div id="cartonExportBox" class="mobile-field-grid carton-field-grid hidden-market">
        <div class="field-card">
            <label>Shipping Mark</label>
            <input id="shippingMark" value="" placeholder="Auto" readonly>
        </div>
        <div class="field-card">
            <label>Prefix</label>
            <select id="cartonPrefix" onchange="updateShippingMarkByPrefix()">
            <option value="" selected disabled>เลือก Prefix</option>
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
        </div>
        <div class="field-card">
            <label>เลขอาคาร</label>
            <select id="buildingNoExport" onchange="updateExpectedLinkedLots()">
                <option value="">ไม่มี</option><option value="1">1</option><option value="2">2</option><option value="3" selected>3</option>
                <option value="4">4</option><option value="5">5</option><option value="6">6</option>
            </select>
        </div>
        <div class="field-card">
            <label>Suffix หลังเลขอาคาร</label>
            <input id="buildingSuffixExport" value="" placeholder="เช่น N หรือ QR" oninput="updateExpectedLinkedLots()">
        </div>
        <input id="cartonExp" value="" type="hidden">
    </div>
</div>


<div id="autoExpInfo" class="info" style="display:none"></div>
<div id="linkedLotInfo" class="info" style="display:none"></div>

<div class="nav-row">
    
</div>
</div>

<div id="page2" class="step-page photo-grid">
    <div class="photo-card pouch-card">
        <h3>รูปที่ 1: ซอง</h3>
        <p class="small">เลือกไฟล์รูปจากโทรศัพท์ หรือกดเปิดกล้องเพื่อถ่ายรูปซอง</p>
        <input type="file" id="fileInputPouch" accept="image/*">
        <label class="static-mobile-file-btn" for="fileInputPouch">📁 เลือกไฟล์รูปซอง</label>
        <img id="previewPouch" style="display:none;">
        <span id="pouchCaptureTime" class="capture-time"></span>
    </div>

    <div class="photo-card carton-card">
        <h3>รูปที่ 2: กล่อง</h3>
        <p class="small">เลือกไฟล์รูปจากโทรศัพท์ หรือกดเปิดกล้องเพื่อถ่ายรูปกล่อง</p>
        <input type="file" id="fileInputCarton" accept="image/*">
        <label class="static-mobile-file-btn" for="fileInputCarton">📁 เลือกไฟล์รูปกล่อง</label>
        <img id="previewCarton" style="display:none;">
        <span id="cartonCaptureTime" class="capture-time"></span>
    </div>

    <div class="photo-card camera-card">
        <h3>ถ่ายจากกล้อง</h3>
        <p class="small">กดเปิดกล้องเพื่อดูภาพแบบเต็มจอ แล้วเลือกถ่ายรูปซองหรือรูปกล่อง</p>
        <button id="openCameraBtn" onclick="startCamera()">เปิดกล้อง</button>
        <canvas id="canvas" style="display:none;"></canvas>
    </div>

    <div id="cameraOverlay" class="camera-overlay" style="display:none;">
        <div class="camera-live-wrap">
            <video id="video" autoplay playsinline muted></video>
            <div class="scan-guide"></div>
        </div>
        <div class="camera-toolbar">
            <button id="capturePouchBtn" onclick="captureImage('pouch')">ถ่ายรูปซอง</button>
            <button id="captureCartonBtn" onclick="captureImage('carton')">ถ่ายรูปกล่อง</button>
            <button class="btn-secondary" onclick="stopCamera()">ปิดกล้อง</button>
        </div>
    </div>

    <div class="nav-row check-row">
        <button class="btn-secondary" onclick="goPage(1)">ย้อนกลับ</button>
        <button class="btn-success" onclick="sendCheck()">ตรวจสอบล็อตซอง + กล่อง</button>
    </div>
</div>

<div id="page3" class="step-page result-dashboard">
<div class="nav-row">
    <button class="btn-secondary" onclick="goPage(1)">ตั้งค่า</button>
    <button class="btn-secondary" onclick="goPage(2)">รูปภาพ</button>
</div>
<div id="result"></div>
<div id="detail"></div>
</div>
</div>

<div id="resultPopup" class="result-popup-overlay" onclick="closeResultPopup(event)">
    <div class="result-popup" onclick="event.stopPropagation()">
        <div id="resultPopupContent"></div>
    </div>
</div>

<script>
let pouchImageData = "";
let cartonImageData = "";
let captureTarget = "pouch";
let cameraStream = null;

let toastTimer = null;

function showToast(message, type = "success") {
    const toast = document.getElementById("captureToast");
    if (!toast) return;
    toast.className = "capture-toast" + (type ? " " + type : "");
    toast.textContent = message;
    toast.classList.add("show");
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2400);
}

function updateCaptureTime(kind) {
    const now = new Date();
    const timeText = now.toLocaleTimeString("th-TH", { hour12:false });
    const el = document.getElementById(kind === "carton" ? "cartonCaptureTime" : "pouchCaptureTime");
    if (el) el.textContent = "บันทึกล่าสุด: " + timeText;
}

function closeResultPopup(event) {
    const popup = document.getElementById("resultPopup");
    if (popup) popup.classList.remove("show");
}

let latestResultPopupHtml = "";
let latestShareResultText = "PASS";
let latestShareMachine = "-";


function openResultPopup(html) {
    const popup = document.getElementById("resultPopup");
    const content = document.getElementById("resultPopupContent");
    if (content) content.innerHTML = html;
    if (popup) popup.classList.add("show");
}

function reopenLatestResultPopup() {
    if (latestResultPopupHtml) {
        openResultPopup(latestResultPopupHtml);
    } else {
        alert("ยังไม่มีผลตรวจล่าสุด");
    }
}


function formatShareDateTime() {
    const now = new Date();
    const dd = String(now.getDate()).padStart(2, "0");
    const mm = String(now.getMonth() + 1).padStart(2, "0");
    const yyyy = now.getFullYear();
    const hh = String(now.getHours()).padStart(2, "0");
    const mi = String(now.getMinutes()).padStart(2, "0");
    const ss = String(now.getSeconds()).padStart(2, "0");
    return `${dd}/${mm}/${yyyy} ${hh}:${mi}:${ss}`;
}

function getShareMessage() {
    const machineEl = document.getElementById("lpMachine");
    const machine = (machineEl?.value || latestShareMachine || "-").trim();
    const resultText = (latestShareResultText || "-").toUpperCase();
    return `ไลน์ ${machine} ตรวจสอบความถูกต้องของ Lot แล้ว (${resultText})

วันที่ ${formatShareDateTime()}`;
}

async function shareResultImage(imageUrl) {
    if (!imageUrl) {
        alert("ยังไม่มีรูปผลตรวจสำหรับแชร์");
        return;
    }

    try {
        const absoluteUrl = new URL(imageUrl, window.location.href).href;
        const response = await fetch(absoluteUrl, { cache: "no-store" });
        if (!response.ok) throw new Error("โหลดรูปไม่สำเร็จ");

        const blob = await response.blob();
        const file = new File([blob], "Lot_Check_Result.jpg", { type: blob.type || "image/jpeg" });
        const shareText = getShareMessage();

        if (navigator.canShare && navigator.canShare({ files: [file] }) && navigator.share) {
            await navigator.share({
                title: "IP ONE Lot Check Result",
                text: shareText,
                files: [file]
            });
            return;
        }

        if (navigator.share) {
            await navigator.share({
                title: "IP ONE Lot Check Result",
                text: shareText,
                url: absoluteUrl
            });
            return;
        }

        const a = document.createElement("a");
        a.href = absoluteUrl;
        a.download = "Lot_Check_Result.jpg";
        document.body.appendChild(a);
        a.click();
        a.remove();
        alert("เครื่องนี้ไม่รองรับการแชร์ตรงไปยัง LINE ระบบจึงดาวน์โหลดรูปให้แทน\n\n" + shareText);
    } catch (err) {
        alert("แชร์รูปไม่สำเร็จ: " + err.message);
    }
}


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
        const line = document.getElementById("lpMachine").value.trim().toUpperCase() || "MS1";
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

function setMachineOptionsForMode(mode) {
    const machineSelect = document.getElementById("lpMachine");
    if (!machineSelect) return;
    const current = machineSelect.value;
    const options = mode === "sachet"
        ? ["MS1","MS2","MS3","MS4","MS5","MS6","MS7","MS8","MS9","MS10","MS11","MS12","AS1","AS2"]
        : ["LP1","LP2","LP3","LP4","LP5","LP6","LP7","LP8","LP9"];
    machineSelect.innerHTML = options.map(v => `<option value="${v}">${v}</option>`).join("");
    if (options.includes(current)) machineSelect.value = current;
    else machineSelect.value = mode === "sachet" ? "MS11" : "LP7";
    const sachetLine = document.getElementById("sachetLine");
    if (sachetLine && mode === "sachet") sachetLine.value = machineSelect.value;
}

function changeMode() {
    const mode = document.getElementById("mode").value;
    setMachineOptionsForMode(mode);
    const lpLabel = document.getElementById("machineHeaderLabel");
    if (lpLabel) lpLabel.innerText = mode === "sachet" ? "เครื่อง Sachet" : "เครื่อง Linapack";
    changeProduct();
}

function changeProduct() {
    const product = document.getElementById("productType").value;
    const market = document.getElementById("marketType").value;
    const mode = document.getElementById("mode").value;

    const mixDate = document.getElementById("mixDate");
    const mixCode = document.getElementById("mixCode");
    const mixDateLabel = document.getElementById("mixDateHeaderLabel");
    const mixCodeLabel = document.getElementById("mixCodeHeaderLabel");
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

    // แสดงวันผสมเฉพาะกรณีที่ต้องใช้จริงเท่านั้น
    // EPC ไม่ต้องแสดงช่องวันที่ผสม / Mix Code เด็ดขาด
    const needMix = (product === "EPW" && (market === "TH" || market === "LAOS"));
    [mixDate, mixCode, mixDateLabel, mixCodeLabel].forEach(el => { if (el) el.classList.toggle("hidden-field", !needMix); });
    document.querySelectorAll(".mix-field").forEach(el => el.classList.toggle("hidden-field", !needMix));
    if (!needMix) {
        if (mixDate) mixDate.value = "";
        if (mixCode) mixCode.value = "";
    }

    const isThaiMarket = market === "TH";
    const isExportMarket = (market === "EXPORT" || market === "LAOS");

    cartonTHBox.classList.toggle("hidden-market", !isThaiMarket);
    cartonExportBox.classList.toggle("hidden-market", !isExportMarket);

    // งานไทย: Prefix บังคับเป็น 00 และไม่แสดงตัวเลือก Prefix ต่างประเทศ
    // งานต่างประเทศ/ลาว: แสดง Prefix ต่างประเทศ และระบบเติม Shipping Mark อัตโนมัติ
    if (isExportMarket) updateShippingMarkByPrefix();
    else updateExpectedLinkedLots();

    if (mode === "linapack") {
        const needMix = (product === "EPW" && (market === "TH" || market === "LAOS"));
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
    const isCarton = kind === "carton";
    const preview = document.getElementById(isCarton ? "previewCarton" : "previewPouch");
    if (!preview) return;

    if (isCarton) {
        cartonImageData = dataUrl;
        updateCaptureTime("carton");
    } else {
        pouchImageData = dataUrl;
        updateCaptureTime("pouch");
    }

    preview.src = dataUrl;
    preview.classList.add("has-image");
    preview.removeAttribute("hidden");
    preview.style.setProperty("display", "block", "important");

    const card = preview.closest(".photo-card");
    if (card) {
        card.querySelectorAll(".static-upload-placeholder,.upload-placeholder").forEach(function(el){
            el.style.setProperty("display", "none", "important");
        });
    }
}

function setCaptureTarget(kind) {
    captureTarget = kind === "carton" ? "carton" : "pouch";
}

document.getElementById("fileInputPouch").addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) { setImage("pouch", event.target.result); showToast("✅ เลือกรูปซองจากเครื่องเรียบร้อย"); };
    reader.readAsDataURL(file);
});

document.getElementById("fileInputCarton").addEventListener("change", function(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(event) { setImage("carton", event.target.result); showToast("✅ เลือกรูปกล่องจากเครื่องเรียบร้อย"); };
    reader.readAsDataURL(file);
});

async function startCamera() {
    try {
        const video = document.getElementById("video");
        const cameraCard = document.querySelector(".camera-card");
        const cameraOverlay = document.getElementById("cameraOverlay");
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Browser นี้ไม่รองรับการเปิดกล้อง หรือไม่ได้เปิดผ่าน HTTPS/localhost");
        }
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        const constraints = {
            audio: false,
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };
        cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = cameraStream;
        await video.play();
        if (cameraCard) cameraCard.classList.add("camera-active");
        if (cameraOverlay) cameraOverlay.classList.add("show");
    } catch (err) {
        document.getElementById("result").innerHTML = '<div class="ng">เปิดกล้องไม่ได้</div><p>' + err + '</p>';
    }
}

function stopCamera() {
    const video = document.getElementById("video");
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    if (video) video.srcObject = null;
    const cameraCard = document.querySelector(".camera-card");
    const cameraOverlay = document.getElementById("cameraOverlay");
    if (cameraCard) cameraCard.classList.remove("camera-active");
    if (cameraOverlay) cameraOverlay.classList.remove("show");
}

function captureImage(kind) {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const target = kind === "carton" ? "carton" : "pouch";

    if (!video.videoWidth) {
        document.getElementById("result").innerHTML = '<div class="ng">กรุณาเปิดกล้องก่อน</div>';
        showToast("กรุณาเปิดกล้องก่อน", "error");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const captured = canvas.toDataURL("image/jpeg", 0.92);
    setImage(target, captured);
    showToast(target === "carton" ? "✅ บันทึกรูปกล่องเรียบร้อย" : "✅ บันทึกรูปซองเรียบร้อย");
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
        payload.line = document.getElementById("lpMachine").value;
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

        const pass = data.summary === "PASS";
        latestShareResultText = pass ? "PASS" : "NG";
        latestShareMachine = (document.getElementById("lpMachine")?.value || payload.line || "-").trim();
        resultDiv.innerHTML = `
            <div class="result-hero">
                <div class="result-status-card ${pass ? 'pass-card' : 'ng-card'}">
                    <div class="result-title ${pass ? 'pass-text' : 'ng-text'}">${pass ? 'PASS ✅' : 'NG ❌'}</div>
                    <p class="result-subtitle">${pass ? 'ตรวจสอบล็อตซองและกล่องผ่าน' : 'พบข้อมูลไม่ตรงตามเงื่อนไข'}</p>
                </div>
                <div class="result-meta-card">
                    <div class="result-meta-grid">
                        <div class="meta-item"><div class="meta-label">เวลา</div><div class="meta-value">${data.time || '-'}</div></div>
                        <div class="meta-item"><div class="meta-label">โหมด</div><div class="meta-value">${data.checkType || '-'}</div></div>
                        <div class="meta-item"><div class="meta-label">ประเภทงาน</div><div class="meta-value">${data.marketType || '-'}</div></div>
                        <div class="meta-item"><div class="meta-label">Expected EXP</div><div class="meta-value">${data.expectedExp || '-'}</div></div>
                    </div>
                </div>
            </div>
        `;

        const ngRows = (data.details || []).filter(row => row.status === "NG");
        let ngHtml = "";
        if (ngRows.length === 0) {
            ngHtml = `<div class="result-popup-ok-box">✓ ไม่พบรายการ NG</div>`;
        } else {
            ngHtml = `<div class="result-popup-ng-box"><div class="result-section-title">รายการที่ NG</div>`;
            ngHtml += `<table><tr><th>รายการ NG</th><th>อ่านได้</th><th>ค่าที่ควรเป็น</th></tr>`;
            ngRows.forEach(row => {
                ngHtml += `<tr><td>${row.item}</td><td>${row.actual}</td><td>${row.expected}</td></tr>`;
            });
            ngHtml += `</table></div>`;
        }

        const popupHtml = `
            <div class="result-popup-header ${pass ? 'popup-pass' : 'popup-ng'}">
                <div>
                    <div class="result-popup-title">${pass ? 'PASS ✅' : 'NG ❌'}</div>
                    <div class="result-popup-subtitle">${pass ? 'ตรวจสอบล็อตซองและกล่องผ่าน' : 'พบข้อมูลไม่ตรงตามเงื่อนไข'} | ${data.time || '-'}</div>
                </div>
                <button class="result-popup-close" onclick="closeResultPopup(event)">×</button>
            </div>
            <div class="result-popup-body">
                <div class="result-popup-meta">
                    <div class="meta-item"><div class="meta-label">โหมด</div><div class="meta-value">${data.checkType || '-'}</div></div>
                    <div class="meta-item"><div class="meta-label">ประเภทงาน</div><div class="meta-value">${data.marketType || '-'}</div></div>
                    <div class="meta-item"><div class="meta-label">Expected EXP</div><div class="meta-value">${data.expectedExp || '-'}</div></div>
                    <div class="meta-item"><div class="meta-label">เวลา</div><div class="meta-value">${data.time || '-'}</div></div>
                </div>
                <div class="result-popup-image-wrap">
                    ${data.stampedImageUrl ? `<img src="${data.stampedImageUrl}">` : `<div class="warn">ไม่มีรูปแสตมป์</div>`}
                </div>
                <div class="result-popup-bottom">
                    ${data.expectedPouchLot ? `<div class="result-popup-lot-box"><div class="result-popup-lot-title">Lot ซองที่ควรเป็น</div><div class="result-popup-lot-value">${data.expectedPouchLot}</div></div>` : ``}
                    ${data.expectedCartonLot ? `<div class="result-popup-lot-box"><div class="result-popup-lot-title">Lot กล่องที่ควรเป็น</div><div class="result-popup-lot-value">${data.expectedCartonLot}</div></div>` : ``}
                    ${ngHtml}
                </div>
                ${data.stampedImageUrl ? `<div class="result-popup-actions"><button class="download" type="button" onclick="shareResultImage('${data.stampedImageUrl}')" style="background:#06c755;">แชร์รูปเข้า LINE / แอปอื่น</button><a class="download" href="${data.stampedImageUrl}" target="_blank">เปิดรูป</a><a class="download" href="${data.stampedImageUrl}" download="Lot_Check_Result.jpg" style="background:#16a34a;">ดาวน์โหลดรูป</a></div>` : ``}
                <div class="result-json"><details><summary>AI อ่านได้ทั้งหมด</summary><pre>${JSON.stringify(data.lines, null, 2)}</pre></details></div>
            </div>`;
        latestResultPopupHtml = popupHtml;
        openResultPopup(popupHtml);

        detailDiv.innerHTML = `
            <div class="result-clean-card ${pass ? 'result-clean-pass' : 'result-clean-ng'}">
                <div class="result-clean-title">${pass ? 'PASS ✅' : 'NG ❌'}</div>
                <div class="result-clean-subtitle">${pass ? 'ตรวจสอบล็อตซองและกล่องผ่าน' : 'พบข้อมูลไม่ตรงตามเงื่อนไข'}</div>
                <button type="button" onclick="reopenLatestResultPopup()" class="btn-success result-reopen-btn">เปิดผลตรวจอีกครั้ง</button>
            </div>
        `;

    } catch (err) {
        resultDiv.innerHTML = `<div class="ng">ERROR</div><p>${err}</p>`;
    }
}

window.onload = function() {
    setTodayDefault();
    updateShippingMarkByPrefix();
    changeCheckType();
    changeMode();
    updateExpectedLinkedLots();
    goPage(1);
};


function fixLotHeaderColumns() {
    const grid = document.querySelector('#pouchHeader .config-grid');
    if (!grid) return;
    const labels = Array.from(grid.querySelectorAll('label')).filter(el => !el.classList.contains('hidden-field') && getComputedStyle(el).display !== 'none');
    const count = Math.max(1, labels.length);
    grid.style.setProperty('--lot-cols', count);
}

const _oldChangeMode = changeMode;
changeMode = function() {
    _oldChangeMode();
    fixLotHeaderColumns();
};

const _oldChangeProduct = changeProduct;
changeProduct = function() {
    _oldChangeProduct();
    fixLotHeaderColumns();
};

window.addEventListener('load', () => {
    fixLotHeaderColumns();
});

</script>

<script>
(function(){
  function directChildren(el, selector){
    return Array.prototype.filter.call(el.children, function(n){ return n.matches && n.matches(selector); });
  }
  function polishConfigGrid(grid){
    if(!grid || grid.dataset.polishedMobile === '1') return;
    var labels = directChildren(grid, 'label');
    if(!labels.length) return;
    var controls = directChildren(grid, 'input:not([type="hidden"]), select, textarea');
    if(!controls.length) return;
    var others = Array.prototype.filter.call(grid.children, function(n){
      return labels.indexOf(n) === -1 && controls.indexOf(n) === -1;
    });
    var frag = document.createDocumentFragment();
    var count = Math.min(labels.length, controls.length);
    for(var i=0;i<count;i++){
      var wrap = document.createElement('div');
      wrap.className = 'mobile-field';
      wrap.appendChild(labels[i]);
      wrap.appendChild(controls[i]);
      frag.appendChild(wrap);
    }
    for(var j=count;j<labels.length;j++) frag.appendChild(labels[j]);
    for(var k=count;k<controls.length;k++) frag.appendChild(controls[k]);
    others.forEach(function(n){ frag.appendChild(n); });
    grid.appendChild(frag);
    grid.dataset.polishedMobile = '1';
  }
  function addUploadUI(inputId, labelText){
    var input = document.getElementById(inputId);
    if(!input || input.dataset.mobileUpload === '1') return;
    input.dataset.mobileUpload = '1';
    var ph = document.createElement('div');
    ph.className = 'upload-placeholder';
    input.parentNode.insertBefore(ph, input.nextSibling);
    var lab = document.createElement('label');
    lab.className = 'mobile-file-btn';
    lab.htmlFor = input.id;
    lab.textContent = labelText;
    input.parentNode.insertBefore(lab, ph.nextSibling);
    input.addEventListener('change', function(){ ph.style.display='none'; });
  }
  function addBottomNav(){
    if(document.querySelector('.mobile-bottom-nav')) return;
    var nav=document.createElement('div');
    nav.className='mobile-bottom-nav';
    nav.innerHTML='<button type="button" onclick="window.scrollTo({top:0,behavior:\'smooth\'})"><span class="nav-ico">🏠</span><span>ตรวจล็อต</span></button><button type="button" onclick="document.getElementById(\'page2\').scrollIntoView({behavior:\'smooth\'})"><span class="nav-ico">📷</span><span>รูปภาพ</span></button><button type="button" onclick="sendCheck()"><span class="nav-ico">🔍</span><span>ตรวจ</span></button><button type="button" onclick="document.getElementById(\'pouchHeader\').scrollIntoView({behavior:\'smooth\'})"><span class="nav-ico">⚙️</span><span>ตั้งค่า</span></button>';
    document.body.appendChild(nav);
  }
  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('.config-grid').forEach(polishConfigGrid);
    addUploadUI('fileInputPouch','เลือกไฟล์ / เปิดกล้อง');
    addUploadUI('fileInputCarton','เลือกไฟล์ / เปิดกล้อง');
    addBottomNav();
  });
})();
</script>


<script>
(function(){
  function hideStatic(inputId){
    var input=document.getElementById(inputId);
    if(!input) return;
    input.addEventListener('change', function(){
      var card=input.closest('.photo-card');
      if(!card) return;
      card.querySelectorAll('.static-upload-placeholder,.upload-placeholder').forEach(function(el){el.style.display='none';});
    });
  }
  document.addEventListener('DOMContentLoaded', function(){hideStatic('fileInputPouch');hideStatic('fileInputCarton');});
})();
</script>


<script>
(function(){
  function productNeedsMix(){
    const p = document.getElementById('productType');
    const m = document.getElementById('marketType');
    if(!p || !m) return false;
    return p.value === 'EPW' && (m.value === 'TH' || m.value === 'LAOS');
  }
  function hardApplyMixVisibility(){
    const need = productNeedsMix();
    document.body.classList.toggle('product-epc', !need);

    document.querySelectorAll('.mix-field, #mixDate, #mixCode, #mixDateHeaderLabel, #mixCodeHeaderLabel').forEach(function(el){
      if(!el) return;
      el.classList.toggle('force-hidden', !need);
      el.classList.toggle('hidden-field', !need);
      el.style.setProperty('display', need ? '' : 'none', 'important');
      if(!need && (el.id === 'mixDate' || el.id === 'mixCode')) el.value = '';
    });

    // If some mobile-polish script wrapped these fields, hide the wrapper too.
    ['mixDate','mixCode','mixDateHeaderLabel','mixCodeHeaderLabel'].forEach(function(id){
      const el = document.getElementById(id);
      if(!el) return;
      const wrap = el.closest('.mobile-field, .field-card, .mix-field');
      if(wrap){
        wrap.classList.toggle('force-hidden', !need);
        wrap.style.setProperty('display', need ? '' : 'none', 'important');
      }
    });

    if(typeof fixLotHeaderColumns === 'function') {
      try { fixLotHeaderColumns(); } catch(e) {}
    }
  }

  window.hardApplyMixVisibility = hardApplyMixVisibility;

  document.addEventListener('DOMContentLoaded', function(){
    ['productType','marketType','mode'].forEach(function(id){
      const el = document.getElementById(id);
      if(el) el.addEventListener('change', function(){ setTimeout(hardApplyMixVisibility, 0); setTimeout(hardApplyMixVisibility, 80); });
    });
    hardApplyMixVisibility();
    setTimeout(hardApplyMixVisibility, 100);
    setTimeout(hardApplyMixVisibility, 500);
  });

  const oldChangeProduct = window.changeProduct;
  window.changeProduct = function(){
    if(typeof oldChangeProduct === 'function') oldChangeProduct.apply(this, arguments);
    hardApplyMixVisibility();
    setTimeout(hardApplyMixVisibility, 50);
  };
})();
</script>



<script>
/* ===== FINAL FIX: line machine options + carton prefix by market ===== */
(function(){
  const SACHET_MACHINES = ["MS1","MS2","MS3","MS4","MS5","MS6","MS7","MS8","MS9","MS10","MS11","MS12","AS1","AS2"];
  const LINAPACK_MACHINES = ["LP1","LP2","LP3","LP4","LP5","LP6","LP7","LP8","LP9"];

  function setOptions(select, options, fallback){
    if(!select) return;
    const current = (select.value || '').trim().toUpperCase();
    select.innerHTML = options.map(v => `<option value="${v}">${v}</option>`).join('');
    select.value = options.includes(current) ? current : fallback;
  }

  function finalApplyLineMachine(){
    const mode = document.getElementById('mode')?.value || 'sachet';
    const machine = document.getElementById('lpMachine');
    const label = document.getElementById('machineHeaderLabel');
    if(mode === 'sachet'){
      setOptions(machine, SACHET_MACHINES, 'MS11');
      if(label) label.textContent = 'เครื่อง Sachet';
      const sachetLine = document.getElementById('sachetLine');
      if(sachetLine && machine) sachetLine.value = machine.value;
    }else{
      setOptions(machine, LINAPACK_MACHINES, 'LP7');
      if(label) label.textContent = 'เครื่อง Linapack';
    }
  }

  function finalApplyCartonMarket(){
    const market = document.getElementById('marketType')?.value || 'TH';
    const thBox = document.getElementById('cartonTHBox');
    const exportBox = document.getElementById('cartonExportBox');
    const prefix = document.getElementById('cartonPrefix');
    const shipping = document.getElementById('shippingMark');
    const isExport = market === 'EXPORT' || market === 'LAOS';

    if(thBox){
      thBox.classList.toggle('hidden-market', isExport);
      thBox.style.setProperty('display', isExport ? 'none' : 'grid', 'important');
    }
    if(exportBox){
      exportBox.classList.toggle('hidden-market', !isExport);
      exportBox.style.setProperty('display', isExport ? 'grid' : 'none', 'important');
    }
    if(prefix){
      prefix.disabled = !isExport ? true : false;
      if(isExport){
        prefix.removeAttribute('disabled');
        prefix.style.pointerEvents = 'auto';
        prefix.style.opacity = '1';
      }
    }
    if(isExport && typeof updateShippingMarkByPrefix === 'function'){
      try { updateShippingMarkByPrefix(); } catch(e) {}
    }else if(!isExport && shipping){
      shipping.value = '-';
    }
  }

  function finalApplyAll(){
    finalApplyLineMachine();
    finalApplyCartonMarket();
    if(typeof autoExp === 'function') { try { autoExp(); } catch(e) {} }
    if(typeof updateExpectedLinkedLots === 'function') { try { updateExpectedLinkedLots(); } catch(e) {} }
    if(typeof hardApplyMixVisibility === 'function') { try { hardApplyMixVisibility(); } catch(e) {} }
  }

  // Override after all old scripts so no earlier script can force LP list or hide export prefix.
  window.finalApplyLineMachine = finalApplyLineMachine;
  window.finalApplyCartonMarket = finalApplyCartonMarket;
  window.finalApplyAll = finalApplyAll;

  const oldChangeMode = window.changeMode;
  window.changeMode = function(){
    if(typeof oldChangeMode === 'function') { try { oldChangeMode.apply(this, arguments); } catch(e) {} }
    finalApplyAll();
    setTimeout(finalApplyAll, 50);
  };

  const oldChangeProduct = window.changeProduct;
  window.changeProduct = function(){
    if(typeof oldChangeProduct === 'function') { try { oldChangeProduct.apply(this, arguments); } catch(e) {} }
    finalApplyAll();
    setTimeout(finalApplyAll, 50);
  };

  document.addEventListener('DOMContentLoaded', function(){
    ['mode','lpMachine','marketType','productType','cartonPrefix','buildingNo','buildingNoExport','buildingSuffixTH','buildingSuffixExport'].forEach(function(id){
      const el = document.getElementById(id);
      if(el) el.addEventListener('change', function(){ setTimeout(finalApplyAll, 0); setTimeout(finalApplyAll, 80); });
    });
    finalApplyAll();
    setTimeout(finalApplyAll, 100);
    setTimeout(finalApplyAll, 500);
  });
})();
</script>



<style>
/* ===== FINAL HOTFIX: mobile field visibility / date alignment / upload preview ===== */
input[type="date"]{
    min-height:46px !important;
    height:46px !important;
    line-height:46px !important;
    padding-top:0 !important;
    padding-bottom:0 !important;
    font-size:16px !important;
}
select, input{
    min-height:44px !important;
}
#previewPouch:not(.has-image), #previewCarton:not(.has-image){
    display:none !important;
}
#previewPouch.has-image, #previewCarton.has-image{
    display:block !important;
    width:100% !important;
    max-height:360px !important;
    object-fit:contain !important;
    margin-top:10px !important;
}
@media (max-width: 768px){
    #page1, #page2, #page3,
    .mobile-field-grid, .setup-field-grid, .carton-field-grid,
    #cartonTHBox, #cartonExportBox{
        display:grid !important;
        grid-template-columns:1fr !important;
        width:100% !important;
        max-width:100% !important;
        overflow:visible !important;
    }
    .field-card, .photo-card, .mobile-card, .section-card{
        width:100% !important;
        max-width:100% !important;
        overflow:visible !important;
    }
    select, input, button, .static-mobile-file-btn{
        width:100% !important;
        max-width:100% !important;
        box-sizing:border-box !important;
    }
}
</style>

<script>
/* ===== FINAL HOTFIX: blank defaults, upload/camera, shipping mark ===== */
(function(){
  const SACHET_MACHINES_FINAL = ["MS1","MS2","MS3","MS4","MS5","MS6","MS7","MS8","MS9","MS10","MS11","MS12","AS1","AS2"];
  const LINAPACK_MACHINES_FINAL = ["LP1","LP2","LP3","LP4","LP5","LP6","LP7","LP8","LP9"];

  function fillSelect(select, options, placeholder){
    if(!select) return;
    const current = (select.value || '').trim().toUpperCase();
    select.innerHTML = `<option value="" selected disabled>${placeholder}</option>` + options.map(v=>`<option value="${v}">${v}</option>`).join('');
    if(options.includes(current)) select.value = current;
    else select.value = '';
  }

  function applyMachineByModeFinal(){
    const modeEl = document.getElementById('mode');
    const machine = document.getElementById('lpMachine');
    const label = document.getElementById('machineHeaderLabel');
    const mode = modeEl ? modeEl.value : '';
    if(label) label.textContent = mode === 'sachet' ? 'เครื่อง Sachet' : (mode === 'linapack' ? 'เครื่อง Linapack' : 'เครื่อง');
    if(!mode){
      fillSelect(machine, [], 'เลือกประเภทไลน์ก่อน');
      return;
    }
    fillSelect(machine, mode === 'sachet' ? SACHET_MACHINES_FINAL : LINAPACK_MACHINES_FINAL, 'เลือกเครื่อง');
  }

  function applyCartonMarketFinal(){
    const market = document.getElementById('marketType')?.value || '';
    const thBox = document.getElementById('cartonTHBox');
    const exportBox = document.getElementById('cartonExportBox');
    const prefix = document.getElementById('cartonPrefix');
    const shipping = document.getElementById('shippingMark');
    const isExport = market === 'EXPORT' || market === 'LAOS';
    const isTH = market === 'TH';
    if(thBox) thBox.style.setProperty('display', isTH ? 'grid' : 'none', 'important');
    if(exportBox) exportBox.style.setProperty('display', isExport ? 'grid' : 'none', 'important');
    if(prefix){
      prefix.disabled = !isExport;
      prefix.style.pointerEvents = isExport ? 'auto' : 'none';
      prefix.style.opacity = isExport ? '1' : '.75';
      if(!isExport) prefix.value = '';
    }
    if(shipping && !isExport) shipping.value = '-';
    if(isExport && shipping && prefix && prefix.value && typeof PREFIX_SHIPPING_MAP !== 'undefined'){
      shipping.value = PREFIX_SHIPPING_MAP[prefix.value] || '';
    }
  }

  function applyBlankDefaultsOnce(){
    ['mode','productType','marketType','lpMachine','cartonPrefix'].forEach(id=>{
      const el=document.getElementById(id);
      if(el) el.value='';
    });
    applyMachineByModeFinal();
    applyCartonMarketFinal();
    if(typeof hardApplyMixVisibility === 'function') try{hardApplyMixVisibility();}catch(e){}
  }

  function robustSetImage(kind, dataUrl){
    if(kind === 'carton') window.cartonImageData = dataUrl;
    else window.pouchImageData = dataUrl;
    // Also update lexical variables when available in this script scope.
    try { if(kind === 'carton') cartonImageData = dataUrl; else pouchImageData = dataUrl; } catch(e) {}
    const preview = document.getElementById(kind === 'carton' ? 'previewCarton' : 'previewPouch');
    if(preview){
      preview.onload = function(){
        preview.classList.add('has-image');
        preview.style.setProperty('display','block','important');
      };
      preview.src = dataUrl;
      preview.classList.add('has-image');
      preview.removeAttribute('hidden');
      preview.style.setProperty('display','block','important');
    }
    if(typeof updateCaptureTime === 'function') try{updateCaptureTime(kind);}catch(e){}
  }
  window.setImage = robustSetImage;

  function attachFile(id, kind){
    const input = document.getElementById(id);
    if(!input) return;
    input.removeAttribute('capture');
    input.setAttribute('accept','image/*');
    input.onchange = function(e){
      const file = e.target.files && e.target.files[0];
      if(!file) return;
      const reader = new FileReader();
      reader.onload = function(ev){
        robustSetImage(kind, ev.target.result);
        if(typeof showToast === 'function') showToast(kind === 'carton' ? '✅ เลือกรูปกล่องจากเครื่องเรียบร้อย' : '✅ เลือกรูปซองจากเครื่องเรียบร้อย');
      };
      reader.onerror = function(){ if(typeof showToast === 'function') showToast('อ่านไฟล์รูปไม่สำเร็จ','error'); };
      reader.readAsDataURL(file);
    };
  }

  window.updateShippingMarkByPrefix = function(){
    const prefix = document.getElementById('cartonPrefix');
    const shipping = document.getElementById('shippingMark');
    if(!prefix || !shipping) return;
    if(prefix.value === 'CUSTOM'){
      shipping.readOnly = false;
      shipping.value = '';
      shipping.placeholder = 'กรอก Shipping Mark เอง';
      return;
    }
    shipping.readOnly = true;
    shipping.value = (typeof PREFIX_SHIPPING_MAP !== 'undefined' ? (PREFIX_SHIPPING_MAP[prefix.value] || '') : '');
    if(typeof updateExpectedLinkedLots === 'function') try{ updateExpectedLinkedLots(); }catch(e){}
  };

  const originalStart = window.startCamera;
  window.startCamera = async function(){
    try{
      const video = document.getElementById('video');
      const overlay = document.getElementById('cameraOverlay');
      if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error('Browser นี้ไม่รองรับกล้อง หรือไม่ได้เปิดผ่าน HTTPS/localhost');
      try { if(window.cameraStream) window.cameraStream.getTracks().forEach(t=>t.stop()); } catch(e) {}
      try { if(typeof cameraStream !== 'undefined' && cameraStream) cameraStream.getTracks().forEach(t=>t.stop()); } catch(e) {}
      const stream = await navigator.mediaDevices.getUserMedia({audio:false, video:{facingMode:{ideal:'environment'}, width:{ideal:1920}, height:{ideal:1080}}});
      window.cameraStream = stream;
      try { cameraStream = stream; } catch(e) {}
      video.srcObject = stream;
      await video.play();
      if(overlay) overlay.classList.add('show');
      document.querySelector('.camera-card')?.classList.add('camera-active');
      if(typeof showToast === 'function') showToast('เปิดกล้องเรียบร้อย');
    }catch(err){
      if(typeof showToast === 'function') showToast('เปิดกล้องไม่ได้: '+err.message, 'error');
      else alert('เปิดกล้องไม่ได้: '+err.message);
    }
  };

  const originalStop = window.stopCamera;
  window.stopCamera = function(){
    try { if(window.cameraStream) window.cameraStream.getTracks().forEach(t=>t.stop()); } catch(e) {}
    try { if(typeof cameraStream !== 'undefined' && cameraStream) cameraStream.getTracks().forEach(t=>t.stop()); } catch(e) {}
    window.cameraStream = null;
    try { cameraStream = null; } catch(e) {}
    const video=document.getElementById('video');
    if(video) video.srcObject = null;
    document.getElementById('cameraOverlay')?.classList.remove('show');
    document.querySelector('.camera-card')?.classList.remove('camera-active');
  };

  window.captureImage = function(kind){
    const target = kind === 'carton' ? 'carton' : 'pouch';
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    if(!video || !canvas || !video.videoWidth){
      if(typeof showToast === 'function') showToast('กรุณาเปิดกล้องก่อน', 'error');
      return;
    }
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    robustSetImage(target, canvas.toDataURL('image/jpeg', 0.92));
    if(typeof showToast === 'function') showToast(target === 'carton' ? '✅ บันทึกรูปกล่องเรียบร้อย' : '✅ บันทึกรูปซองเรียบร้อย');
  };

  function validateRequiredBeforeCheck(){
    const missing = [];
    const mode = document.getElementById('mode')?.value;
    const machine = document.getElementById('lpMachine')?.value;
    const product = document.getElementById('productType')?.value;
    const market = document.getElementById('marketType')?.value;
    if(!mode) missing.push('ประเภทไลน์');
    if(!machine) missing.push('เครื่อง');
    if(!product) missing.push('ประเภทผลิตภัณฑ์');
    if(!market) missing.push('ประเภทงาน');
    if(market === 'EXPORT' || market === 'LAOS'){
      if(!document.getElementById('cartonPrefix')?.value) missing.push('Prefix');
    }
    if(missing.length){
      if(typeof showToast === 'function') showToast('กรุณาเลือก: '+missing.join(', '), 'error');
      else alert('กรุณาเลือก: '+missing.join(', '));
      return false;
    }
    return true;
  }
  const oldSendCheck = window.sendCheck;
  window.sendCheck = async function(){
    if(!validateRequiredBeforeCheck()) return;
    return oldSendCheck.apply(this, arguments);
  };

  document.addEventListener('DOMContentLoaded', function(){
    attachFile('fileInputPouch','pouch');
    attachFile('fileInputCarton','carton');
    const mode=document.getElementById('mode');
    const market=document.getElementById('marketType');
    const prefix=document.getElementById('cartonPrefix');
    if(mode) mode.addEventListener('change', function(){ applyMachineByModeFinal(); if(typeof updateExpectedLinkedLots==='function') updateExpectedLinkedLots(); });
    if(market) market.addEventListener('change', function(){ applyCartonMarketFinal(); if(typeof updateExpectedLinkedLots==='function') updateExpectedLinkedLots(); });
    if(prefix) prefix.addEventListener('change', function(){ window.updateShippingMarkByPrefix(); });
  });

  window.addEventListener('load', function(){
    // Old scripts set default selections on load; clear only requested dropdowns after them.
    setTimeout(applyBlankDefaultsOnce, 0);
    setTimeout(applyBlankDefaultsOnce, 150);
    setTimeout(applyBlankDefaultsOnce, 600);
  });
})();
</script>



<style>
/* ===== FINAL PATCH 2026-06-24: prevent mobile date overflow and align date fields ===== */
.field-card input[type="date"],
.mobile-field input[type="date"],
input[type="date"]{
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    height:44px !important;
    min-height:44px !important;
    line-height:44px !important;
    padding:0 12px !important;
    box-sizing:border-box !important;
    vertical-align:middle !important;
    font-size:15px !important;
    -webkit-appearance:none !important;
    appearance:none !important;
}
.field-card select,
.field-card input,
.mobile-field select,
.mobile-field input{
    width:100% !important;
    max-width:100% !important;
    min-width:0 !important;
    box-sizing:border-box !important;
}
</style>

<script>
/* ===== FINAL PATCH: machine defaults after line selection, export prefix, and reliable check button ===== */
(function(){
  const SACHET_LIST = ["MS1","MS2","MS3","MS4","MS5","MS6","MS7","MS8","MS9","MS10","MS11","MS12","AS1","AS2"];
  const LP_LIST = ["LP1","LP2","LP3","LP4","LP5","LP6","LP7","LP8","LP9"];

  function optHtml(list, placeholder){
    return `<option value="" disabled>${placeholder}</option>` + list.map(v=>`<option value="${v}">${v}</option>`).join("");
  }

  function setMachineList(forceDefault){
    const mode = document.getElementById('mode')?.value || '';
    const machine = document.getElementById('lpMachine');
    const label = document.getElementById('machineHeaderLabel');
    if(!machine) return;

    const old = (machine.value || '').trim().toUpperCase();
    if(!mode){
      machine.innerHTML = `<option value="" selected disabled>เลือกประเภทไลน์ก่อน</option>`;
      if(label) label.textContent = 'เครื่อง';
      return;
    }

    const list = mode === 'sachet' ? SACHET_LIST : LP_LIST;
    const fallback = mode === 'sachet' ? 'MS11' : 'LP7';
    machine.innerHTML = optHtml(list, 'เลือกเครื่อง');
    if(list.includes(old)) machine.value = old;
    else machine.value = forceDefault ? fallback : fallback;
    if(label) label.textContent = mode === 'sachet' ? 'เครื่อง Sachet' : 'เครื่อง Linapack';

    const sachetLine = document.getElementById('sachetLine');
    if(sachetLine && mode === 'sachet') sachetLine.value = machine.value;
  }

  function applyMarketPrefix(){
    const market = document.getElementById('marketType')?.value || '';
    const thBox = document.getElementById('cartonTHBox');
    const exportBox = document.getElementById('cartonExportBox');
    const prefix = document.getElementById('cartonPrefix');
    const shipping = document.getElementById('shippingMark');
    const isExport = market === 'EXPORT' || market === 'LAOS';
    const isTH = market === 'TH';

    if(thBox){
      thBox.classList.toggle('hidden-market', !isTH);
      thBox.style.setProperty('display', isTH ? 'grid' : 'none', 'important');
    }
    if(exportBox){
      exportBox.classList.toggle('hidden-market', !isExport);
      exportBox.style.setProperty('display', isExport ? 'grid' : 'none', 'important');
    }
    if(prefix){
      prefix.disabled = !isExport;
      prefix.style.setProperty('pointer-events', isExport ? 'auto' : 'none', 'important');
      prefix.style.setProperty('opacity', isExport ? '1' : '.75', 'important');
      if(!isExport) prefix.value = '';
    }
    if(shipping){
      if(isExport && prefix && prefix.value && typeof PREFIX_SHIPPING_MAP !== 'undefined'){
        shipping.value = PREFIX_SHIPPING_MAP[prefix.value] || '';
      }else if(!isExport){
        shipping.value = '-';
      }else if(isExport && !prefix.value){
        shipping.value = '';
      }
    }
  }

  function showCheckMessage(msg){
    if(typeof showToast === 'function') showToast(msg, 'error');
    const resultDiv = document.getElementById('result');
    if(resultDiv) resultDiv.innerHTML = `<div class="ng">${msg}</div>`;
  }

  function validateBeforeCheckFinal(){
    const missing = [];
    const mode = document.getElementById('mode')?.value || '';
    const machine = document.getElementById('lpMachine')?.value || '';
    const product = document.getElementById('productType')?.value || '';
    const market = document.getElementById('marketType')?.value || '';
    const mfgDate = document.getElementById('mfgDate')?.value || '';

    if(!mode) missing.push('ประเภทไลน์');
    if(mode && !machine) missing.push('เครื่อง');
    if(!product) missing.push('ประเภทผลิตภัณฑ์');
    if(!market) missing.push('ประเภทงาน');
    if(!mfgDate) missing.push('วันที่ผลิต');
    if((market === 'EXPORT' || market === 'LAOS') && !document.getElementById('cartonPrefix')?.value) missing.push('Prefix');

    const needMix = product === 'EPW' && (market === 'TH' || market === 'LAOS');
    if(needMix && !document.getElementById('mixDate')?.value) missing.push('วันที่ผสม');

    const hasPouch = !!(window.pouchImageData || (typeof pouchImageData !== 'undefined' && pouchImageData));
    const hasCarton = !!(window.cartonImageData || (typeof cartonImageData !== 'undefined' && cartonImageData));
    if(!hasPouch) missing.push('รูปซอง');
    if(!hasCarton) missing.push('รูปกล่อง');

    if(missing.length){
      showCheckMessage('กรุณาเลือก/กรอก: ' + missing.join(', '));
      return false;
    }
    return true;
  }

  function refreshAll(){
    applyMarketPrefix();
    if(typeof updateShippingMarkByPrefix === 'function'){
      try { if(document.getElementById('marketType')?.value === 'EXPORT' || document.getElementById('marketType')?.value === 'LAOS') updateShippingMarkByPrefix(); } catch(e) {}
    }
    if(typeof hardApplyMixVisibility === 'function') { try { hardApplyMixVisibility(); } catch(e) {} }
    if(typeof autoExp === 'function') { try { autoExp(); } catch(e) {} }
    if(typeof updateExpectedLinkedLots === 'function') { try { updateExpectedLinkedLots(); } catch(e) {} }
  }

  const prevChangeMode = window.changeMode;
  window.changeMode = function(){
    try { if(typeof prevChangeMode === 'function') prevChangeMode.apply(this, arguments); } catch(e) {}
    setMachineList(true);
    refreshAll();
    setTimeout(function(){ setMachineList(true); refreshAll(); }, 50);
  };

  const prevChangeProduct = window.changeProduct;
  window.changeProduct = function(){
    try { if(typeof prevChangeProduct === 'function') prevChangeProduct.apply(this, arguments); } catch(e) {}
    applyMarketPrefix();
    refreshAll();
    setTimeout(function(){ applyMarketPrefix(); refreshAll(); }, 50);
  };

  const prevSendCheck = window.sendCheck;
  window.sendCheck = async function(){
    try{
      setMachineList(false);
      applyMarketPrefix();
      if(!validateBeforeCheckFinal()) return;
      if(typeof updateMFGFromDate === 'function') { try { updateMFGFromDate(); } catch(e) {} }
      if(typeof updateMixCodeFromDate === 'function') { try { updateMixCodeFromDate(); } catch(e) {} }
      if(typeof prevSendCheck === 'function') return await prevSendCheck.apply(this, arguments);
      showCheckMessage('ไม่พบฟังก์ชันตรวจสอบ');
    }catch(err){
      showCheckMessage('ตรวจสอบไม่ได้: ' + (err && err.message ? err.message : err));
    }
  };

  document.addEventListener('DOMContentLoaded', function(){
    const mode = document.getElementById('mode');
    const market = document.getElementById('marketType');
    const prefix = document.getElementById('cartonPrefix');
    const machine = document.getElementById('lpMachine');

    if(mode) mode.addEventListener('change', function(){ setMachineList(true); refreshAll(); });
    if(market) market.addEventListener('change', function(){ applyMarketPrefix(); refreshAll(); });
    if(prefix) prefix.addEventListener('change', function(){ applyMarketPrefix(); refreshAll(); });
    if(machine) machine.addEventListener('change', function(){
      const sachetLine = document.getElementById('sachetLine');
      if(sachetLine && document.getElementById('mode')?.value === 'sachet') sachetLine.value = machine.value;
      if(typeof updateExpectedLinkedLots === 'function') updateExpectedLinkedLots();
    });

    // Keep initial fields blank as requested; only machine shows default after user selects line type.
    setTimeout(function(){
      if(!(document.getElementById('mode')?.value)) setMachineList(false);
      applyMarketPrefix();
    }, 700);
  });
})();
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
    # Prefer fonts that support Thai. Do not bundle font files; use system fonts if available.
    candidates = [
        os.path.join(os.getcwd(), "NotoSansThai-Regular.ttf"),
        os.path.join(os.getcwd(), "THSarabunNew.ttf"),
        "C:/Windows/Fonts/NotoSansThai-Regular.ttf",
        "C:/Windows/Fonts/THSarabunNew.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/opentype/tlwg/Sawasdee-Bold.otf",
        "/usr/share/fonts/opentype/tlwg/Sawasdee.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        try:
            if os.path.exists(path) or path.lower() in ("arial.ttf",):
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

        if str(summary).upper() == "PASS":
            title = "LOT CHECK PASS"
            line2 = "POUCH + CARTON VERIFIED"
            color = (255, 255, 255)
            stamp_bg = (22, 163, 74)   # green
        else:
            title = "LOT CHECK NG"
            line2 = "POUCH + CARTON VERIFICATION FAILED"
            color = (255, 255, 255)
            stamp_bg = (220, 38, 38)   # red

        # Header: PASS = green, NG = red
        draw.rectangle([0, 0, canvas_w, header_h], fill=stamp_bg)
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
        for x, label in [(left_x, "POUCH"), (right_x, "CARTON")]:
            draw.rounded_rectangle([x, y0, x + panel_w, y0 + panel_h], radius=22, fill=(255, 255, 255), outline=(215, 225, 235), width=3)
            draw.text((x + 22, y0 + 20), label, font=label_font, fill=(20, 40, 60))

        pouch_x = left_x + (panel_w - pouch_resized.width) // 2
        carton_x = right_x + (panel_w - carton_resized.width) // 2
        img_y = y0 + 72
        image.paste(pouch_resized, (pouch_x, img_y))
        image.paste(carton_resized, (carton_x, img_y))

        # Footer stamp
        footer_y = header_h + image_area_h + 10
        draw.rectangle([0, footer_y, canvas_w, canvas_h], fill=stamp_bg)
        draw_text_with_shadow(draw, (margin, footer_y + 28), title, title_font, color)
        draw_text_with_shadow(draw, (margin, footer_y + 96), f"POUCH + CARTON | {mode} | {product_type} | {market_type}", body_font, (255, 255, 255))
    else:
        image = _open_base64_image(image_base64)

        draw = ImageDraw.Draw(image)
        w, h = image.size

        title_font = get_font(max(30, int(w * 0.045)))
        body_font = get_font(max(20, int(w * 0.028)))

        if str(summary).upper() == "PASS":
            title = "LOT CHECK PASS"
            line2 = "LOT VERIFIED"
            color = (255, 255, 255)
            stamp_bg = (22, 163, 74)   # green
        else:
            title = "LOT CHECK NG"
            line2 = "LOT VERIFICATION FAILED"
            color = (255, 255, 255)
            stamp_bg = (220, 38, 38)   # red

        check_type_en = str(check_type)
        if check_type_en == "ซอง":
            check_type_en = "POUCH"
        elif check_type_en == "กล่อง":
            check_type_en = "CARTON"

        x = max(20, int(w * 0.035))

        # Stamp banner at bottom: PASS = green, NG = red
        line_count = 4
        line_height_title = int(title_font.size * 1.25)
        line_height_body = int(body_font.size * 1.25)
        total_text_height = line_height_title + (line_count - 1) * line_height_body
        pad_y = max(16, int(h * 0.018))
        banner_h = total_text_height + pad_y * 2
        y = max(0, h - banner_h + pad_y)
        draw.rectangle([0, h - banner_h, w, h], fill=stamp_bg)

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
        "building_no": "",
        "suffix": "",
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

    # Building No. and Suffix are separated so the UI can show which field is NG.
    if mfg_index is not None and mfg_index + 1 < len(tokens):
        building = tokens[mfg_index + 1]
        result["building_no"] = building
        if mfg_index + 2 < len(tokens):
            next_token = tokens[mfg_index + 2]
            if re.fullmatch(r"[A-Z]+", next_token):
                result["suffix"] = next_token
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

        # Building No. and Suffix are checked separately
        actual_building_no = field_actual.get("building_no") or building_code
        actual_suffix = field_actual.get("suffix") or ""
        if building_no:
            if not append_carton_field_check(details, "Building No.", actual_building_no, building_no):
                overall = False
            expected_suffix = (building_suffix or "").strip().upper()
            if expected_suffix:
                if not append_carton_field_check(details, "Building Suffix", actual_suffix, expected_suffix):
                    overall = False
            else:
                suffix_ok = not actual_suffix
                details.append({
                    "item": "Building Suffix",
                    "status": "PASS" if suffix_ok else "NG",
                    "actual": actual_suffix if actual_suffix else "ไม่มี",
                    "expected": "ไม่มี Suffix" if suffix_ok else "ไม่ควรมี Suffix"
                })
                if not suffix_ok:
                    overall = False
        else:
            no_building_ok = not actual_building_no
            details.append({
                "item": "Building No.",
                "status": "PASS" if no_building_ok else "NG",
                "actual": actual_building_no if actual_building_no else "ไม่มี",
                "expected": "ไม่มีเลขอาคาร"
            })
            details.append({
                "item": "Building Suffix",
                "status": "PASS" if not actual_suffix else "NG",
                "actual": actual_suffix if actual_suffix else "ไม่มี",
                "expected": "ไม่มี Suffix"
            })
            if not no_building_ok or actual_suffix:
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

    # Building No. and Suffix are checked separately
    actual_building_no = field_actual.get("building_no")
    actual_suffix = field_actual.get("suffix")
    if building_no:
        if not append_carton_field_check(details, "Building No.", actual_building_no, building_no):
            overall = False
        expected_suffix = (building_suffix or "").strip().upper()
        if expected_suffix:
            if not append_carton_field_check(details, "Building Suffix", actual_suffix, expected_suffix):
                overall = False
        else:
            suffix_ok = not actual_suffix
            details.append({
                "item": "Building Suffix",
                "status": "PASS" if suffix_ok else "NG",
                "actual": actual_suffix if actual_suffix else "ไม่มี",
                "expected": "ไม่มี Suffix" if suffix_ok else "ไม่ควรมี Suffix"
            })
            if not suffix_ok:
                overall = False
    else:
        details.append({
            "item": "Building No.",
            "status": "PASS",
            "actual": "ไม่ตรวจเลขอาคาร",
            "expected": "ไม่ตรวจ"
        })
        details.append({
            "item": "Building Suffix",
            "status": "PASS",
            "actual": "ไม่ตรวจ Suffix",
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
            expected_carton_lot = f"{shipping_mark} 00001 {carton_alpha_code} {expected_mfg} {building_no}{(' ' + building_suffix) if building_suffix else ''}".strip()

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
import base64
import io
import json
import os
import re
import urllib.error
import urllib.request
import uuid
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from calendar import monthrange
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

load_dotenv()

app = Flask(__name__)
# Allow high-quality phone photos and multiple pouch/carton images.
# Keep OCR strict, but do not reject the upload too early.
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

STAMP_DIR = "stamped_images"
os.makedirs(STAMP_DIR, exist_ok=True)


HTML = '<!DOCTYPE html>\n<html lang="th">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n<title>IP ONE Lot Checker</title>\n<link rel="icon" type="image/png" href="data:image/png;base64,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">\n<link rel="shortcut icon" type="image/png" href="data:image/png;base64,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">\n<link rel="apple-touch-icon" href="data:image/png;base64,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">\n<style>\n:root{--blue:#0b63ce;--navy:#071f38;--bg:#eef4fb;--card:#fff;--text:#0f172a;--muted:#64748b;--border:#dbe4ef;--green:#16a34a;--red:#dc2626;}\n*{box-sizing:border-box}\nhtml,body{margin:0;padding:0;font-family:Arial,\'Tahoma\',sans-serif;background:var(--bg);color:var(--text);}\nbody{padding:10px;}\n.app{max-width:1180px;margin:0 auto;}\n.header{display:flex;align-items:center;justify-content:center;gap:12px;background:var(--navy);color:#fff;border-radius:18px;padding:12px 14px;box-shadow:0 8px 24px rgba(15,23,42,.18);text-align:left;}\n.logo{width:52px;height:52px;object-fit:contain;background:#fff;border-radius:12px;padding:5px;}\n.header h1{font-size:22px;margin:0;line-height:1.1;}\n.header p{margin:3px 0 0;font-size:12px;color:#cbd5e1;}\n.card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:14px;margin-top:12px;box-shadow:0 6px 18px rgba(15,23,42,.06);}\n.card-title{display:flex;align-items:center;gap:8px;font-weight:800;font-size:16px;margin-bottom:12px;color:#0f172a;}\n.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;}\n.field{min-width:0;}\n.field label{display:block;font-size:13px;font-weight:700;color:#475569;margin:0 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}\n.field input,.field select{width:100%;height:44px;line-height:44px;font-size:15px;padding:0 12px;border:1px solid var(--border);border-radius:12px;background:#fff;color:var(--text);outline:none;min-width:0;}\n.field input:focus,.field select:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(11,99,206,.12)}\n.field input[readonly],.field select:disabled{background:#f8fafc;color:#64748b;}\n.hidden{display:none!important;}\n.photo-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;}\n.photo-card{border:1px dashed #c8d5e4;border-radius:16px;padding:12px;background:#f8fbff;}\n.photo-card h3{margin:0 0 8px;font-size:15px;}\n.file-btn{display:block;width:100%;text-align:center;background:#eaf3ff;border:1px solid #b9d7ff;color:#0757b7;border-radius:12px;padding:12px;font-weight:800;cursor:pointer;}\n.file-btn input{display:none;}\n.preview{display:none;width:100%;max-height:300px;object-fit:contain;margin-top:10px;border-radius:14px;background:#0f172a;border:1px solid var(--border);}\n.time-label{font-size:12px;color:var(--muted);margin-top:6px;}\n.actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}\nbutton{border:0;border-radius:14px;padding:13px 14px;font-size:16px;font-weight:800;color:#fff;background:linear-gradient(135deg,var(--blue),#084c9e);cursor:pointer;}\nbutton.secondary{background:#475569;}\nbutton.success{background:linear-gradient(135deg,#16a34a,#15803d);font-size:18px;}\nbutton.danger{background:#dc2626;}\nbutton:disabled{opacity:.55;cursor:not-allowed;}\n.toast{position:fixed;top:16px;left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;padding:12px 18px;border-radius:14px;font-weight:800;z-index:100000;box-shadow:0 10px 28px rgba(0,0,0,.25);max-width:92vw;text-align:center;}\n.toast.error{background:#dc2626;}\n.camera-modal{display:none;position:fixed;inset:0;background:#000;z-index:99999;flex-direction:column;}\n.camera-modal.active{display:flex;}\n.camera-wrap{position:relative;flex:1;display:flex;align-items:center;justify-content:center;background:#000;overflow:hidden;}\n#cameraVideo{width:100%;height:100%;object-fit:contain;background:#000;}\n.scan-guide{position:absolute;left:14%;top:38%;width:72%;height:22%;border:4px solid #22c55e;border-radius:18px;box-shadow:0 0 0 9999px rgba(0,0,0,.12);pointer-events:none;}\n.camera-toolbar{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;background:#111827;padding:12px;padding-bottom:calc(12px + env(safe-area-inset-bottom));}\n.result-modal{display:none;position:fixed;inset:0;background:rgba(15,23,42,.72);z-index:99998;align-items:center;justify-content:center;padding:16px;}\n.result-modal.active{display:flex;}\n.result-box{background:#fff;border-radius:22px;width:min(980px,96vw);max-height:92vh;overflow:auto;box-shadow:0 24px 70px rgba(0,0,0,.35);}\n.result-head{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;color:#fff;border-radius:22px 22px 0 0;}\n.result-head.pass{background:#16a34a;}\n.result-head.ng{background:#dc2626;}\n.result-head h2{margin:0;font-size:22px;}\n.close-x{background:rgba(255,255,255,.18);width:44px;height:44px;border-radius:999px;padding:0;font-size:26px;line-height:44px;}\n.result-body{padding:14px;}\n.evidence{display:block;width:100%;max-height:58vh;object-fit:contain;background:#f8fafc;border:1px solid var(--border);border-radius:16px;}\n.result-summary{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}\n.result-mini{background:#f8fafc;border:1px solid var(--border);border-radius:14px;padding:10px;font-size:14px;}\n.result-mini b{display:block;color:#334155;margin-bottom:4px;}\n.ng-list{margin-top:12px;background:#fff7f7;border:1px solid #fecaca;border-radius:14px;padding:10px;}\n.ng-list ul{margin:6px 0 0 20px;padding:0;}\n.share-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}\n@media (max-width:720px){\n body{padding:8px;background:#f2f7fd;}\n .header{border-radius:16px;padding:10px;justify-content:center;}\n .logo{width:46px;height:46px;}\n .header h1{font-size:19px;}\n .grid{grid-template-columns:1fr;gap:10px;}\n .photo-grid{grid-template-columns:1fr;}\n .actions{grid-template-columns:1fr;}\n .card{padding:12px;border-radius:16px;margin-top:10px;}\n .field input,.field select{height:48px;line-height:48px;font-size:16px;}\n .camera-toolbar{grid-template-columns:1fr;}\n .result-box{width:100vw;max-height:100vh;border-radius:0;}\n .result-head{border-radius:0;}\n .result-summary,.share-row{grid-template-columns:1fr;}\n .evidence{max-height:44vh;}\n}\n\n.dynamic-machine-list{grid-column:1/-1;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;}\n.dynamic-pouch-cards{display:contents;}\n.dynamic-machine-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:12px;}\n.machine-card-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px;}\n.machine-card-head b{font-size:14px;}\n.btn-small{width:auto;padding:8px 10px;font-size:13px;margin:0;} .flip-btn{display:block;margin-top:8px;width:100%;background:#64748b;}\n.camera-toolbar #extraCaptureButtons{display:contents;}\n@media(max-width:720px){.dynamic-machine-list{grid-template-columns:1fr;} .camera-toolbar #extraCaptureButtons{display:contents;}}\n</style>\n</head>\n<body>\n<div class="app"><div style="background:#fff3cd;border:1px solid #ffe08a;border-radius:12px;padding:8px 12px;margin:8px 0;font-weight:800;color:#7c4a00;text-align:center;">VERSION GPT-5.6 + AUTO EMBOSS OCR FIX / 2026-07-01</div>\n  <div class="header">\n    <img class="logo" src="data:image/png;base64,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" alt="IP One Logo">\n    <div><h1>IP ONE LOT CHECKER</h1><p>POUCH + CARTON VERIFICATION</p></div>\n  </div>\n  <div style="margin:10px 0 0;padding:8px 12px;border-radius:12px;background:#dcfce7;color:#166534;font-weight:800;text-align:center;font-size:13px;">VERSION GPT-5.6 + AUTO EMBOSS OCR FIX / 2026-07-01</div>\n\n  <div class="card">\n    <div class="card-title">ตั้งค่าการตรวจ</div>\n    <div class="grid">\n      <div class="field"><label>ประเภทไลน์</label><select id="mode"><option value="">เลือกประเภทไลน์</option><option value="linapack">Linapack</option><option value="sachet">Sachet</option><option value="auto">Auto</option></select></div>\n      <div class="field"><label>เครื่องซองที่ 1</label><select id="line" disabled><option value="">เลือกประเภทไลน์ก่อน</option></select></div>\n      <div class="field" id="addMachineField"><label>&nbsp;</label><button type="button" class="secondary" id="addPouchMachineBtn">+ เพิ่มเครื่องซอง</button></div>\n      <div id="extraMachineFields" class="dynamic-machine-list"></div>\n      <div class="field"><label>ผลิตภัณฑ์</label><select id="productType"><option value="">เลือกผลิตภัณฑ์</option><option value="EPC">EPC</option><option value="EPW">EPW</option><option value="FS">FS</option><option value="IS">IS</option><option value="SS">SS</option></select></div>\n      <div class="field"><label>ประเภทงาน</label><select id="marketType"><option value="">เลือกประเภทงาน</option><option value="TH">งานไทย</option><option value="EXPORT">งานต่างประเทศ</option><option value="LAOS">งานต่างประเทศ ลาว</option></select></div>\n      <div class="field" id="epcLaosShelfLifeField"><label>อายุ EPC งานลาว</label><select id="epcLaosShelfLife" disabled><option value="24">2 ปี</option><option value="15">1 ปี 3 เดือน (บางไลน์)</option></select></div>\n      <div class="field"><label>วันที่ผลิต</label><input type="date" id="mfgDate"></div>\n      <div class="field mix-field" id="mixDateField"><label>วันที่ผสม</label><input type="date" id="mixDate"></div>\n      <div class="field mix-field" id="mixCodeField"><label>Mix Code</label><input id="mixCode" readonly placeholder="Auto"></div>\n    </div>\n    <input type="hidden" id="mfg"><input type="hidden" id="exp">\n  </div>\n\n  <div class="card">\n    <div class="card-title">ข้อมูลล็อตกล่อง</div>\n    <div class="grid">\n      <div class="field"><label>Shipping Mark</label><input id="shippingMark" readonly placeholder="เลือก Prefix"></div>\n      <div class="field"><label>Prefix</label><select id="cartonPrefix" disabled><option value="">เลือกประเภทงานก่อน</option></select></div>\n      <div class="field"><label>เลขอาคาร</label><select id="buildingNo"><option value="">เลือกเลขอาคาร</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option><option value="6">6</option></select></div>\n      <div class="field"><label>Suffix</label><input id="buildingSuffix" placeholder="เช่น QR / N"></div>\n    </div>\n  </div>\n\n  <div class="card">\n    <div class="card-title">รูปสำหรับตรวจ</div>\n    <div class="photo-grid">\n      <div class="photo-card"><h3>รูปซอง เครื่องที่ 1</h3><label class="file-btn">เลือกรูปซองเครื่องที่ 1<input type="file" id="fileInputPouch" accept="image/*"></label><img id="previewPouch" class="preview"><button type="button" class="secondary btn-small flip-btn" id="flipPouchBtn">↔ พลิกรูปกลับด้าน</button><div id="pouchTime" class="time-label"></div></div>\n      <div id="extraPouchCards" class="dynamic-pouch-cards"></div>\n      <div class="photo-card"><h3>รูปกล่อง</h3><label class="file-btn">เลือกรูปกล่อง<input type="file" id="fileInputCarton" accept="image/*"></label><img id="previewCarton" class="preview"><button type="button" class="secondary btn-small flip-btn" id="flipCartonBtn">↔ พลิกรูปกลับด้าน</button><div id="cartonTime" class="time-label"></div></div>\n    </div>\n    <div class="actions"><button type="button" id="openCameraBtn">เปิดกล้อง</button><button type="button" class="success" id="checkBtn">ตรวจสอบล็อตซอง + กล่อง</button></div>\n  </div>\n</div>\n\n<div class="camera-modal" id="cameraModal">\n  <div class="camera-wrap"><video id="cameraVideo" autoplay playsinline muted></video><div class="scan-guide"></div></div>\n  <div class="camera-toolbar"><button type="button" id="capturePouchBtn">ถ่ายซอง 1</button><span id="extraCaptureButtons"></span><button type="button" id="captureCartonBtn">ถ่ายกล่อง</button><button type="button" class="danger" id="closeCameraBtn">ปิดกล้อง</button></div>\n</div>\n<canvas id="cameraCanvas" class="hidden"></canvas>\n\n<div class="result-modal" id="resultModal">\n  <div class="result-box">\n    <div class="result-head" id="resultHead"><h2 id="resultTitle">ผลตรวจ</h2><button type="button" class="close-x" id="closeResultBtn">×</button></div>\n    <div class="result-body">\n      <img id="evidenceImg" class="evidence" alt="หลักฐานการตรวจ">\n      <div class="result-summary">\n        <div class="result-mini"><b>Lot ซองที่ควรเป็น</b><span id="expectedPouchLot">-</span></div>\n        <div class="result-mini"><b>Lot กล่องที่ควรเป็น</b><span id="expectedCartonLot">-</span></div>\n      </div>\n      <div class="ng-list" id="ngBox"><b>รายการ NG</b><div id="ngContent">-</div></div>\n      <div class="share-row"><button type="button" id="shareBtn">แชร์รูปเข้า LINE / แอปอื่น</button><button type="button" class="secondary" id="closeResultBtn2">ปิด</button></div>\n    </div>\n  </div>\n</div>\n\n<script>const $ = (id) => document.getElementById(id);\nlet pouchImageData = "";\nlet cartonImageData = "";\nlet cameraStream = null;\nlet lastResult = null;\nlet pouchMachines = [];\nlet pouchSeq = 1;\n\nconst PREFIX_SHIPPING_MAP = {\n  KC:"", VN:"IPO VN", VT:"VN-MT", KK:"AKK", CT:"CDT", TS:"TS", AC:"AKC", SM:"SOMCHAICHALUEN", AX:"AKX", MM:"I.P. ONE-MYANMAR",\n  ML:"ML", KT:"KT", MW:"MWD", MK:"MK", MY:"MDY", TG:"TG", MN:"MNJM", MA:"MLA", LM:"MT/LM+VY", DK:"DKSH", NT:"NTPL",\n  XR:"XR", BU:"BUL", UK:"U,K,T-7", DB:"DBL INDUSTRIES PLC", OL:"IMPORTER:ORGANIC LINE CO., LTD", OD:"IMPORTER:ORGANIC LINE CO., LTD",\n  MI:"", WD:"WEDAR", CZ:"", ND:"NDF", CS:"CSMS", FN:"FENIX", CD:"CDM", DT:"DBT", YP:"YPG", LB:"", LQ:""\n};\nconst EXPORT_PREFIXES = Object.keys(PREFIX_SHIPPING_MAP);\nconst NO_SHIPPING_MARK_PREFIXES = new Set(EXPORT_PREFIXES.filter(code => !String(PREFIX_SHIPPING_MAP[code] || "").trim() || String(PREFIX_SHIPPING_MAP[code] || "").trim().toUpperCase() === "ZZZZZ"));\nfunction shippingMarkRequiredForPrefix(prefix){\n  return !!prefix && !NO_SHIPPING_MARK_PREFIXES.has(String(prefix || "").toUpperCase());\n}\nconst MONTH_CODES = ["A","B","C","D","E","F","G","H","I","J","K","L"];\n\nfunction showToast(msg, type="success"){\n  const t = document.createElement("div");\n  t.className = "toast" + (type === "error" ? " error" : "");\n  t.textContent = msg;\n  document.body.appendChild(t);\n  setTimeout(() => t.remove(), 2600);\n}\n\nfunction ddmmyyFromDate(v){\n  if(!v) return "";\n  const parts = v.split("-");\n  if(parts.length !== 3) return "";\n  const [y,m,d] = parts;\n  return `${d}${m}${String(y).slice(-2)}`;\n}\n\nfunction addMonths(dateStr, months){\n  if(!dateStr) return "";\n  const [y,m,d] = dateStr.split("-").map(Number);\n  const dt = new Date(y, m - 1, d);\n  dt.setMonth(dt.getMonth() + months);\n  return `${String(dt.getDate()).padStart(2,"0")}${String(dt.getMonth()+1).padStart(2,"0")}${String(dt.getFullYear()).slice(-2)}`;\n}\n\nfunction updateDates(){\n  const mfgEl = $("mfg");\n  const expEl = $("exp");\n  const mfgDate = $("mfgDate")?.value || "";\n  if(mfgEl) mfgEl.value = ddmmyyFromDate(mfgDate);\n  let exp = "";\n  const product = $("productType")?.value || "";\n  const market = $("marketType")?.value || "";\n  if(product === "FS" && market === "TH") exp = addMonths(mfgDate, 12);\n  if(product === "FS" && (market === "EXPORT" || market === "LAOS")) exp = addMonths(mfgDate, 24);\n  if(["IS","SS"].includes(product) && market === "TH") exp = addMonths(mfgDate, 24);\n  if(["IS","SS"].includes(product) && (market === "EXPORT" || market === "LAOS")) exp = addMonths(mfgDate, 36);\n  if(product === "EPC" && market === "TH") exp = addMonths(mfgDate, 15);\n  if(product === "EPC" && market === "LAOS") exp = addMonths(mfgDate, Number($("epcLaosShelfLife")?.value || 24));\n  if(product === "EPW" && market === "LAOS") exp = addMonths(mfgDate, 36);\n  if(expEl) expEl.value = exp;\n}\n\nfunction updateMix(){\n  const mixDate = $("mixDate")?.value || "";\n  const mixCode = $("mixCode");\n  if(!mixCode) return;\n  if(!mixDate){ mixCode.value = ""; return; }\n  const [y,m,d] = mixDate.split("-");\n  mixCode.value = `${d}${MONTH_CODES[Number(m)-1] || ""}`;\n}\n\nfunction updateProductUI(){\n  const product = $("productType")?.value || "";\n  const market = $("marketType")?.value || "";\n  // EPW งานไทย และ EPW งานลาว ต้องมีวันที่ผสม\n  // EPW งานต่างประเทศทั่วไป ไม่ต้องมีวันที่ผสม\n  const needsMix = product === "EPW" && (market === "TH" || market === "LAOS");\n  const mixDateField = $("mixDateField");\n  const mixCodeField = $("mixCodeField");\n  if(mixDateField) mixDateField.classList.toggle("hidden", !needsMix);\n  if(mixCodeField) mixCodeField.classList.toggle("hidden", !needsMix);\n  document.querySelectorAll(".mix-field").forEach(el => el.classList.toggle("hidden", !needsMix));\n  if(!needsMix){\n    if($("mixDate")) $("mixDate").value = "";\n    if($("mixCode")) $("mixCode").value = "";\n  }\n  const epcLife = $("epcLaosShelfLife");\n  const epcLifeField = $("epcLaosShelfLifeField");\n  const showEpcLife = product === "EPC" && market === "LAOS";\n  if(epcLife){\n    epcLife.disabled = !showEpcLife;\n    if(!showEpcLife) epcLife.value = "24";\n  }\n  if(epcLifeField){\n    epcLifeField.style.opacity = showEpcLife ? "1" : ".55";\n  }\n  updateDates();\n}\n\nfunction machineListForMode(mode){\n  if(mode === "linapack") return ["LP1","LP2","LP3","LP4","LP5","LP6","LP7","LP8","LP9"];\n  if(mode === "sachet") return ["MS1","MS2","MS3","MS4","MS5","MS6","MS7","MS8","MS9","MS10","MS11","MS12","AS1","AS2"];\n  if(mode === "auto") return ["V1","V3","Mespack1","Mespack2","Mespack3"];\n  return [];\n}\n\nfunction fillMachineSelect(selectEl, mode, placeholder){\n  if(!selectEl) return;\n  const oldValue = selectEl.value;\n  selectEl.innerHTML = "";\n  const list = machineListForMode(mode);\n  if(!list.length){\n    selectEl.disabled = true;\n    selectEl.appendChild(new Option("เลือกประเภทไลน์ก่อน", ""));\n    return;\n  }\n  selectEl.disabled = false;\n  selectEl.appendChild(new Option(placeholder || "เลือกเครื่อง", ""));\n  list.forEach(code => selectEl.appendChild(new Option(code, code)));\n  if(list.includes(oldValue)) selectEl.value = oldValue;\n  else selectEl.value = "";\n}\n\nfunction updateAllMachineOptions(){\n  const mode = $("mode")?.value || "";\n  fillMachineSelect($("line"), mode, "เลือกเครื่อง");\n  pouchMachines.forEach(pm => fillMachineSelect($(pm.lineId), mode, `เลือกเครื่องซองที่ ${pm.index}`));\n}\n\nfunction updateMarketUI(){\n  const market = $("marketType")?.value || "";\n  const prefix = $("cartonPrefix");\n  const shipping = $("shippingMark");\n  if(!prefix) return;\n  prefix.innerHTML = "";\n  if(shipping) shipping.value = "";\n  if(!market){\n    prefix.disabled = true;\n    prefix.appendChild(new Option("เลือกประเภทงานก่อน", ""));\n  } else if(market === "TH"){\n    prefix.disabled = true;\n    prefix.appendChild(new Option("00", "00"));\n    prefix.value = "00";\n    if(shipping) shipping.value = "-";\n  } else {\n    prefix.disabled = false;\n    prefix.appendChild(new Option("เลือก Prefix", ""));\n    EXPORT_PREFIXES.forEach(code => prefix.appendChild(new Option(`${code} → ${PREFIX_SHIPPING_MAP[code]}`, code)));\n  }\n  updateProductUI();\n  updateDates();\n  updateShippingMark();\n}\n\nfunction updateShippingMark(){\n  const market = $("marketType")?.value || "";\n  const prefix = ($("cartonPrefix")?.value || "").toUpperCase();\n  const shipping = $("shippingMark");\n  if(!shipping) return;\n  if(market === "TH"){\n    shipping.value = "ไม่ตรวจ";\n    return;\n  }\n  if(!prefix){\n    shipping.value = "";\n    return;\n  }\n  if(!shippingMarkRequiredForPrefix(prefix)){\n    shipping.value = "ไม่ตรวจ";\n    return;\n  }\n  shipping.value = PREFIX_SHIPPING_MAP[prefix] || "";\n}\n\nfunction setPreview(which, data){\n  let imgId = "previewPouch";\n  let timeId = "pouchTime";\n  if(which === "carton"){\n    imgId = "previewCarton";\n    timeId = "cartonTime";\n  } else if(which.startsWith("pouch_")){\n    const id = which.slice(6);\n    imgId = `previewPouch_${id}`;\n    timeId = `pouchTime_${id}`;\n  }\n  const img = $(imgId);\n  const tm = $(timeId);\n  if(img){\n    img.src = data;\n    img.style.display = "block";\n  }\n  if(tm){\n    tm.textContent = "บันทึกล่าสุด " + new Date().toLocaleTimeString("th-TH", {hour12:false});\n  }\n}\n\nfunction storeImageData(which, data){\n  if(which === "pouch") pouchImageData = data;\n  else if(which === "carton") cartonImageData = data;\n  else if(which.startsWith("pouch_")){\n    const id = which.slice(6);\n    const pm = pouchMachines.find(x => String(x.id) === String(id));\n    if(pm) pm.image = data;\n  }\n  setPreview(which, data);\n}\n\nfunction getStoredImageData(which){\n  if(which === "pouch") return pouchImageData;\n  if(which === "carton") return cartonImageData;\n  if(which.startsWith("pouch_")){\n    const id = which.slice(6);\n    const pm = pouchMachines.find(x => String(x.id) === String(id));\n    return pm ? (pm.image || "") : "";\n  }\n  return "";\n}\n\nfunction flipImage(which){\n  const data = getStoredImageData(which);\n  if(!data) return showToast("ยังไม่มีรูปให้พลิก", "error");\n  const img = new Image();\n  img.onload = () => {\n    try{\n      const canvas = document.createElement("canvas");\n      const w = img.naturalWidth || img.width;\n      const h = img.naturalHeight || img.height;\n      canvas.width = w;\n      canvas.height = h;\n      const ctx = canvas.getContext("2d");\n      ctx.translate(w, 0);\n      ctx.scale(-1, 1);\n      ctx.drawImage(img, 0, 0, w, h);\n      const flipped = canvas.toDataURL("image/jpeg", 0.95);\n      storeImageData(which, flipped);\n      showToast("พลิกรูปกลับด้านแล้ว");\n    }catch(err){\n      showToast("พลิกรูปไม่ได้: " + err.message, "error");\n    }\n  };\n  img.onerror = () => showToast("อ่านรูปเพื่อพลิกไม่ได้", "error");\n  img.src = data;\n}\nfunction normalizeImageFile(file){\n  return new Promise((resolve, reject) => {\n    const reader = new FileReader();\n    reader.onerror = () => reject(new Error("อ่านไฟล์รูปไม่ได้"));\n    reader.onload = () => {\n      const rawData = reader.result;\n      const img = new Image();\n      img.onload = () => {\n        try{\n          const maxSide = 2200;\n          let w = img.naturalWidth || img.width;\n          let h = img.naturalHeight || img.height;\n          if(w > maxSide || h > maxSide){\n            const scale = Math.min(maxSide / w, maxSide / h);\n            w = Math.round(w * scale);\n            h = Math.round(h * scale);\n          }\n          const canvas = document.createElement("canvas");\n          canvas.width = w;\n          canvas.height = h;\n          const ctx = canvas.getContext("2d");\n          ctx.drawImage(img, 0, 0, w, h);\n          // แปลงรูปที่อัปโหลดเป็น JPEG คุณภาพสูง เพื่อลดการสูญเสียรายละเอียด dot matrix บนมือถือ\n          resolve(canvas.toDataURL("image/jpeg", 0.95));\n        }catch(e){\n          resolve(rawData);\n        }\n      };\n      img.onerror = () => resolve(rawData);\n      img.src = rawData;\n    };\n    reader.readAsDataURL(file);\n  });\n}\n\nasync function handleFile(which, input){\n  const file = input.files && input.files[0];\n  if(!file) return;\n  try{\n    const data = await normalizeImageFile(file);\n    storeImageData(which, data);\n    showToast("บันทึกรูปเรียบร้อย");\n  }catch(err){\n    showToast("บันทึกรูปไม่ได้: " + err.message, "error");\n  }\n}\n\nfunction renumberPouchMachines(){\n  pouchMachines.forEach((pm, i) => {\n    pm.index = i + 2;\n    const card = $(`machineCard_${pm.id}`);\n    if(card){\n      const title = card.querySelector("b");\n      if(title) title.textContent = `เครื่องซองที่ ${pm.index}`;\n      const sel = $(pm.lineId);\n      if(sel && sel.options.length) sel.options[0].textContent = `เลือกเครื่องซองที่ ${pm.index}`;\n    }\n    const photo = $(`pouchCard_${pm.id}`);\n    if(photo){\n      const h = photo.querySelector("h3");\n      if(h) h.textContent = `รูปซอง เครื่องที่ ${pm.index}`;\n      const label = photo.querySelector(".file-text");\n      if(label) label.textContent = `เลือกรูปซองเครื่องที่ ${pm.index}`;\n    }\n    const cap = $(pm.captureId);\n    if(cap) cap.textContent = `ถ่ายซอง ${pm.index}`;\n  });\n}\n\nfunction removePouchMachine(id){\n  pouchMachines = pouchMachines.filter(pm => String(pm.id) !== String(id));\n  [`machineCard_${id}`, `pouchCard_${id}`, `capturePouch_${id}`].forEach(elId => {\n    const el = $(elId);\n    if(el) el.remove();\n  });\n  renumberPouchMachines();\n}\n\nfunction addPouchMachine(){\n  const id = `p${++pouchSeq}_${Date.now().toString(36)}`;\n  const index = pouchMachines.length + 2;\n  const pm = {\n    id,\n    index,\n    lineId: `line_${id}`,\n    fileId: `fileInputPouch_${id}`,\n    previewId: `previewPouch_${id}`,\n    timeId: `pouchTime_${id}`,\n    captureId: `capturePouch_${id}`,\n    image: ""\n  };\n  pouchMachines.push(pm);\n\n  const machineWrap = document.createElement("div");\n  machineWrap.className = "dynamic-machine-card";\n  machineWrap.id = `machineCard_${id}`;\n  machineWrap.innerHTML = `\n    <div class="machine-card-head">\n      <b>เครื่องซองที่ ${index}</b>\n      <button type="button" class="secondary btn-small" data-remove-pouch="${id}">ลบ</button>\n    </div>\n    <select id="${pm.lineId}"></select>\n  `;\n  $("extraMachineFields").appendChild(machineWrap);\n\n  const photoWrap = document.createElement("div");\n  photoWrap.className = "photo-card";\n  photoWrap.id = `pouchCard_${id}`;\n  photoWrap.innerHTML = `\n    <h3>รูปซอง เครื่องที่ ${index}</h3>\n    <label class="file-btn"><span class="file-text">เลือกรูปซองเครื่องที่ ${index}</span><input type="file" id="${pm.fileId}" accept="image/*"></label>\n    <img id="${pm.previewId}" class="preview">\n    <button type="button" class="secondary btn-small flip-btn" id="flipPouch_${id}">↔ พลิกรูปกลับด้าน</button>\n    <div id="${pm.timeId}" class="time-label"></div>\n  `;\n  $("extraPouchCards").appendChild(photoWrap);\n\n  const capBtn = document.createElement("button");\n  capBtn.type = "button";\n  capBtn.id = pm.captureId;\n  capBtn.textContent = `ถ่ายซอง ${index}`;\n  $("extraCaptureButtons").appendChild(capBtn);\n\n  fillMachineSelect($(pm.lineId), $("mode")?.value || "", `เลือกเครื่องซองที่ ${index}`);\n  $(pm.fileId).addEventListener("change", e => handleFile(`pouch_${id}`, e.target));\n  $(pm.captureId).addEventListener("click", () => captureTo(`pouch_${id}`));\n  const flipBtn = $(`flipPouch_${id}`);\n  if(flipBtn) flipBtn.addEventListener("click", () => flipImage(`pouch_${id}`));\n  const removeBtn = machineWrap.querySelector(`[data-remove-pouch="${id}"]`);\n  if(removeBtn) removeBtn.addEventListener("click", () => removePouchMachine(id));\n}\n\nasync function openCamera(){\n  try{\n    if(!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) throw new Error("browser ไม่รองรับกล้อง");\n    cameraStream = await navigator.mediaDevices.getUserMedia({ video:{ facingMode:{ ideal:"environment" }, width:{ ideal:2560 }, height:{ ideal:1440 } }, audio:false });\n    $("cameraVideo").srcObject = cameraStream;\n    $("cameraModal").classList.add("active");\n  }catch(err){\n    showToast("เปิดกล้องไม่ได้: " + err.message, "error");\n  }\n}\n\nfunction closeCamera(){\n  if(cameraStream) cameraStream.getTracks().forEach(t => t.stop());\n  cameraStream = null;\n  if($("cameraVideo")) $("cameraVideo").srcObject = null;\n  if($("cameraModal")) $("cameraModal").classList.remove("active");\n}\n\nfunction captureTo(which){\n  const video = $("cameraVideo");\n  if(!video || !video.videoWidth) return showToast("ยังไม่พบภาพจากกล้อง", "error");\n  const canvas = $("cameraCanvas");\n  const maxSide = 2200;\n  let w = video.videoWidth;\n  let h = video.videoHeight;\n  if(w > maxSide || h > maxSide){\n    const scale = Math.min(maxSide / w, maxSide / h);\n    w = Math.round(w * scale);\n    h = Math.round(h * scale);\n  }\n  canvas.width = w;\n  canvas.height = h;\n  canvas.getContext("2d").drawImage(video, 0, 0, w, h);\n  const data = canvas.toDataURL("image/jpeg", 0.95);\n  storeImageData(which, data);\n  showToast("บันทึกรูปเรียบร้อย");\n}\n\nfunction getPouchesForPayload(){\n  const list = [{ line: $("line")?.value || "", image: pouchImageData }];\n  pouchMachines.forEach(pm => {\n    list.push({ line: $(pm.lineId)?.value || "", image: pm.image || "" });\n  });\n  return list;\n}\n\nfunction validateBeforeCheck(){\n  const miss = [];\n  if(!$("mode")?.value) miss.push("ประเภทไลน์");\n  if(!$("line")?.value) miss.push("เครื่องซองที่ 1");\n  if(!$("productType")?.value) miss.push("ผลิตภัณฑ์");\n  if(!$("marketType")?.value) miss.push("ประเภทงาน");\n  if(!$("mfgDate")?.value) miss.push("วันที่ผลิต");\n  if($("productType")?.value === "EPW" && ["TH","LAOS"].includes($("marketType")?.value || "") && !$("mixDate")?.value) miss.push("วันที่ผสม");\n  if(($("marketType")?.value === "EXPORT" || $("marketType")?.value === "LAOS") && !$("cartonPrefix")?.value) miss.push("Prefix");\n  if(!$("buildingNo")?.value) miss.push("เลขอาคาร");\n  if(!pouchImageData) miss.push("รูปซองเครื่องที่ 1");\n  if(!cartonImageData) miss.push("รูปกล่อง");\n  pouchMachines.forEach(pm => {\n    if(!$(pm.lineId)?.value) miss.push(`เครื่องซองที่ ${pm.index}`);\n    if(!pm.image) miss.push(`รูปซองเครื่องที่ ${pm.index}`);\n  });\n  if(miss.length){\n    showToast("กรุณาเลือก/กรอก: " + miss.join(", "), "error");\n    return false;\n  }\n  return true;\n}\n\nasync function sendCheck(){\n  updateDates();\n  updateMix();\n  updateShippingMark();\n  if(!validateBeforeCheck()) return;\n  const btn = $("checkBtn");\n  btn.disabled = true;\n  btn.textContent = "กำลังตรวจสอบ... รอได้ยาว ห้ามปิดหน้านี้";\n  try{\n    const pouches = getPouchesForPayload();\n    const payload = {\n      checkType:"both",\n      mode: $("mode").value,\n      productType: $("productType").value,\n      marketType: $("marketType").value,\n      epcLaosShelfLifeMonths: $("epcLaosShelfLife")?.value || "24",\n      mfg: $("mfg")?.value || ddmmyyFromDate($("mfgDate").value),\n      line: $("line").value,\n      exp: $("exp")?.value || "",\n      mixCode: $("mixCode")?.value || "",\n      pouchImage: pouchImageData,\n      cartonImage: cartonImageData,\n      pouches,\n      buildingNo: $("buildingNo").value,\n      buildingSuffix: $("buildingSuffix")?.value || "",\n      shippingMark: (($("marketType").value === "TH" || !shippingMarkRequiredForPrefix($("cartonPrefix")?.value || "")) ? "" : ($("shippingMark")?.value || "")),\n      cartonAlphaCode: $("marketType").value === "TH" ? "00" : $("cartonPrefix").value\n    };\n    const bodyText = JSON.stringify(payload);\n    const approxMB = new Blob([bodyText]).size / 1024 / 1024;\n    if(approxMB > 35){\n      throw new Error(`รูปภาพรวมมีขนาดใหญ่เกินไป (${approxMB.toFixed(1)} MB) กรุณาลดจำนวนรูปหรือถ่ายเฉพาะบริเวณล็อต`);\n    }\n    async function readJsonResponse(res){\n      const responseText = await res.text();\n      try{\n        return responseText ? JSON.parse(responseText) : {};\n      }catch(parseErr){\n        if(responseText && responseText.trim().startsWith("<")){\n          throw new Error("หลังบ้านตอบเป็น HTML แทน JSON: ให้ตรวจว่าใช้ไฟล์ ASYNC JOB OCR เวอร์ชันล่าสุด และดู Render Logs");\n        }\n        throw new Error("ระบบหลังบ้านตอบกลับไม่ถูกต้อง กรุณาดู Render Logs");\n      }\n    }\n\n    const startRes = await fetch("/check", {\n      method:"POST",\n      headers:{"Content-Type":"application/json", "Accept":"application/json"},\n      body: bodyText\n    });\n    const startData = await readJsonResponse(startRes);\n    if(!startRes.ok) throw new Error(startData.error || startData.message || `เริ่มตรวจสอบไม่สำเร็จ (HTTP ${startRes.status})`);\n\n    if(startData.jobId){\n      const jobId = startData.jobId;\n      const started = Date.now();\n      while(true){\n        await new Promise(resolve => setTimeout(resolve, 2500));\n        const waitSec = Math.round((Date.now() - started) / 1000);\n        btn.textContent = `กำลัง OCR... รอแล้ว ${waitSec} วินาที ห้ามปิดหน้านี้`;\n        const stRes = await fetch(`/check_status/${encodeURIComponent(jobId)}`, {headers:{"Accept":"application/json"}});\n        const stData = await readJsonResponse(stRes);\n        if(!stRes.ok) throw new Error(stData.error || stData.message || `ตรวจสอบสถานะไม่สำเร็จ (HTTP ${stRes.status})`);\n        if(stData.status === "done"){\n          showResult(stData.result);\n          break;\n        }\n        if(stData.status === "error"){\n          throw new Error(stData.error || "ตรวจสอบไม่สำเร็จ");\n        }\n        if(waitSec > 600){\n          throw new Error("ระบบใช้เวลานานเกิน 10 นาที กรุณาลองใหม่หรือตรวจสอบ Render Logs");\n        }\n      }\n    } else {\n      showResult(startData);\n    }\n  }catch(err){\n    const msg = String(err && err.message ? err.message : err);\n    if(msg.includes("expected pattern") || msg.includes("did not match")){\n      showToast("รูปที่ส่งไปอ่านไม่ได้ตามรูปแบบที่ระบบ/API รองรับ กรุณาถ่ายใหม่หรือเลือกรูปใหม่", "error");\n    } else {\n      showToast(msg, "error");\n    }\n  }finally{\n    btn.disabled = false;\n    btn.textContent = "ตรวจสอบล็อตซอง + กล่อง";\n  }\n}\n\nfunction showResult(data){\n  lastResult = data;\n  const pass = data.summary === "PASS";\n  if($("resultHead")) $("resultHead").className = "result-head " + (pass ? "pass" : "ng");\n  if($("resultTitle")) $("resultTitle").textContent = pass ? "PASS" : "NG";\n  if($("evidenceImg")) $("evidenceImg").src = data.stampedImageUrl || "";\n  if($("expectedPouchLot")) $("expectedPouchLot").textContent = data.expectedPouchLot || "-";\n  if($("expectedCartonLot")) $("expectedCartonLot").textContent = data.expectedCartonLot || "-";\n  const ngs = (data.details || []).filter(d => d.status === "NG");\n  if($("ngContent")){\n    $("ngContent").innerHTML = ngs.length\n      ? "<ul>" + ngs.map(d => `<li><b>${d.item}</b>: อ่านได้ ${d.actual || "-"} / ควรเป็น ${d.expected || "-"}</li>`).join("") + "</ul>"\n      : "ไม่พบรายการ NG";\n  }\n  if($("resultModal")) $("resultModal").classList.add("active");\n}\n\nfunction closeResult(){\n  if($("resultModal")) $("resultModal").classList.remove("active");\n}\n\nfunction formatShareDate(){\n  const now = new Date();\n  return `${String(now.getDate()).padStart(2,"0")}/${String(now.getMonth()+1).padStart(2,"0")}/${now.getFullYear()} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`;\n}\n\nasync function shareResult(){\n  if(!lastResult) return;\n  const machineText = getPouchesForPayload().map(x => x.line).filter(v => v && v.trim()).join(", ") || "-";\n  const text = `ไลน์ ${machineText} ตรวจสอบความถูกต้องของ Lot แล้ว (${lastResult.summary})\\n\\nวันที่ ${formatShareDate()}`;\n  try{\n    const imageUrl = lastResult.stampedImageUrl || "";\n    if(imageUrl){\n      const resp = await fetch(imageUrl);\n      const blob = await resp.blob();\n      const file = new File([blob], "lot-check.jpg", {type:"image/jpeg"});\n      if(navigator.canShare && navigator.canShare({files:[file]})){\n        await navigator.share({text, files:[file]});\n        return;\n      }\n      if(navigator.share){\n        await navigator.share({text, url: location.origin + imageUrl});\n        return;\n      }\n    }\n    await navigator.clipboard.writeText(text);\n    showToast("คัดลอกข้อความแล้ว");\n  }catch(err){\n    showToast("แชร์ไม่ได้: " + err.message, "error");\n  }\n}\n\nfunction bindEvents(){\n  $("mode")?.addEventListener("change", updateAllMachineOptions);\n  $("productType")?.addEventListener("change", updateProductUI);\n  $("marketType")?.addEventListener("change", updateMarketUI);\n  $("epcLaosShelfLife")?.addEventListener("change", updateDates);\n  $("cartonPrefix")?.addEventListener("change", updateShippingMark);\n  $("mfgDate")?.addEventListener("change", updateDates);\n  $("mixDate")?.addEventListener("change", updateMix);\n  $("fileInputPouch")?.addEventListener("change", e => handleFile("pouch", e.target));\n  $("fileInputCarton")?.addEventListener("change", e => handleFile("carton", e.target));\n  $("flipPouchBtn")?.addEventListener("click", () => flipImage("pouch"));\n  $("flipCartonBtn")?.addEventListener("click", () => flipImage("carton"));\n  $("addPouchMachineBtn")?.addEventListener("click", addPouchMachine);\n  $("openCameraBtn")?.addEventListener("click", openCamera);\n  $("closeCameraBtn")?.addEventListener("click", closeCamera);\n  $("capturePouchBtn")?.addEventListener("click", () => captureTo("pouch"));\n  $("captureCartonBtn")?.addEventListener("click", () => captureTo("carton"));\n  $("checkBtn")?.addEventListener("click", sendCheck);\n  $("closeResultBtn")?.addEventListener("click", closeResult);\n  $("closeResultBtn2")?.addEventListener("click", closeResult);\n  $("shareBtn")?.addEventListener("click", shareResult);\n}\n\nwindow.addEventListener("DOMContentLoaded", () => {\n  bindEvents();\n  updateAllMachineOptions();\n  updateProductUI();\n  updateMarketUI();\n});\n</script>\n</body>\n</html>'


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


def normalize_epc_laos_exp_months(value):
    """EPC Laos can be either 24 months or 15 months depending on line."""
    try:
        months = int(str(value or "24").strip())
    except Exception:
        months = 24
    return 15 if months == 15 else 24


AUTO_MACHINE_MAP = {
    "V1": "VH1",
    "V3": "VH3",
    "MESPACK1": "MH1",
    "MESPACK2": "MH2",
    "MESPACK3": "MH3",
    "VH1": "VH1",
    "VH3": "VH3",
    "MH1": "MH1",
    "MH2": "MH2",
    "MH3": "MH3",
}


def map_auto_machine(ui_code):
    return AUTO_MACHINE_MAP.get(str(ui_code or "").strip().upper(), str(ui_code or "").strip().upper())


def calculate_auto_exp(market_type, mfg):
    dt = parse_ddmmyy(mfg)
    if not dt:
        return ""
    market_type = str(market_type or "").upper()
    if market_type == "TH":
        return format_ddmmyy(add_months(dt, 12))
    if market_type == "LAOS":
        return format_ddmmyy(add_months(dt, 24))
    return ""


def calculate_exp(product_type, market_type, mfg, epc_laos_exp_months=24):
    dt = parse_ddmmyy(mfg)
    if not dt:
        return ""

    if product_type == "FS":
        if market_type == "TH":
            return format_ddmmyy(add_months(dt, 12))
        if market_type in ["EXPORT", "LAOS"]:
            return format_ddmmyy(add_months(dt, 24))
        return ""

    if product_type in ["IS", "SS"]:
        if market_type == "TH":
            return format_ddmmyy(add_months(dt, 24))
        if market_type in ["EXPORT", "LAOS"]:
            return format_ddmmyy(add_months(dt, 36))
        return ""

    if product_type == "EPC":
        if market_type == "TH":
            return format_ddmmyy(add_months(dt, 15))
        if market_type == "LAOS":
            return format_ddmmyy(add_months(dt, normalize_epc_laos_exp_months(epc_laos_exp_months)))
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
    if product_type in ["FS", "IS", "SS"] and market_type in ["TH", "EXPORT", "LAOS"]:
        return True
    if product_type == "EPC" and market_type in ["TH", "LAOS"]:
        return True
    if product_type == "EPW" and market_type == "LAOS":
        return True
    return False


def expected_linapack_exp(product_type, market_type, expected_mfg, epc_laos_exp_months=24):
    product_type = str(product_type or "").upper()
    market_type = str(market_type or "").upper()
    if product_type == "FS" and market_type == "TH":
        return exp_date_plus_years(expected_mfg, 1)
    if product_type == "FS" and market_type in ["EXPORT", "LAOS"]:
        return exp_date_plus_years(expected_mfg, 2)
    if product_type in ["IS", "SS"] and market_type == "TH":
        return exp_date_plus_years(expected_mfg, 2)
    if product_type in ["IS", "SS"] and market_type in ["EXPORT", "LAOS"]:
        return exp_date_plus_years(expected_mfg, 3)
    if product_type == "EPC" and market_type == "TH":
        return exp_date_plus_months(expected_mfg, 15)
    if product_type == "EPC" and market_type == "LAOS":
        return exp_date_plus_months(expected_mfg, normalize_epc_laos_exp_months(epc_laos_exp_months))
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
    EPC LAOS    : MFG DDMMYY เลขเครื่อง เวลา + EXP DDMMYY อายุ 2 ปี หรือ 1 ปี 3 เดือน (เลือกได้ตามไลน์)
    EPW TH      : MFG DDMMYY วันผสม เลขเครื่อง เวลา
    EPW EXPORT  : MFG DDMMYY เลขเครื่อง เวลา
    EPW LAOS    : MFG DDMMYY วันผสม เลขเครื่อง เวลา + EXP DDMMYY อายุ 3 ปี
    FS TH : MFG DDMMYY เลขเครื่อง เวลา + EXP DDMMYY อายุ 1 ปี
    FS EXPORT/LAOS : MFG DDMMYY เลขเครื่อง เวลา + EXP DDMMYY อายุ 2 ปี
    IS/SS TH : MFG DDMMYY เลขเครื่อง เวลา + EXP DDMMYY อายุ 2 ปี
    IS/SS EXPORT/LAOS : MFG DDMMYY เลขเครื่อง เวลา + EXP DDMMYY อายุ 3 ปี
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
            model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.6"),
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
    image_base64 = _extract_base64_payload(image_base64)
    image_bytes = base64.b64decode(image_base64, validate=True)
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def _extract_base64_payload(image_base64):
    """Return pure base64 payload from a data URL or raw base64 string."""
    value = str(image_base64 or "").strip()
    if not value:
        return ""
    if "," in value and value.lower().startswith("data:"):
        value = value.split(",", 1)[1]
    return value.strip()


def normalize_image_base64_for_ai(image_base64, max_side=2000):
    """
    Convert any uploaded/captured image data URL to clean JPEG base64.
    This prevents OpenAI/Gemini errors such as:
    'The string did not match the expected pattern' when an image is WebP/HEIC/data URL malformed.
    """
    raw = _extract_base64_payload(image_base64)
    if not raw:
        raise RuntimeError("ไม่พบข้อมูลรูปภาพ กรุณาถ่าย/อัปโหลดรูปใหม่")
    try:
        img = Image.open(io.BytesIO(base64.b64decode(raw, validate=True))).convert("RGB")
        w, h = img.size
        if max(w, h) > max_side:
            scale = max_side / max(w, h)
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95, optimize=True)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        raise RuntimeError("รูปภาพไม่อยู่ในรูปแบบที่ระบบอ่านได้ กรุณาถ่ายใหม่หรือเลือกรูปใหม่") from e


def _resize_to_fit(image, max_w, max_h):
    w, h = image.size
    scale = min(max_w / w, max_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return image.resize((new_w, new_h), Image.LANCZOS)


def stamp_image(image_base64, summary, check_type, product_type, market_type, mode, checked_time, carton_image_base64=None, pouch2_image_base64=None, pouch_extra_image_base64_list=None):
    """
    Create stamped evidence image.
    - Single mode: stamp one image.
    - POUCH + CARTON mode: create one report image that contains pouch1, optional pouch2, and carton.
    """
    if carton_image_base64:
        images = [("POUCH 1", _open_base64_image(image_base64))]
        extra_images = []
        if pouch_extra_image_base64_list:
            extra_images = [x for x in pouch_extra_image_base64_list if x]
        elif pouch2_image_base64:
            extra_images = [pouch2_image_base64]
        for idx, extra_img in enumerate(extra_images, start=2):
            images.append((f"POUCH {idx}", _open_base64_image(extra_img)))
        images.append(("CARTON", _open_base64_image(carton_image_base64)))

        canvas_w = max(1800, min(3200, 700 * len(images)))
        header_h = 155
        footer_h = 170
        gap = 24
        margin = 36
        panel_w = (canvas_w - (margin * 2) - gap * (len(images) - 1)) // len(images)
        image_max_h = 860

        resized = [(label, _resize_to_fit(img, panel_w, image_max_h)) for label, img in images]
        image_area_h = max(img.height for _, img in resized) + 76
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
            stamp_bg = (22, 163, 74)
        else:
            title = "LOT CHECK NG"
            line2 = "POUCH + CARTON VERIFICATION FAILED"
            color = (255, 255, 255)
            stamp_bg = (220, 38, 38)

        draw.rectangle([0, 0, canvas_w, header_h], fill=stamp_bg)
        draw.text((margin, 30), title, font=title_font, fill=color)
        draw.text((margin, 96), line2, font=body_font, fill=(255, 255, 255))
        time_text = f"By Lot Checker | {checked_time}"
        tb = draw.textbbox((0, 0), time_text, font=body_font)
        draw.text((canvas_w - margin - (tb[2] - tb[0]), 56), time_text, font=body_font, fill=(255, 255, 255))

        y0 = header_h + 30
        panel_h = image_area_h - 20
        img_y = y0 + 72
        for idx, (label, img) in enumerate(resized):
            x = margin + idx * (panel_w + gap)
            draw.rounded_rectangle([x, y0, x + panel_w, y0 + panel_h], radius=22, fill=(255, 255, 255), outline=(215, 225, 235), width=3)
            draw.text((x + 22, y0 + 20), label, font=label_font, fill=(20, 40, 60))
            image.paste(img, (x + (panel_w - img.width) // 2, img_y))

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
            stamp_bg = (22, 163, 74)
        else:
            title = "LOT CHECK NG"
            line2 = "LOT VERIFICATION FAILED"
            color = (255, 255, 255)
            stamp_bg = (220, 38, 38)

        check_type_en = str(check_type)
        if check_type_en == "ซอง":
            check_type_en = "POUCH"
        elif check_type_en == "กล่อง":
            check_type_en = "CARTON"

        x = max(20, int(w * 0.035))
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


def enhance_lot_image_for_ai(image_base64, check_type=""):
    """
    Improve OCR readability before sending to Vision AI.
    Always returns pure JPEG base64, never a data URL.
    """
    try:
        clean_b64 = normalize_image_base64_for_ai(image_base64, max_side=2000)
        img = Image.open(io.BytesIO(base64.b64decode(clean_b64, validate=True))).convert("RGB")
        w, h = img.size

        check_kind = str(check_type or "").lower()
        is_auto_emboss = "auto" in check_kind or "emboss" in check_kind

        # Upscale small images; emboss/dot-matrix codes need enough pixels per character.
        target_min_w = 1750 if is_auto_emboss else (1400 if check_kind == "carton" else 1300)
        if w < target_min_w:
            scale = min(2.2 if is_auto_emboss else 1.8, target_min_w / max(1, w))
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        if is_auto_emboss:
            # Auto line uses emboss blocks: letters are seen by relief/shadow, not ink.
            # Stronger contrast/sharpening helps Vision OCR see MFG/EXP on the block.
            img = ImageOps.autocontrast(img)
            img = ImageEnhance.Contrast(img).enhance(1.85)
            img = ImageEnhance.Sharpness(img).enhance(2.6)
        else:
            img = ImageOps.autocontrast(img)
            img = ImageEnhance.Contrast(img).enhance(1.45)
            img = ImageEnhance.Sharpness(img).enhance(1.8)

        max_w = 2200 if is_auto_emboss else 2000
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=96 if is_auto_emboss else 95)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        # Last fallback: still return pure payload, not a full data URL.
        return _extract_base64_payload(image_base64)

def should_use_gemini_ocr(check_type, product_type, market_type):
    """
    OCR_ENGINE env:
    - auto   : ใช้ Gemini เฉพาะเคสที่อ่านยากก่อน (EPC + LAOS + CARTON) ถ้ามี GEMINI_API_KEY
    - gemini : ใช้ Gemini ทุกภาพ
    - openai : ใช้ OpenAI ทุกภาพ
    """
    engine = str(os.getenv("OCR_ENGINE", "auto") or "auto").strip().lower()
    if engine == "openai":
        return False
    if engine == "gemini":
        return True
    return (
        str(check_type or "").strip().lower() == "carton"
        and str(product_type or "").strip().upper() == "EPC"
        and str(market_type or "").strip().upper() == "LAOS"
        and bool(os.getenv("GEMINI_API_KEY"))
    )


def call_gemini_vision_ocr(image_base64, prompt, check_type):
    """Call Gemini Vision by REST API using only Python standard library."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("ไม่พบ GEMINI_API_KEY")

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    enhanced_base64 = _extract_base64_payload(enhance_lot_image_for_ai(image_base64, check_type))

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": enhanced_base64}},
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "topP": 1,
            "topK": 1,
            "maxOutputTokens": 1024,
            "response_mime_type": "application/json",
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini OCR error: HTTP {e.code} {err_body[:500]}")

    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
        return text
    except Exception:
        raise RuntimeError("Gemini OCR response ไม่อยู่ในรูปแบบที่อ่านได้")


def call_openai_vision_ocr(image_base64, prompt, check_type):
    """Call OpenAI Vision OCR and return raw JSON text."""
    if not client:
        raise RuntimeError("ไม่พบ OPENAI_API_KEY")
    response = client.responses.create(
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.6"),
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{_extract_base64_payload(enhance_lot_image_for_ai(image_base64, check_type))}"},
                ],
            }
        ],
    )
    return response.output_text

def _safe_ocr_lines(result_text):
    try:
        data = json.loads(clean_json_text(result_text))
        lines = data.get("lines", [])
        if isinstance(lines, str):
            lines = [lines]
        return data, [str(x).strip().upper() for x in lines if str(x).strip()]
    except Exception:
        return {}, []

def score_ocr_candidate(result_text, check_type, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, shipping_mark, carton_alpha_code):
    """
    Give a simple rule-based score to decide between OpenAI and Gemini output.
    Verification still happens later; this only chooses the better transcription.
    """
    data, lines = _safe_ocr_lines(result_text)
    joined = " ".join(lines)
    score = 0

    if lines:
        score += 5
    if "UNCLEAR" in joined or "?" in joined:
        score -= 2

    # Date / expected values visible in OCR result.
    if expected_mfg and expected_mfg in joined:
        score += 4
    if expected_exp and expected_exp in joined:
        score += 4
    if expected_line and expected_line.upper() in joined:
        score += 2

    if check_type == "carton":
        # Laos carton does not require EXP and should not be forced into MFG/EXP pouch format.
        if market_type == "LAOS":
            if "EXP" in joined:
                score -= 5
            if re.search(r"\bMFG\b", joined):
                score -= 4
            # Strongly prefer the known export carton visual pattern: AAA 00000 AA DDMMYY N AA
            for line in lines:
                if re.search(r"\b[A-Z]{3}\s+\d{5}\s+[A-Z]{2}\s+\d{6}\s+\d+\s+[A-Z]{1,5}\b", line):
                    score += 12
                if shipping_mark and shipping_mark.upper() in line:
                    score += 5
                if carton_alpha_code and carton_alpha_code.upper() in line:
                    score += 3
                # Common wrong hallucination in previous tests: AKX -> MFG, AX -> PK
                if re.search(r"\bMFG\s+\d{5}\s+PK\b", line):
                    score -= 10
        else:
            if shipping_mark and shipping_mark.upper() in joined:
                score += 4
            if carton_alpha_code and carton_alpha_code.upper() in joined:
                score += 3
    else:
        # Pouch/sachet codes usually need MFG; EXP depends on product/market rules and is verified later.
        if re.search(r"\bMFG\b", joined):
            score += 3
        if expected_exp and re.search(r"\bEXP\b", joined):
            score += 3

    # Prefer parseable JSON with a lines list.
    if isinstance(data.get("lines"), list):
        score += 3
    return score

def choose_dual_ocr_result(openai_text, gemini_text, check_type, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, shipping_mark, carton_alpha_code):
    openai_score = score_ocr_candidate(openai_text, check_type, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, shipping_mark, carton_alpha_code)
    gemini_score = score_ocr_candidate(gemini_text, check_type, mode, product_type, market_type, expected_mfg, expected_line, expected_exp, shipping_mark, carton_alpha_code)
    selected_text = gemini_text if gemini_score > openai_score else openai_text
    try:
        selected_json = json.loads(clean_json_text(selected_text))
        selected_json["ocr_engine_selected"] = "gemini" if gemini_score > openai_score else "openai"
        selected_json["ocr_scores"] = {"openai": openai_score, "gemini": gemini_score}
        return json.dumps(selected_json, ensure_ascii=False)
    except Exception:
        return selected_text

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
        if product_type == "EPC" and market_type == "LAOS":
            prompt = """
You are an OCR transcriber for an EPC Laos CARTON lot code.
This is a CARTON code, not a pouch code.
Read ONLY the dot-matrix carton lot/batch text visible in the image.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits or letters.
Do NOT look for MFG. Do NOT add MFG.
Do NOT look for EXP. EXP is not checked for Laos carton.

Expected visual structure is:
AAA 00000 AA DDMMYY N AA
Example visual structure only: AKX 00001 AX 250626 1 PE

Important for this carton type:
- The first 3 letters are a shipping mark such as AKX, not MFG.
- The 2 letters before the date may be AX, not PK.
- If the first letters are unclear between AKX and MFG, return A?X or UNCLEAR; do not guess MFG.
- If AX is unclear between AX and PK, return A? / ?X / UNCLEAR; do not guess PK.
- Return exactly what is printed, including spaces.

Return JSON only:
{"lines":["carton lot exactly as seen"],"has_exp":false}
"""
        elif market_type == "TH":
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
- Optional shipping mark before running number; some prefixes/countries such as CZ have no shipping mark
- Running number
- Prefix before date
- MFG date
- optional building number and suffix
- optional EXP date

Return JSON only:
{
  "lines": ["carton batch/lot exactly as seen"],
  "has_shipping_mark": false,
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
    elif mode == "auto":
        prompt = """
You are an OCR transcriber for AUTO line emboss block lot codes.
The lot is embossed/engraved on metal or molded blocks, so letters may be visible by shadows and relief, not ink.

Read ONLY the visible emboss lot text.
Do NOT verify correctness. Do NOT use any expected value. Do NOT correct digits or words.

Expected visual structure for this OCR target:
MFG DDMMYY MACHINE EXP DDMMYY

MACHINE can visually be VH1, VH3, MH1, MH2, or MH3.
MFG may appear as MFG., MFG>, MFG|, or with a small separator immediately after G. If M F G are visible, transcribe the word as MFG.
EXP may appear as EXP., EXP>, EXP|, or with a small separator immediately after P. If E X P are visible, transcribe the word as EXP.

Return JSON only:
{"lines":["emboss lot line exactly as seen"]}
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

    if str(mode or "").lower() == "auto" and str(check_type or "").lower() == "pouch":
        check_type = "auto_pouch_emboss"

    # OCR engine selection.
    # OCR_ENGINE=openai : OpenAI only
    # OCR_ENGINE=gemini : Gemini only
    # OCR_ENGINE=auto   : Gemini for difficult EPC Laos carton, otherwise OpenAI
    # OCR_ENGINE=dual   : Read with both OpenAI + Gemini, then choose the result that matches product rules better
    engine = str(os.getenv("OCR_ENGINE", "auto") or "auto").strip().lower()

    if engine == "dual":
        # RENDER-SAFE FAST OCR MODE:
        # The previous dual mode called both OpenAI and Gemini for some images.
        # With 2 pouch machines + carton this can create too many slow external calls and Render may return HTML/timeout.
        # This mode still uses both providers as failover, but only ONE provider per image:
        # - Prefer Gemini first when available because it handled dot-matrix carton text better in tests.
        # - Fall back to OpenAI if Gemini fails.
        errors = []
        if os.getenv("GEMINI_API_KEY"):
            try:
                return call_gemini_vision_ocr(image_base64, prompt, check_type)
            except Exception as e:
                errors.append(f"Gemini: {e}")
        if os.getenv("OPENAI_API_KEY"):
            try:
                return call_openai_vision_ocr(image_base64, prompt, check_type)
            except Exception as e:
                errors.append(f"OpenAI: {e}")
        raise RuntimeError(" / ".join(errors) if errors else "OCR engine ใช้งานไม่ได้")

    if should_use_gemini_ocr(check_type, product_type, market_type):
        try:
            return call_gemini_vision_ocr(image_base64, prompt, check_type)
        except Exception:
            # In auto mode, fall back to OpenAI if Gemini is unavailable.
            if engine == "gemini" or not client:
                raise

    return call_openai_vision_ocr(image_base64, prompt, check_type)


def _safe_json_loads_from_ai(raw_text):
    """Parse AI JSON robustly and raise a Thai-friendly error when parsing fails."""
    try:
        return json.loads(clean_json_text(raw_text))
    except Exception as e:
        preview = str(raw_text or "")[:300].replace("\n", " ")
        raise RuntimeError(f"AI OCR ตอบกลับไม่เป็น JSON ที่อ่านได้: {preview}") from e


def _normalize_batch_ocr_result(batch_json, pouch_count):
    """
    Normalize batch OCR response to:
    {"pouches": {1: {"lines": [...]}, ...}, "carton": {"lines": [...]}}
    Supports a few common model response variants.
    """
    if not isinstance(batch_json, dict):
        raise RuntimeError("ผล Batch OCR ไม่ใช่ JSON object")

    pouch_map = {}
    pouches_obj = batch_json.get("pouches") or batch_json.get("pouch") or []
    if isinstance(pouches_obj, dict):
        # Accept {"1": {"lines": [...]}, "2": ...}
        for k, v in pouches_obj.items():
            try:
                idx = int(str(k).replace("POUCH", "").replace("pouch", "").replace("_", "").strip())
            except Exception:
                continue
            pouch_map[idx] = v if isinstance(v, dict) else {"lines": v if isinstance(v, list) else [str(v)]}
    elif isinstance(pouches_obj, list):
        for pos, item in enumerate(pouches_obj, start=1):
            if isinstance(item, dict):
                idx = item.get("index") or item.get("pouch") or item.get("id") or pos
                try:
                    idx = int(str(idx).replace("POUCH", "").replace("pouch", "").replace("_", "").strip())
                except Exception:
                    idx = pos
                pouch_map[idx] = item
            else:
                pouch_map[pos] = {"lines": [str(item)]}

    # Fallback for top-level pouch1/pouch_1 keys.
    for idx in range(1, pouch_count + 1):
        if idx not in pouch_map:
            for key in (f"pouch{idx}", f"pouch_{idx}", f"POUCH_{idx}", f"POUCH{idx}"):
                if key in batch_json:
                    v = batch_json[key]
                    pouch_map[idx] = v if isinstance(v, dict) else {"lines": v if isinstance(v, list) else [str(v)]}
                    break

    normalized_pouches = {}
    for idx in range(1, pouch_count + 1):
        item = pouch_map.get(idx, {})
        lines = item.get("lines", []) if isinstance(item, dict) else []
        if isinstance(lines, str):
            lines = [lines]
        normalized_pouches[idx] = {
            "lines": [str(x).strip().upper() for x in lines if str(x).strip()],
            "raw": item,
        }

    carton_obj = batch_json.get("carton") or batch_json.get("CARTON") or batch_json.get("box") or {}
    if not isinstance(carton_obj, dict):
        carton_obj = {"lines": carton_obj if isinstance(carton_obj, list) else [str(carton_obj)]}
    carton_lines = carton_obj.get("lines", [])
    if isinstance(carton_lines, str):
        carton_lines = [carton_lines]
    carton_obj["lines"] = [str(x).strip().upper() for x in carton_lines if str(x).strip()]

    return {"pouches": normalized_pouches, "carton": carton_obj, "raw": batch_json}


def _batch_ocr_prompt(pouches, product_type, market_type, mode):
    pouch_desc = "\n".join([f"- POUCH_{idx}: sachet/pouch lot rows for machine {item.get('line','').strip().upper()}" for idx, item in enumerate(pouches, start=1)])
    auto_note = ""
    if str(mode or "").lower() == "auto":
        auto_note = """
AUTO LINE EMBOSS POUCH NOTE:
- POUCH images are emboss block codes, not normal inkjet text.
- The correct visual structure is: MFG DDMMYY MACHINE EXP DDMMYY.
- MACHINE can be VH1, VH3, MH1, MH2, or MH3.
- MFG may be embossed with a dot, arrow, notch, or separator after G, such as MFG. or MFG>. If the letters M F G are visible, transcribe the word as MFG.
- EXP may also have a separator after P. If E X P are visible, transcribe as EXP.
- Do not omit MFG just because emboss contrast is low; read the raised/engraved letters and their shadows.
"""
    carton_note = ""
    if str(product_type).upper() == "EPC" and str(market_type).upper() == "LAOS":
        carton_note = """
CARTON NOTE FOR EPC LAOS:
- The carton code is NOT a pouch MFG/EXP code.
- Do NOT add MFG.
- Do NOT add EXP.
- Typical visible structure may be like: AKC 00001 AC DDMMYY 3
- Some countries/prefixes have no shipping mark; if no shipping mark is visible, do not invent one.
"""
    else:
        carton_note = """
CARTON NOTE:
- Read only the carton batch/lot line visible on the carton.
- Some countries/prefixes have no shipping mark; if no shipping mark is visible, do not invent one.
"""
    return f"""
You are an OCR transcriber for a factory lot verification system.
You will receive multiple images in one request. Each image is labeled before it.

IMAGE LIST:
{pouch_desc}
- CARTON: carton lot/batch code image

TASK:
Read ONLY the visible printed lot/batch/MFG/EXP text from each labeled image.
Do NOT verify correctness.
Do NOT use expected values.
Do NOT correct digits, dates, line codes, MFG, EXP, prefixes, or suffixes.
If a character is unclear, use ? or UNCLEAR.

POUCH RULES:
- Return all visible lot rows for each pouch image.
- Never add missing MFG or EXP. If MFG/EXP is not clearly visible, return exactly what is visible or UNCLEAR.
- Do not normalize dates. Example: if visible is 300626, return 300626 exactly.

{auto_note}
{carton_note}

STRICT NO-GUESSING RULES:
- If a digit/letter is broken, faint, smeared, or ambiguous, use ? for that character.
- If the text is not readable, return an empty lines array or UNCLEAR for that image.
- Return JSON only. Do not explain.

REQUIRED JSON FORMAT:
{{
  "pouches": [
    {{"index": 1, "lines": ["visible line 1", "visible line 2"]}},
    {{"index": 2, "lines": ["visible line 1"]}}
  ],
  "carton": {{"lines": ["visible carton lot line"]}}
}}
"""


def call_gemini_batch_ocr(image_items, prompt):
    """One Gemini request for all pouch/carton images to reduce Render/Gunicorn timeout."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("ไม่พบ GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    parts = [{"text": prompt}]
    for item in image_items:
        enhanced = _extract_base64_payload(enhance_lot_image_for_ai(item["image"], item.get("check_type", "")))
        parts.append({"text": f"\nIMAGE_ID: {item['id']} ({item.get('check_type','')})\n"})
        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": enhanced}})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "topP": 1,
            "topK": 1,
            "maxOutputTokens": 4096,
            "response_mime_type": "application/json",
        },
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=int(os.getenv("OCR_REQUEST_TIMEOUT", "240"))) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini Batch OCR error: HTTP {e.code} {err_body[:500]}")
    parts_out = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts_out).strip()
    if not text:
        raise RuntimeError("Gemini Batch OCR ไม่ส่งข้อความกลับมา")
    return text


def call_openai_batch_ocr(image_items, prompt):
    """One OpenAI request for all pouch/carton images to reduce Render/Gunicorn timeout."""
    if not client:
        raise RuntimeError("ไม่พบ OPENAI_API_KEY")
    content = [{"type": "input_text", "text": prompt}]
    for item in image_items:
        enhanced = _extract_base64_payload(enhance_lot_image_for_ai(item["image"], item.get("check_type", "")))
        content.append({"type": "input_text", "text": f"IMAGE_ID: {item['id']} ({item.get('check_type','')})"})
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{enhanced}"})
    response = client.responses.create(
        model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.6"),
        input=[{"role": "user", "content": content}],
    )
    return response.output_text


def read_both_batch_with_ai(pouches, carton_image_base64, product_type, market_type, mode):
    """
    Batch OCR for checkType='both'. This is the timeout fix:
    4 pouch images + 1 carton image become 1 OCR request instead of 5 slow requests.
    """
    image_items = []
    for idx, item in enumerate(pouches, start=1):
        pouch_check_type = "auto_pouch_emboss" if str(mode or "").lower() == "auto" else "pouch"
        image_items.append({"id": f"POUCH_{idx}", "check_type": pouch_check_type, "image": item.get("image", "")})
    image_items.append({"id": "CARTON", "check_type": "carton", "image": carton_image_base64})
    prompt = _batch_ocr_prompt(pouches, product_type, market_type, mode)
    engine = str(os.getenv("OCR_ENGINE", "auto") or "auto").strip().lower()
    errors = []

    # Prefer Gemini in batch mode because one multi-image Gemini call is usually faster than many separate calls.
    provider_order = []
    if engine == "openai":
        provider_order = ["openai"]
    elif engine == "gemini":
        provider_order = ["gemini"]
    else:
        provider_order = ["gemini", "openai"]

    for provider in provider_order:
        try:
            if provider == "gemini" and os.getenv("GEMINI_API_KEY"):
                raw = call_gemini_batch_ocr(image_items, prompt)
                parsed = _safe_json_loads_from_ai(raw)
                parsed["ocr_batch_provider"] = "gemini"
                return _normalize_batch_ocr_result(parsed, len(pouches))
            if provider == "openai" and os.getenv("OPENAI_API_KEY"):
                raw = call_openai_batch_ocr(image_items, prompt)
                parsed = _safe_json_loads_from_ai(raw)
                parsed["ocr_batch_provider"] = "openai"
                return _normalize_batch_ocr_result(parsed, len(pouches))
        except Exception as e:
            errors.append(f"{provider}: {friendly_error_message(e)}")
    raise RuntimeError("Batch OCR ล้มเหลว: " + " / ".join(errors))

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



def _parse_emboss_joined_mfg_exp(text):
    """
    Robust parser for Auto emboss lot, where OCR may return joined/separated forms:
    MFG>300626, MFG.300626, M F G 300626, EXP:300628, etc.
    """
    t = normalize(text)
    result = {}
    mfg_match = re.search(r"M\s*F\s*G[\s\.\:\-\>\|]*([0-9?]{6})", t)
    if mfg_match:
        result["mfg_word"] = "MFG"
        result["mfg_date"] = mfg_match.group(1)
    exp_match = re.search(r"E\s*X\s*P[\s\.\:\-\>\|]*([0-9?]{6})", t)
    if exp_match:
        result["exp_word"] = "EXP"
        result["exp_date"] = exp_match.group(1)
    machine_match = re.search(r"\b(?:VH|MH|LP|MS|AS)\d{1,2}\b", t)
    if machine_match:
        result["machine"] = machine_match.group(0)
    return result


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

    # MFG - exact token plus emboss-friendly joined forms such as MFG>300626
    emboss_fields = _parse_emboss_joined_mfg_exp(" ".join([text, exp_text]))
    if emboss_fields.get("mfg_word"):
        result["mfg_word"] = "MFG"
    if emboss_fields.get("mfg_date"):
        result["mfg_date"] = emboss_fields.get("mfg_date", "")
    if emboss_fields.get("machine"):
        result["machine"] = emboss_fields.get("machine", "")

    if "MFG" in tokens:
        idx = tokens.index("MFG")
        result["mfg_word"] = "MFG"
        if idx + 1 < len(tokens):
            result["mfg_date"] = tokens[idx + 1]
        if idx + 2 < len(tokens):
            v = tokens[idx + 2]
            if re.fullmatch(r"(?:LP|MS|AS|VH|MH)\d{1,2}", v):
                result["machine"] = v
            else:
                result["mix_code"] = v
        if idx + 3 < len(tokens):
            v = tokens[idx + 3]
            if re.fullmatch(r"(?:LP|MS|AS|VH|MH)\d{1,2}", v):
                result["machine"] = v

    # fallback date
    if not result["mfg_date"]:
        m = re.search(r"\b\d{6}\b", text)
        if m:
            result["mfg_date"] = m.group(0)

    # fallback machine
    if not result["machine"]:
        m = re.search(r"\b(?:LP|MS|AS|VH|MH)\d{1,2}\b", text)
        if m:
            result["machine"] = m.group(0)

    # time
    m = re.search(r"\b([0-2]?\d:[0-5]\d)\b", text)
    if m:
        result["time"] = m.group(1)

    # EXP line - exact token plus emboss-friendly joined forms such as EXP:300628
    exp_source = exp_text if exp_text else text
    exp_tokens = exp_source.split()
    if emboss_fields.get("exp_word"):
        result["exp_word"] = "EXP"
    if emboss_fields.get("exp_date"):
        result["exp_date"] = emboss_fields.get("exp_date", "")

    if "EXP" in exp_tokens:
        idx = exp_tokens.index("EXP")
        result["exp_word"] = "EXP"
        if idx + 1 < len(exp_tokens):
            result["exp_date"] = exp_tokens[idx + 1]
    else:
        if "EXP" in exp_source:
            result["exp_word"] = "EXP"
        if not result["exp_date"]:
            exp_m = re.search(r"E\s*X\s*P[\s\.\:\-\>\|]*([0-9?]{6})", exp_source)
            if exp_m:
                result["exp_word"] = "EXP"
                result["exp_date"] = exp_m.group(1)
        if not result["exp_date"]:
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


def check_pouch_auto(lines, market_type, expected_mfg, expected_line, expected_exp):
    """
    Auto emboss lot verification.
    Expected format:
    - งานไทย: MFG DDMMYY MACHINE EXP DDMMYY (+1 year)
    - งานลาว: MFG DDMMYY MACHINE EXP DDMMYY (+2 years)
    No mix code. No time field.
    """
    details = []
    overall = True

    lines = [normalize(x) for x in lines]
    all_text = " ".join(lines)
    mfg_line = lines[0] if len(lines) > 0 else all_text
    exp_line = " ".join(lines[1:]) if len(lines) > 1 else all_text
    fields = parse_pouch_lot_fields(mfg_line, exp_line)

    machine_actual = fields.get("machine", "")
    if not machine_actual:
        alt_machine = str(fields.get("mix_code") or "").strip().upper()
        if re.fullmatch(r"(?:VH|MH)\d{1,2}", alt_machine):
            machine_actual = alt_machine

    if not append_field_check(details, "MFG", fields.get("mfg_word"), "MFG"):
        overall = False
    if not append_field_check(details, "วันผลิต", fields.get("mfg_date"), expected_mfg):
        overall = False
    if not append_field_check(details, "เลขเครื่อง", machine_actual, expected_line):
        overall = False
    if not append_field_check(details, "EXP", fields.get("exp_word"), "EXP"):
        overall = False
    if not append_field_check(details, "วันหมดอายุ", fields.get("exp_date"), expected_exp):
        overall = False

    return overall, details


def check_pouch_linapack(lines, product_type, market_type, expected_mfg, expected_line, expected_exp, mix_code, ai_time="", epc_laos_exp_months=24):
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

    expected_exp_calc = expected_linapack_exp(product_type, market_type, expected_mfg, epc_laos_exp_months)
    if expected_exp_calc:
        expected_exp = expected_exp_calc
        # LINAPACK_RULE_EXPECTED_EXP_OVERRIDE
        try:
            if str(mode).lower() == "linapack":
                expected_exp = expected_linapack_exp(product_type, market_type, expected_mfg, epc_laos_exp_months)
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

NO_SHIPPING_MARK_CODES = {"KC", "MI", "CZ", "LB", "LQ"}
NO_SHIPPING_MARK_VALUES = {"", "-", "ZZZZZ", "ไม่ตรวจ", "NO", "NONE", "N/A", "NA"}

def shipping_mark_is_required(shipping_mark="", carton_alpha_code=""):
    """Return False when the selected country/prefix has no shipping mark to verify.
    CZ and any code mapped to blank/ZZZZZ are intentionally skipped.
    """
    code = clean_lot_token(carton_alpha_code)
    mark_raw = str(shipping_mark or "").strip()
    mark_upper = mark_raw.upper()
    if code in NO_SHIPPING_MARK_CODES:
        return False
    if mark_upper in NO_SHIPPING_MARK_VALUES:
        return False
    if clean_lot_token(mark_raw) == "ZZZZZ":
        return False
    return bool(mark_raw)

def normalize_shipping_mark_for_check(shipping_mark="", carton_alpha_code=""):
    return str(shipping_mark or "").strip().upper() if shipping_mark_is_required(shipping_mark, carton_alpha_code) else ""


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
    shipping_mark = normalize_shipping_mark_for_check(shipping_mark, "")
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
    shipping_mark_required = shipping_mark_is_required(shipping_mark, carton_alpha_code)

    # Running No. = first 4-5 digit token. MFG date is 6 digits, so it is ignored here.
    run_index = None
    for i, token in enumerate(tokens):
        if re.fullmatch(r"\d{4,5}", token):
            result["running_no"] = token
            run_index = i
            break

    # Shipping Mark = token before Running No.
    # If this country/prefix has no shipping mark (for example CZ), do not extract/check it.
    if shipping_mark_required and run_index is not None and run_index > 0:
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

def check_carton(lines, market_type, expected_mfg, expected_exp, building_no, building_suffix, shipping_mark, carton_alpha_code, ai_json, check_exp=True):
    """
    Carton verification แบบแยก field และเทียบทีละตัวอักษร
    เพื่อแสดงชัดเจนว่าตัวเลข/ตัวอักษรตำแหน่งไหนผิด
    """
    shipping_mark = normalize_shipping_mark_for_check(shipping_mark, carton_alpha_code)
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
    if not check_exp:
        # ล็อตกล่องงานลาว: ไม่ตรวจ EXP เลย ไม่บังคับให้มี และไม่ NG ถ้า OCR อ่านเจอ
        actual_exp = field_actual.get("exp")
        details.append({
            "item": "EXP",
            "status": "PASS",
            "actual": actual_exp if actual_exp else "ไม่ตรวจ",
            "expected": "ไม่ตรวจ EXP สำหรับล็อตกล่องงานลาว"
        })
    elif expected_exp:
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


def friendly_error_message(err):
    raw = str(err or "")
    low = raw.lower()
    if "expected pattern" in low or "did not match" in low:
        return "ระบบอ่านรูปไม่สำเร็จ: รูปหรือข้อมูลที่ส่งไปไม่ตรงรูปแบบที่ API รองรับ กรุณาถ่ายใหม่/เลือกรูปใหม่ แล้วลองอีกครั้ง"
    if "unexpected token" in low or "not valid json" in low:
        return "ระบบประมวลผลไม่สำเร็จ: หลังบ้านไม่ได้ส่ง JSON กลับมา กรุณาดู Render Logs"
    if "quota" in low or "429" in low or "rate" in low:
        return "OCR ถูกจำกัดจำนวนครั้งชั่วคราว/เรียกพร้อมกันมากเกินไป กรุณาลองใหม่ หรือกำหนด OCR_MAX_WORKERS=1 ใน Render"
    if "timeout" in low or "timed out" in low:
        return "OCR ใช้เวลานานเกินไป กรุณาลองใหม่ หรือตั้ง Start Command เป็น gunicorn app:app --timeout 300"
    if "gemini" in low and ("400" in low or "api" in low):
        return "Gemini OCR ใช้งานไม่สำเร็จ กรุณาตรวจสอบ GEMINI_API_KEY / GEMINI_MODEL หรือเปลี่ยน OCR_ENGINE=openai ชั่วคราว"
    if "openai" in low and ("api" in low or "key" in low):
        return "OpenAI OCR ใช้งานไม่สำเร็จ กรุณาตรวจสอบ OPENAI_API_KEY"
    return raw


@app.errorhandler(413)
def handle_request_too_large(e):
    return jsonify({"error": "รูปภาพรวมมีขนาดใหญ่เกิน 64MB กรุณาลดจำนวนรูปหรือครอปเฉพาะบริเวณล็อต"}), 413


@app.errorhandler(400)
def handle_bad_request(e):
    if request.path == "/check":
        return jsonify({"error": "ข้อมูลที่ส่งมาไม่ถูกต้อง กรุณาลองใหม่"}), 400
    return e


@app.errorhandler(504)
def handle_gateway_timeout(e):
    if request.path == "/check":
        return jsonify({"error": "ระบบใช้เวลาประมวลผลนานเกินไป กรุณาลองใหม่ หรือเพิ่ม Gunicorn timeout เป็น 300 วินาที"}), 504
    return e

@app.errorhandler(500)
def handle_internal_error(e):
    if request.path == "/check":
        return jsonify({"error": "ระบบหลังบ้านประมวลผลไม่สำเร็จ กรุณาลองใหม่ โดยถ่ายรูปเฉพาะบริเวณล็อตให้ใกล้ขึ้น"}), 500
    return e


@app.route("/stamped/<filename>")
def stamped_file(filename):
    return send_from_directory(STAMP_DIR, filename)




@app.route("/")
def index():
    return HTML



@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# Async job store: prevents Render/Gunicorn request timeout during slow OCR.
# /check returns a jobId immediately, then the browser polls /check_status/<jobId>.
JOBS = {}
JOBS_LOCK = threading.Lock()
OCR_EXECUTOR = ThreadPoolExecutor(max_workers=int(os.getenv("OCR_JOB_WORKERS", "2")))
JOB_TTL_SECONDS = int(os.getenv("OCR_JOB_TTL_SECONDS", "1800"))
JOB_DIR = os.getenv("OCR_JOB_DIR", "ocr_jobs")
os.makedirs(JOB_DIR, exist_ok=True)

def _job_path(job_id):
    safe = re.sub(r"[^a-fA-F0-9]", "", str(job_id))[:64]
    return os.path.join(JOB_DIR, f"{safe}.json")

def _save_job(job_id, job):
    try:
        path = _job_path(job_id)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(job, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass

def _load_job(job_id):
    try:
        with open(_job_path(job_id), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _cleanup_jobs():
    now = time.time()
    with JOBS_LOCK:
        old_ids = [jid for jid, job in JOBS.items() if now - job.get("created", now) > JOB_TTL_SECONDS]
        for jid in old_ids:
            JOBS.pop(jid, None)
            try:
                os.remove(_job_path(jid))
            except Exception:
                pass

def _check_sync_from_data(data):
    try:
        data = data or {}

        check_type = data.get("checkType", "pouch").strip().lower()
        mode = data.get("mode", "sachet").strip().lower()
        product_type = data.get("productType", "EPC").strip().upper()
        market_type = data.get("marketType", "TH").strip().upper()
        original_market_type = market_type
        epc_laos_exp_months = normalize_epc_laos_exp_months(data.get("epcLaosShelfLifeMonths", 24))
        expected_mfg = data.get("mfg", "").strip()
        expected_line = data.get("line", "").strip().upper()
        expected_line2 = data.get("line2", "").strip().upper()
        if mode == "auto":
            expected_line = map_auto_machine(expected_line)
            expected_line2 = map_auto_machine(expected_line2)
        expected_exp = data.get("exp", "").strip()
        # Special LAOS EXP examples: EPC +2 years, EPW +3 years. Backend recalculates again below.
        try:
            if str(product_type).upper() == "EPW" and str(market_type).upper() == "LAOS":
                expected_exp = exp_date_plus_years(expected_mfg, 3)
        except Exception:
            pass
        mix_code = data.get("mixCode", "").strip().upper()
        pouch_image_data = data.get("pouchImage", "")
        pouch2_image_data = data.get("pouchImage2", "")
        carton_image_data = data.get("cartonImage", "")
        image_data = data.get("image", "")  # fallback for old clients

        # Dynamic pouch machines from new UI. Fallback to legacy pouchImage/pouchImage2.
        pouches = data.get("pouches") or []
        if not isinstance(pouches, list):
            pouches = []
        clean_pouches = []
        for item in pouches:
            if not isinstance(item, dict):
                continue
            line_code = str(item.get("line", "")).strip().upper()
            if mode == "auto":
                line_code = map_auto_machine(line_code)
            img_data = item.get("image", "") or ""
            if line_code or img_data:
                clean_pouches.append({"line": line_code, "image": img_data})
        if not clean_pouches:
            if expected_line or pouch_image_data:
                clean_pouches.append({"line": expected_line, "image": pouch_image_data})
            if expected_line2 or pouch2_image_data:
                clean_pouches.append({"line": expected_line2, "image": pouch2_image_data})
        pouches = clean_pouches

        building_no = data.get("buildingNo", "").strip()
        building_suffix = data.get("buildingSuffix", "").strip().upper()
        if not building_no:
            building_suffix = ""
        carton_alpha_code = data.get("cartonAlphaCode", "").strip().upper()
        shipping_mark = normalize_shipping_mark_for_check(data.get("shippingMark", ""), carton_alpha_code)

        # Carton lot does not separate Laos. Treat Laos as normal Export format, but do not verify EXP for Laos cartons.
        if check_type == "carton" and market_type == "LAOS":
            market_type = "EXPORT"

        if not expected_mfg:
            return jsonify({"error": "กรุณาเลือกวันที่ผลิต"}), 400

        if check_type == "both":
            if not carton_image_data:
                return jsonify({"error": "กรุณาถ่าย/อัปโหลดรูปกล่องให้ครบ"}), 400
            if not pouches:
                return jsonify({"error": "กรุณาเพิ่มเครื่องซองอย่างน้อย 1 เครื่อง"}), 400
            for idx, item in enumerate(pouches, start=1):
                if not item.get("line"):
                    return jsonify({"error": f"กรุณาเลือกเครื่องซองที่ {idx}"}), 400
                if not item.get("image"):
                    return jsonify({"error": f"กรุณาถ่าย/อัปโหลดรูปซองเครื่องที่ {idx}"}), 400
        elif not image_data:
            return jsonify({"error": "กรุณาอัปโหลดรูปหรือถ่ายรูปก่อน"}), 400

        engine = str(os.getenv("OCR_ENGINE", "auto") or "auto").strip().lower()
        if engine == "openai" and not os.getenv("OPENAI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY"}), 500
        if engine == "gemini" and not os.getenv("GEMINI_API_KEY"):
            return jsonify({"error": "ไม่พบ GEMINI_API_KEY"}), 500
        if engine == "dual" and not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY หรือ GEMINI_API_KEY สำหรับ dual mode"}), 500
        if engine == "auto" and not os.getenv("OPENAI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            return jsonify({"error": "ไม่พบ OPENAI_API_KEY หรือ GEMINI_API_KEY"}), 500

        # EXP is locked by system. Do not trust editable/browser-submitted value.
        if mode == "auto":
            auto_exp = calculate_auto_exp(market_type, expected_mfg)
            expected_exp = auto_exp if auto_exp else ""
            skip_exp = not bool(expected_exp)
        else:
            auto_exp = calculate_exp(product_type, market_type, expected_mfg, epc_laos_exp_months)
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
            # BATCH OCR TIMEOUT FIX:
            # 4 pouch images + 1 carton image are sent to the OCR provider in ONE request.
            # This avoids Render/Gunicorn timeout caused by many slow sequential/concurrent OCR calls.
            carton_market_type = "EXPORT" if market_type == "LAOS" else market_type
            carton_check_exp = original_market_type != "LAOS"
            carton_expected_exp = expected_exp if carton_check_exp else ""

            batch_result = read_both_batch_with_ai(
                pouches=pouches,
                carton_image_base64=carton_image_data,
                product_type=product_type,
                market_type=original_market_type,
                mode=mode,
            )

            pouch_results = []
            for idx, pouch_item in enumerate(pouches, start=1):
                line_code = pouch_item.get("line", "").strip().upper()
                pouch_entry = batch_result.get("pouches", {}).get(idx, {})
                pouch_lines_i = pouch_entry.get("lines", []) if isinstance(pouch_entry, dict) else []
                if mode == "sachet":
                    pouch_overall_i, pouch_details_i = check_pouch_sachet(
                        pouch_lines_i, product_type, market_type, expected_mfg, line_code, expected_exp
                    )
                elif mode == "auto":
                    pouch_overall_i, pouch_details_i = check_pouch_auto(
                        pouch_lines_i, market_type, expected_mfg, line_code, expected_exp
                    )
                else:
                    ai_time_i = ""
                    raw_entry = pouch_entry.get("raw", {}) if isinstance(pouch_entry, dict) else {}
                    if isinstance(raw_entry, dict):
                        ai_time_i = raw_entry.get("time", "")
                    pouch_overall_i, pouch_details_i = check_pouch_linapack(
                        pouch_lines_i, product_type, market_type, expected_mfg, line_code, expected_exp, mix_code, ai_time_i, epc_laos_exp_months
                    )
                pouch_results.append({
                    "index": idx,
                    "line": line_code,
                    "image": pouch_item.get("image", ""),
                    "json": pouch_entry,
                    "lines": pouch_lines_i,
                    "overall": pouch_overall_i,
                    "details": pouch_details_i,
                })

            carton_json = batch_result.get("carton", {})
            carton_lines = carton_json.get("lines", []) if isinstance(carton_json, dict) else []

            mode_name = "Sachet + Carton" if mode == "sachet" else ("Auto + Carton" if mode == "auto" else "Linapack + Carton")

            carton_overall, carton_details = check_carton(
                carton_lines, carton_market_type, expected_mfg, carton_expected_exp, building_no, building_suffix,
                shipping_mark, carton_alpha_code, carton_json, check_exp=carton_check_exp
            )

            details = []
            for pr in pouch_results:
                for d in pr["details"]:
                    d = dict(d)
                    d["item"] = f"ซองเครื่อง {pr['index']} - " + str(d.get("item", ""))
                    details.append(d)
            for d in carton_details:
                d = dict(d)
                d["item"] = "กล่อง - " + str(d.get("item", ""))
                details.append(d)

            overall = bool(all(pr["overall"] for pr in pouch_results) and carton_overall)
            check_type_name = "POUCH + CARTON"
            lines = {f"pouch{pr['index']}": pr["lines"] for pr in pouch_results}
            lines["carton"] = carton_lines
            image_data = pouches[0].get("image", "")
        else:
            image_base64 = normalize_image_base64_for_ai(image_data)
            raw_ai = read_lot_with_ai(
                image_base64, check_type, mode, product_type, original_market_type if (check_type == "carton" and original_market_type == "LAOS") else market_type, expected_mfg, expected_line,
                expected_exp, mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code
            )
            result_json = json.loads(clean_json_text(raw_ai))
            lines = result_json.get("lines", [])

        if check_type != "both" and check_type == "carton":
            carton_check_exp = original_market_type != "LAOS"
            carton_expected_exp = expected_exp if carton_check_exp else ""
            overall, details = check_carton(
                lines,
                market_type,
                expected_mfg,
                carton_expected_exp,
                building_no,
                building_suffix,
                shipping_mark,
                carton_alpha_code,
                result_json,
                check_exp=carton_check_exp
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
        elif check_type != "both" and mode == "auto":
            overall, details = check_pouch_auto(
                lines,
                market_type,
                expected_mfg,
                expected_line,
                expected_exp
            )
            mode_name = "Auto"
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
            carton_image_data if check_type == "both" else None,
            pouch2_image_data if check_type == "both" else None,
            [item.get("image", "") for item in pouches[1:]] if check_type == "both" else None
        )

        def build_expected_pouch(line_code):
            if mode == "sachet":
                return f"MFG {expected_mfg} {line_code} 1" + (f" EXP {expected_exp}" if expected_exp else "")
            if mode == "auto":
                return f"MFG {expected_mfg} {line_code}" + (f" EXP {expected_exp}" if expected_exp else "")
            line1 = f"MFG {expected_mfg}"
            if linapack_requires_mix(product_type, market_type) and mix_code:
                line1 += f" {mix_code}"
            line1 += f" {line_code} เวลา"
            return line1 + (f" / EXP {expected_exp}" if expected_exp else "")

        if check_type == "both":
            expected_pouch_lot = " | ".join(
                [f"เครื่อง {idx}: " + build_expected_pouch(item.get("line", "")) for idx, item in enumerate(pouches, start=1)]
            )
        else:
            expected_pouch_lot = "เครื่อง 1: " + build_expected_pouch(expected_line)

        if market_type == "TH":
            expected_carton_lot = f"00001 00 {expected_mfg} {building_no}{(' ' + building_suffix) if building_suffix else ''}".strip()
        else:
            if shipping_mark:
                expected_carton_lot = f"{shipping_mark} 00001 {carton_alpha_code} {expected_mfg} {building_no}{(' ' + building_suffix) if building_suffix else ''}".strip()
            else:
                expected_carton_lot = f"00001 {carton_alpha_code} {expected_mfg} {building_no}{(' ' + building_suffix) if building_suffix else ''}".strip()

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
        return jsonify({"error": friendly_error_message(e) or ("ตรวจสอบไม่สำเร็จ: " + e.__class__.__name__)}), 500


def _run_check_job(job_id, data):
    try:
        with app.app_context():
            resp = _check_sync_from_data(data)
            status_code = 200
            if isinstance(resp, tuple):
                flask_resp, status_code = resp[0], resp[1]
            else:
                flask_resp = resp
                status_code = getattr(resp, "status_code", 200)
            try:
                payload = flask_resp.get_json(silent=True) or {}
            except Exception:
                payload = {"error": "หลังบ้านไม่ได้ส่ง JSON กลับมา"}
                status_code = 500
        with JOBS_LOCK:
            if status_code >= 400:
                JOBS[job_id].update({"status": "error", "error": payload.get("error") or payload.get("message") or f"HTTP {status_code}", "updated": time.time()})
                _save_job(job_id, JOBS[job_id])
            else:
                JOBS[job_id].update({"status": "done", "result": payload, "updated": time.time()})
                _save_job(job_id, JOBS[job_id])
    except Exception as e:
        with JOBS_LOCK:
            if job_id in JOBS:
                JOBS[job_id].update({"status": "error", "error": friendly_error_message(e) or str(e), "updated": time.time()})
                _save_job(job_id, JOBS[job_id])

@app.route("/check", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}
    _cleanup_jobs()
    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {"status": "queued", "created": time.time(), "updated": time.time()}
        _save_job(job_id, JOBS[job_id])
    OCR_EXECUTOR.submit(_run_check_job, job_id, data)
    return jsonify({"status": "queued", "jobId": job_id, "message": "เริ่มตรวจสอบแล้ว ระบบจะประมวลผลต่อหลังบ้าน"}), 202

@app.route("/check_status/<job_id>")
def check_status(job_id):
    _cleanup_jobs()
    with JOBS_LOCK:
        job = JOBS.get(job_id) or _load_job(job_id)
        if not job:
            return jsonify({"status": "error", "error": "ไม่พบงานตรวจสอบ อาจหมดอายุแล้ว กรุณากดตรวจใหม่"}), 404
        return jsonify(dict(job))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
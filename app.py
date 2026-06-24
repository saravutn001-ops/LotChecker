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


HTML = '<!DOCTYPE html>\n<html lang="th">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n<title>IP ONE Lot Checker</title>\n<link rel="icon" type="image/png" href="data:image/png;base64,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">\n<link rel="shortcut icon" type="image/png" href="data:image/png;base64,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">\n<link rel="apple-touch-icon" href="data:image/png;base64,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">\n<style>\n:root{--blue:#0b63ce;--navy:#071f38;--bg:#eef4fb;--card:#fff;--text:#0f172a;--muted:#64748b;--border:#dbe4ef;--green:#16a34a;--red:#dc2626;}\n*{box-sizing:border-box}\nhtml,body{margin:0;padding:0;font-family:Arial,\'Tahoma\',sans-serif;background:var(--bg);color:var(--text);}\nbody{padding:10px;}\n.app{max-width:1180px;margin:0 auto;}\n.header{display:flex;align-items:center;justify-content:center;gap:12px;background:var(--navy);color:#fff;border-radius:18px;padding:12px 14px;box-shadow:0 8px 24px rgba(15,23,42,.18);text-align:left;}\n.logo{width:52px;height:52px;object-fit:contain;background:#fff;border-radius:12px;padding:5px;}\n.header h1{font-size:22px;margin:0;line-height:1.1;}\n.header p{margin:3px 0 0;font-size:12px;color:#cbd5e1;}\n.card{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:14px;margin-top:12px;box-shadow:0 6px 18px rgba(15,23,42,.06);}\n.card-title{display:flex;align-items:center;gap:8px;font-weight:800;font-size:16px;margin-bottom:12px;color:#0f172a;}\n.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;}\n.field{min-width:0;}\n.field label{display:block;font-size:13px;font-weight:700;color:#475569;margin:0 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}\n.field input,.field select{width:100%;height:44px;line-height:44px;font-size:15px;padding:0 12px;border:1px solid var(--border);border-radius:12px;background:#fff;color:var(--text);outline:none;min-width:0;}\n.field input:focus,.field select:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(11,99,206,.12)}\n.field input[readonly],.field select:disabled{background:#f8fafc;color:#64748b;}\n.hidden{display:none!important;}\n.photo-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;}\n.photo-card{border:1px dashed #c8d5e4;border-radius:16px;padding:12px;background:#f8fbff;}\n.photo-card h3{margin:0 0 8px;font-size:15px;}\n.file-btn{display:block;width:100%;text-align:center;background:#eaf3ff;border:1px solid #b9d7ff;color:#0757b7;border-radius:12px;padding:12px;font-weight:800;cursor:pointer;}\n.file-btn input{display:none;}\n.preview{display:none;width:100%;max-height:300px;object-fit:contain;margin-top:10px;border-radius:14px;background:#0f172a;border:1px solid var(--border);}\n.time-label{font-size:12px;color:var(--muted);margin-top:6px;}\n.actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}\nbutton{border:0;border-radius:14px;padding:13px 14px;font-size:16px;font-weight:800;color:#fff;background:linear-gradient(135deg,var(--blue),#084c9e);cursor:pointer;}\nbutton.secondary{background:#475569;}\nbutton.success{background:linear-gradient(135deg,#16a34a,#15803d);font-size:18px;}\nbutton.danger{background:#dc2626;}\nbutton:disabled{opacity:.55;cursor:not-allowed;}\n.toast{position:fixed;top:16px;left:50%;transform:translateX(-50%);background:#16a34a;color:#fff;padding:12px 18px;border-radius:14px;font-weight:800;z-index:100000;box-shadow:0 10px 28px rgba(0,0,0,.25);max-width:92vw;text-align:center;}\n.toast.error{background:#dc2626;}\n.camera-modal{display:none;position:fixed;inset:0;background:#000;z-index:99999;flex-direction:column;}\n.camera-modal.active{display:flex;}\n.camera-wrap{position:relative;flex:1;display:flex;align-items:center;justify-content:center;background:#000;overflow:hidden;}\n#cameraVideo{width:100%;height:100%;object-fit:contain;background:#000;}\n.scan-guide{position:absolute;left:14%;top:38%;width:72%;height:22%;border:4px solid #22c55e;border-radius:18px;box-shadow:0 0 0 9999px rgba(0,0,0,.12);pointer-events:none;}\n.camera-toolbar{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;background:#111827;padding:12px;padding-bottom:calc(12px + env(safe-area-inset-bottom));}\n.result-modal{display:none;position:fixed;inset:0;background:rgba(15,23,42,.72);z-index:99998;align-items:center;justify-content:center;padding:16px;}\n.result-modal.active{display:flex;}\n.result-box{background:#fff;border-radius:22px;width:min(980px,96vw);max-height:92vh;overflow:auto;box-shadow:0 24px 70px rgba(0,0,0,.35);}\n.result-head{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;color:#fff;border-radius:22px 22px 0 0;}\n.result-head.pass{background:#16a34a;}\n.result-head.ng{background:#dc2626;}\n.result-head h2{margin:0;font-size:22px;}\n.close-x{background:rgba(255,255,255,.18);width:44px;height:44px;border-radius:999px;padding:0;font-size:26px;line-height:44px;}\n.result-body{padding:14px;}\n.evidence{display:block;width:100%;max-height:58vh;object-fit:contain;background:#f8fafc;border:1px solid var(--border);border-radius:16px;}\n.result-summary{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}\n.result-mini{background:#f8fafc;border:1px solid var(--border);border-radius:14px;padding:10px;font-size:14px;}\n.result-mini b{display:block;color:#334155;margin-bottom:4px;}\n.ng-list{margin-top:12px;background:#fff7f7;border:1px solid #fecaca;border-radius:14px;padding:10px;}\n.ng-list ul{margin:6px 0 0 20px;padding:0;}\n.share-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:12px;}\n@media (max-width:720px){\n body{padding:8px;background:#f2f7fd;}\n .header{border-radius:16px;padding:10px;justify-content:center;}\n .logo{width:46px;height:46px;}\n .header h1{font-size:19px;}\n .grid{grid-template-columns:1fr;gap:10px;}\n .photo-grid{grid-template-columns:1fr;}\n .actions{grid-template-columns:1fr;}\n .card{padding:12px;border-radius:16px;margin-top:10px;}\n .field input,.field select{height:48px;line-height:48px;font-size:16px;}\n .camera-toolbar{grid-template-columns:1fr;}\n .result-box{width:100vw;max-height:100vh;border-radius:0;}\n .result-head{border-radius:0;}\n .result-summary,.share-row{grid-template-columns:1fr;}\n .evidence{max-height:44vh;}\n}\n\n.dynamic-machine-list{grid-column:1/-1;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;}\n.dynamic-pouch-cards{display:contents;}\n.dynamic-machine-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:12px;}\n.machine-card-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px;}\n.machine-card-head b{font-size:14px;}\n.btn-small{width:auto;padding:8px 10px;font-size:13px;margin:0;}\n.camera-toolbar #extraCaptureButtons{display:contents;}\n@media(max-width:720px){.dynamic-machine-list{grid-template-columns:1fr;} .camera-toolbar #extraCaptureButtons{display:contents;}}\n</style>\n</head>\n<body>\n<div class="app">\n  <div class="header">\n    <img class="logo" src="data:image/png;base64,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" alt="IP One Logo">\n    <div><h1>IP ONE LOT CHECKER</h1><p>POUCH + CARTON VERIFICATION</p></div>\n  </div>\n\n  <div class="card">\n    <div class="card-title">ตั้งค่าการตรวจ</div>\n    <div class="grid">\n      <div class="field"><label>ประเภทไลน์</label><select id="mode"><option value="">เลือกประเภทไลน์</option><option value="linapack">Linapack</option><option value="sachet">Sachet</option></select></div>\n      <div class="field"><label>เครื่องซองที่ 1</label><select id="line" disabled><option value="">เลือกประเภทไลน์ก่อน</option></select></div>\n      <div class="field" id="addMachineField"><label>&nbsp;</label><button type="button" class="secondary" id="addPouchMachineBtn">+ เพิ่มเครื่องซอง</button></div>\n      <div id="extraMachineFields" class="dynamic-machine-list"></div>\n      <div class="field"><label>ผลิตภัณฑ์</label><select id="productType"><option value="">เลือกผลิตภัณฑ์</option><option value="EPC">EPC</option><option value="EPW">EPW</option></select></div>\n      <div class="field"><label>ประเภทงาน</label><select id="marketType"><option value="">เลือกประเภทงาน</option><option value="TH">งานไทย</option><option value="EXPORT">งานต่างประเทศ</option><option value="LAOS">งานต่างประเทศ ลาว</option></select></div>\n      <div class="field"><label>วันที่ผลิต</label><input type="date" id="mfgDate"></div>\n      <div class="field mix-field" id="mixDateField"><label>วันที่ผสม</label><input type="date" id="mixDate"></div>\n      <div class="field mix-field" id="mixCodeField"><label>Mix Code</label><input id="mixCode" readonly placeholder="Auto"></div>\n    </div>\n    <input type="hidden" id="mfg"><input type="hidden" id="exp">\n  </div>\n\n  <div class="card">\n    <div class="card-title">ข้อมูลล็อตกล่อง</div>\n    <div class="grid">\n      <div class="field"><label>Shipping Mark</label><input id="shippingMark" readonly placeholder="เลือก Prefix"></div>\n      <div class="field"><label>Prefix</label><select id="cartonPrefix" disabled><option value="">เลือกประเภทงานก่อน</option></select></div>\n      <div class="field"><label>เลขอาคาร</label><select id="buildingNo"><option value="">เลือกเลขอาคาร</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option><option value="6">6</option></select></div>\n      <div class="field"><label>Suffix</label><input id="buildingSuffix" placeholder="เช่น QR / N"></div>\n    </div>\n  </div>\n\n  <div class="card">\n    <div class="card-title">รูปสำหรับตรวจ</div>\n    <div class="photo-grid">\n      <div class="photo-card"><h3>รูปซอง เครื่องที่ 1</h3><label class="file-btn">เลือกรูปซองเครื่องที่ 1<input type="file" id="fileInputPouch" accept="image/*"></label><img id="previewPouch" class="preview"><div id="pouchTime" class="time-label"></div></div>\n      <div id="extraPouchCards" class="dynamic-pouch-cards"></div>\n      <div class="photo-card"><h3>รูปกล่อง</h3><label class="file-btn">เลือกรูปกล่อง<input type="file" id="fileInputCarton" accept="image/*"></label><img id="previewCarton" class="preview"><div id="cartonTime" class="time-label"></div></div>\n    </div>\n    <div class="actions"><button type="button" id="openCameraBtn">เปิดกล้อง</button><button type="button" class="success" id="checkBtn">ตรวจสอบล็อตซอง + กล่อง</button></div>\n  </div>\n</div>\n\n<div class="camera-modal" id="cameraModal">\n  <div class="camera-wrap"><video id="cameraVideo" autoplay playsinline muted></video><div class="scan-guide"></div></div>\n  <div class="camera-toolbar"><button type="button" id="capturePouchBtn">ถ่ายซอง 1</button><span id="extraCaptureButtons"></span><button type="button" id="captureCartonBtn">ถ่ายกล่อง</button><button type="button" class="danger" id="closeCameraBtn">ปิดกล้อง</button></div>\n</div>\n<canvas id="cameraCanvas" class="hidden"></canvas>\n\n<div class="result-modal" id="resultModal">\n  <div class="result-box">\n    <div class="result-head" id="resultHead"><h2 id="resultTitle">ผลตรวจ</h2><button type="button" class="close-x" id="closeResultBtn">×</button></div>\n    <div class="result-body">\n      <img id="evidenceImg" class="evidence" alt="หลักฐานการตรวจ">\n      <div class="result-summary">\n        <div class="result-mini"><b>Lot ซองที่ควรเป็น</b><span id="expectedPouchLot">-</span></div>\n        <div class="result-mini"><b>Lot กล่องที่ควรเป็น</b><span id="expectedCartonLot">-</span></div>\n      </div>\n      <div class="ng-list" id="ngBox"><b>รายการ NG</b><div id="ngContent">-</div></div>\n      <div class="share-row"><button type="button" id="shareBtn">แชร์รูปเข้า LINE / แอปอื่น</button><button type="button" class="secondary" id="closeResultBtn2">ปิด</button></div>\n    </div>\n  </div>\n</div>\n\n<script>\nconst $ = (id) => document.getElementById(id);\nlet pouchImageData = "";\nlet cartonImageData = "";\nlet cameraStream = null;\nlet lastResult = null;\nlet pouchMachines = [];\nconst PREFIX_SHIPPING_MAP = {"KC": "ZZZZZ", "VN": "IPO VN", "VT": "VN-MT", "KK": "AKK", "CT": "CDT", "TS": "TS", "AC": "AKC", "SM": "SOMCHAICHALUEN", "AX": "AKX", "MM": "I.P. ONE-MYANMAR", "ML": "ML", "KT": "KT", "MW": "MWD", "MK": "MK", "MY": "MDY", "TG": "TG", "MN": "MNJM", "MA": "MLA", "LM": "MT/LM+VY", "DK": "DKSH", "NT": "NTPL", "XR": "XR", "BU": "BUL", "UK": "U,K,T-7", "DB": "DBL INDUSTRIES PLC", "OL": "IMPORTER:ORGANIC LINE CO., LTD", "OD": "IMPORTER:ORGANIC LINE CO., LTD", "MI": "ZZZZZ", "WD": "WEDAR", "CZ": "ZZZZZ", "ND": "NDF", "CS": "CSMS", "FN": "FENIX", "CD": "CDM", "DT": "DBT", "YP": "YPG", "LB": "ZZZZZ", "LQ": "ZZZZZ"};\nconst EXPORT_PREFIXES = ["KC", "VN", "VT", "KK", "CT", "TS", "AC", "SM", "AX", "MM", "ML", "KT", "MW", "MK", "MY", "TG", "MN", "MA", "LM", "DK", "NT", "XR", "BU", "UK", "DB", "OL", "OD", "MI", "WD", "CZ", "ND", "CS", "FN", "CD", "DT", "YP", "LB", "LQ"];\n\nconst MONTH_CODES = ["A","B","C","D","E","F","G","H","I","J","K","L"];\nfunction showToast(msg, type="success"){ const t=document.createElement("div"); t.className="toast"+(type==="error"?" error":""); t.textContent=msg; document.body.appendChild(t); setTimeout(()=>t.remove(),2600); }\nfunction ddmmyyFromDate(v){ if(!v) return ""; const [y,m,d]=v.split("-"); return `${d}${m}${String(y).slice(-2)}`; }\nfunction addMonths(dateStr, months){ if(!dateStr) return ""; const [y,m,d]=dateStr.split("-").map(Number); const dt=new Date(y,m-1,d); dt.setMonth(dt.getMonth()+months); return `${String(dt.getDate()).padStart(2,"0")}${String(dt.getMonth()+1).padStart(2,"0")}${String(dt.getFullYear()).slice(-2)}`; }\nfunction updateDates(){ $("mfg").value=ddmmyyFromDate($("mfgDate").value); const p=$("productType").value, market=$("marketType").value; let exp=""; if(p==="EPC" && market==="TH") exp=addMonths($("mfgDate").value,15); if(p==="EPW" && market==="LAOS") exp=addMonths($("mfgDate").value,36); $("exp").value=exp; }\nfunction updateMix(){ const v=$("mixDate").value; if(!v){ $("mixCode").value=""; return; } const [y,m,d]=v.split("-"); $("mixCode").value=`${d}${MONTH_CODES[Number(m)-1]}`; }\nfunction updateProductUI(){ const isEPC=$("productType").value==="EPC"; document.querySelectorAll(".mix-field").forEach(el=>el.classList.toggle("hidden", isEPC)); if(isEPC){ $("mixDate").value=""; $("mixCode").value=""; } updateDates(); }\nfunction machineListForMode(mode){ if(mode==="linapack") return ["LP1","LP2","LP3","LP4","LP5","LP6","LP7","LP8","LP9"]; if(mode==="sachet") return ["MS1","MS2","MS3","MS4","MS5","MS6","MS7","MS8","MS9","MS10","MS11","MS12","AS1","AS2"]; return []; }\nfunction fillMachineSelect(sel, mode, placeholder){ if(!sel) return; sel.innerHTML=""; const list=machineListForMode(mode); sel.disabled=list.length===0; if(!list.length){ sel.innerHTML="<option value="">\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e1b\u0e23\u0e30\u0e40\u0e20\u0e17\u0e44\u0e25\u0e19\u0e4c\u0e01\u0e48\u0e2d\u0e19</option>"; return; } sel.insertAdjacentHTML("beforeend", `<option value="">${placeholder}</option>`); list.forEach(x=>sel.insertAdjacentHTML("beforeend", `<option value="${x}">${x}</option>`)); sel.value=""; }\nfunction updateAllMachineOptions(){ const mode=$("mode").value; fillMachineSelect($("line"), mode, "\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07"); pouchMachines.forEach(pm=>fillMachineSelect($(pm.lineId), mode, `\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e0b\u0e2d\u0e07\u0e17\u0e35\u0e48 ${pm.index}`)); }\nfunction updateMarketUI(){ const market=$("marketType").value; const prefix=$("cartonPrefix"); prefix.innerHTML=""; $("shippingMark").value=""; if(!market){ prefix.disabled=true; prefix.innerHTML="<option value="">\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e1b\u0e23\u0e30\u0e40\u0e20\u0e17\u0e07\u0e32\u0e19\u0e01\u0e48\u0e2d\u0e19</option>"; } else if(market==="TH"){ prefix.disabled=true; prefix.innerHTML="<option value="00">00</option>"; prefix.value="00"; $("shippingMark").value="-"; } else { prefix.disabled=false; prefix.innerHTML="<option value="">\u0e40\u0e25\u0e37\u0e2d\u0e01 Prefix</option>"; EXPORT_PREFIXES.forEach(p=>prefix.insertAdjacentHTML("beforeend", `<option value="${p}">${p}</option>`)); } updateDates(); }\nfunction updateShippingMark(){ const p=$("cartonPrefix").value, market=$("marketType").value; $("shippingMark").value = market==="TH" ? "-" : (p ? (PREFIX_SHIPPING_MAP[p] || "") : ""); }\nfunction setPreview(which, data){ const map={pouch:["previewPouch","pouchTime"], carton:["previewCarton","cartonTime"]}; if(which.startsWith("pouch_")){ const id=which.split("_")[1]; map[which]=[`previewPouch_${id}`,`pouchTime_${id}`]; } const pair=map[which] || map.pouch; const img=$(pair[0]), tm=$(pair[1]); if(img){ img.src=data; img.style.display="block"; } if(tm) tm.textContent="\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e25\u0e48\u0e32\u0e2a\u0e38\u0e14 "+new Date().toLocaleTimeString("th-TH",{hour12:false}); }\nfunction handleFile(which, input){ const f=input.files && input.files[0]; if(!f) return; const r=new FileReader(); r.onload=()=>{ if(which==="pouch") pouchImageData=r.result; else if(which==="carton") cartonImageData=r.result; else if(which.startsWith("pouch_")){ const id=which.split("_")[1]; const pm=pouchMachines.find(x=>String(x.id)===String(id)); if(pm) pm.image=r.result; } setPreview(which,r.result); showToast("\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e23\u0e39\u0e1b\u0e40\u0e23\u0e35\u0e22\u0e1a\u0e23\u0e49\u0e2d\u0e22"); }; r.readAsDataURL(f); }\nfunction addPouchMachine(){ const index=pouchMachines.length+2; const id=Date.now().toString(36)+Math.random().toString(36).slice(2,6); const pm={id,index,lineId:`line_${id}`,fileId:`fileInputPouch_${id}`,previewId:`previewPouch_${id}`,timeId:`pouchTime_${id}`,captureId:`capturePouch_${id}`,image:""}; pouchMachines.push(pm); const machineHtml=`<div class="dynamic-machine-card" id="machineCard_${id}"><div class="machine-card-head"><b>\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e0b\u0e2d\u0e07\u0e17\u0e35\u0e48 ${index}</b><button type="button" class="secondary btn-small" data-remove-pouch="${id}">\u0e25\u0e1a</button></div><select id="${pm.lineId}"></select></div>`; $("extraMachineFields").insertAdjacentHTML("beforeend", machineHtml); const photoHtml=`<div class="photo-card" id="pouchCard_${id}"><h3>\u0e23\u0e39\u0e1b\u0e0b\u0e2d\u0e07 \u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e17\u0e35\u0e48 ${index}</h3><label class="file-btn">\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e23\u0e39\u0e1b\u0e0b\u0e2d\u0e07\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e17\u0e35\u0e48 ${index}<input type="file" id="${pm.fileId}" accept="image/*"></label><img id="${pm.previewId}" class="preview"><div id="${pm.timeId}" class="time-label"></div></div>`; $("extraPouchCards").insertAdjacentHTML("beforeend", photoHtml); $("extraCaptureButtons").insertAdjacentHTML("beforeend", `<button type="button" id="${pm.captureId}">\u0e16\u0e48\u0e32\u0e22\u0e0b\u0e2d\u0e07 ${index}</button>`); fillMachineSelect($(pm.lineId), $("mode").value, `\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e0b\u0e2d\u0e07\u0e17\u0e35\u0e48 ${index}`); $(pm.fileId).addEventListener("change", e=>handleFile(`pouch_${id}`, e.target)); $(pm.captureId).addEventListener("click", ()=>captureTo(`pouch_${id}`)); const removeBtn=document.querySelector(`[data-remove-pouch="${id}"]`); if(removeBtn) removeBtn.addEventListener("click",()=>removePouchMachine(id)); }\nfunction removePouchMachine(id){ pouchMachines = pouchMachines.filter(pm=>String(pm.id)!==String(id)); [`machineCard_${id}`,`pouchCard_${id}`,`capturePouch_${id}`].forEach(x=>{ const el=$(x); if(el) el.remove(); }); renumberPouchMachines(); }\nfunction renumberPouchMachines(){ pouchMachines.forEach((pm,i)=>{ pm.index=i+2; const mc=$(`machineCard_${pm.id}`); if(mc){ const b=mc.querySelector("b"); if(b) b.textContent=`\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e0b\u0e2d\u0e07\u0e17\u0e35\u0e48 ${pm.index}`; } const pc=$(`pouchCard_${pm.id}`); if(pc){ const h=pc.querySelector("h3"); if(h) h.textContent=`\u0e23\u0e39\u0e1b\u0e0b\u0e2d\u0e07 \u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e17\u0e35\u0e48 ${pm.index}`; const label=pc.querySelector("label.file-btn"); if(label && label.firstChild) label.firstChild.textContent=`\u0e40\u0e25\u0e37\u0e2d\u0e01\u0e23\u0e39\u0e1b\u0e0b\u0e2d\u0e07\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e17\u0e35\u0e48 ${pm.index}`; } const cap=$(pm.captureId); if(cap) cap.textContent=`\u0e16\u0e48\u0e32\u0e22\u0e0b\u0e2d\u0e07 ${pm.index}`; }); }\nasync function openCamera(){ try{ cameraStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"}, width:{ideal:1920}, height:{ideal:1080}}, audio:false}); $("cameraVideo").srcObject=cameraStream; $("cameraModal").classList.add("active"); }catch(e){ showToast("\u0e40\u0e1b\u0e34\u0e14\u0e01\u0e25\u0e49\u0e2d\u0e07\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49: "+e.message,"error"); } }\nfunction closeCamera(){ if(cameraStream) cameraStream.getTracks().forEach(t=>t.stop()); cameraStream=null; $("cameraVideo").srcObject=null; $("cameraModal").classList.remove("active"); }\nfunction captureTo(which){ const v=$("cameraVideo"); if(!v.videoWidth) return showToast("\u0e22\u0e31\u0e07\u0e44\u0e21\u0e48\u0e1e\u0e1a\u0e20\u0e32\u0e1e\u0e08\u0e32\u0e01\u0e01\u0e25\u0e49\u0e2d\u0e07","error"); const c=$("cameraCanvas"); c.width=v.videoWidth; c.height=v.videoHeight; c.getContext("2d").drawImage(v,0,0,c.width,c.height); const data=c.toDataURL("image/jpeg",0.92); if(which==="pouch") pouchImageData=data; else if(which==="carton") cartonImageData=data; else if(which.startsWith("pouch_")){ const id=which.split("_")[1]; const pm=pouchMachines.find(x=>String(x.id)===String(id)); if(pm) pm.image=data; } setPreview(which,data); showToast("\u0e1a\u0e31\u0e19\u0e17\u0e36\u0e01\u0e23\u0e39\u0e1b\u0e40\u0e23\u0e35\u0e22\u0e1a\u0e23\u0e49\u0e2d\u0e22"); }\nfunction getPouchesForPayload(){ const list=[]; list.push({line:$("line").value, image:pouchImageData}); pouchMachines.forEach(pm=>{ const sel=$(pm.lineId); list.push({line: sel ? sel.value : "", image: pm.image || ""}); }); return list; }\nfunction validateBeforeCheck(){ const miss=[]; if(!$("mode").value) miss.push("\u0e1b\u0e23\u0e30\u0e40\u0e20\u0e17\u0e44\u0e25\u0e19\u0e4c"); if(!$("line").value) miss.push("\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e0b\u0e2d\u0e07\u0e17\u0e35\u0e48 1"); if(!$("productType").value) miss.push("\u0e1c\u0e25\u0e34\u0e15\u0e20\u0e31\u0e13\u0e11\u0e4c"); if(!$("marketType").value) miss.push("\u0e1b\u0e23\u0e30\u0e40\u0e20\u0e17\u0e07\u0e32\u0e19"); if(!$("mfgDate").value) miss.push("\u0e27\u0e31\u0e19\u0e17\u0e35\u0e48\u0e1c\u0e25\u0e34\u0e15"); if($("productType").value==="EPW" && !$("mixDate").value) miss.push("\u0e27\u0e31\u0e19\u0e17\u0e35\u0e48\u0e1c\u0e2a\u0e21"); if(($("marketType").value==="EXPORT"||$("marketType").value==="LAOS") && !$("cartonPrefix").value) miss.push("Prefix"); if(!$("buildingNo").value) miss.push("\u0e40\u0e25\u0e02\u0e2d\u0e32\u0e04\u0e32\u0e23"); if(!pouchImageData) miss.push("\u0e23\u0e39\u0e1b\u0e0b\u0e2d\u0e07\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e17\u0e35\u0e48 1"); if(!cartonImageData) miss.push("\u0e23\u0e39\u0e1b\u0e01\u0e25\u0e48\u0e2d\u0e07"); pouchMachines.forEach(pm=>{ const sel=$(pm.lineId); if(!sel || !sel.value) miss.push(`\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e0b\u0e2d\u0e07\u0e17\u0e35\u0e48 ${pm.index}`); if(!pm.image) miss.push(`\u0e23\u0e39\u0e1b\u0e0b\u0e2d\u0e07\u0e40\u0e04\u0e23\u0e37\u0e48\u0e2d\u0e07\u0e17\u0e35\u0e48 ${pm.index}`); }); if(miss.length){ showToast("\u0e01\u0e23\u0e38\u0e13\u0e32\u0e40\u0e25\u0e37\u0e2d\u0e01/\u0e01\u0e23\u0e2d\u0e01: "+miss.join(", "),"error"); return false; } return true; }\nasync function sendCheck(){ updateDates(); updateMix(); updateShippingMark(); if(!validateBeforeCheck()) return; $("checkBtn").disabled=true; $("checkBtn").textContent="\u0e01\u0e33\u0e25\u0e31\u0e07\u0e15\u0e23\u0e27\u0e08\u0e2a\u0e2d\u0e1a..."; try{ const pouches=getPouchesForPayload(); const payload={checkType:"both", mode:$("mode").value, productType:$("productType").value, marketType:$("marketType").value, mfg:$("mfg").value, line:$("line").value, exp:$("exp").value, mixCode:$("mixCode").value, pouchImage:pouchImageData, cartonImage:cartonImageData, pouches:pouches, buildingNo:$("buildingNo").value, buildingSuffix:$("buildingSuffix").value, shippingMark:$("shippingMark").value, cartonAlphaCode:$("marketType").value==="TH"?"00":$("cartonPrefix").value}; const res=await fetch("/check",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); const data=await res.json(); if(!res.ok) throw new Error(data.error||"\u0e15\u0e23\u0e27\u0e08\u0e2a\u0e2d\u0e1a\u0e44\u0e21\u0e48\u0e2a\u0e33\u0e40\u0e23\u0e47\u0e08"); showResult(data); }catch(e){ showToast(e.message,"error"); } finally{ $("checkBtn").disabled=false; $("checkBtn").textContent="\u0e15\u0e23\u0e27\u0e08\u0e2a\u0e2d\u0e1a\u0e25\u0e47\u0e2d\u0e15\u0e0b\u0e2d\u0e07 + \u0e01\u0e25\u0e48\u0e2d\u0e07"; } }\nfunction showResult(data){ lastResult=data; const pass=data.summary==="PASS"; $("resultHead").className="result-head "+(pass?"pass":"ng"); $("resultTitle").textContent=pass?"PASS":"NG"; $("evidenceImg").src=data.stampedImageUrl; $("expectedPouchLot").textContent=data.expectedPouchLot||"-"; $("expectedCartonLot").textContent=data.expectedCartonLot||"-"; const ngs=(data.details||[]).filter(d=>d.status==="NG"); $("ngContent").innerHTML=ngs.length?"<ul>"+ngs.map(d=>`<li><b>${d.item}</b>: \u0e2d\u0e48\u0e32\u0e19\u0e44\u0e14\u0e49 ${d.actual||"-"} / \u0e04\u0e27\u0e23\u0e40\u0e1b\u0e47\u0e19 ${d.expected||"-"}</li>`).join("")+"</ul>":"\u0e44\u0e21\u0e48\u0e1e\u0e1a\u0e23\u0e32\u0e22\u0e01\u0e32\u0e23 NG"; $("resultModal").classList.add("active"); }\nfunction closeResult(){ $("resultModal").classList.remove("active"); }\nfunction formatShareDate(){ const now=new Date(); return `${String(now.getDate()).padStart(2,"0")}/${String(now.getMonth()+1).padStart(2,"0")}/${now.getFullYear()} ${String(now.getHours()).padStart(2,"0")}:${String(now.getMinutes()).padStart(2,"0")}:${String(now.getSeconds()).padStart(2,"0")}`; }\nasync function shareResult(){ if(!lastResult) return; const machineText=getPouchesForPayload().map(x=>x.line).filter(v=>v && v.trim()).join(", ") || "-"; const text=`\u0e44\u0e25\u0e19\u0e4c ${machineText} \u0e15\u0e23\u0e27\u0e08\u0e2a\u0e2d\u0e1a\u0e04\u0e27\u0e32\u0e21\u0e16\u0e39\u0e01\u0e15\u0e49\u0e2d\u0e07\u0e02\u0e2d\u0e07 Lot \u0e41\u0e25\u0e49\u0e27 (${lastResult.summary})\\n\\n\u0e27\u0e31\u0e19\u0e17\u0e35\u0e48 ${formatShareDate()}`; try{ const resp=await fetch(lastResult.stampedImageUrl); const blob=await resp.blob(); const file=new File([blob],"lot-check.jpg",{type:"image/jpeg"}); if(navigator.canShare && navigator.canShare({files:[file]})) await navigator.share({text,files:[file]}); else if(navigator.share) await navigator.share({text,url:location.origin+lastResult.stampedImageUrl}); else { await navigator.clipboard.writeText(text); showToast("\u0e04\u0e31\u0e14\u0e25\u0e2d\u0e01\u0e02\u0e49\u0e2d\u0e04\u0e27\u0e32\u0e21\u0e41\u0e25\u0e49\u0e27"); } }catch(e){ showToast("\u0e41\u0e0a\u0e23\u0e4c\u0e44\u0e21\u0e48\u0e44\u0e14\u0e49: "+e.message,"error"); } }\nwindow.addEventListener("DOMContentLoaded",()=>{ $("mode").addEventListener("change",()=>{ updateAllMachineOptions(); }); $("productType").addEventListener("change",updateProductUI); $("marketType").addEventListener("change",updateMarketUI); $("cartonPrefix").addEventListener("change",updateShippingMark); $("mfgDate").addEventListener("change",updateDates); $("mixDate").addEventListener("change",updateMix); $("fileInputPouch").addEventListener("change",e=>handleFile("pouch",e.target)); $("addPouchMachineBtn").addEventListener("click",addPouchMachine); $("fileInputCarton").addEventListener("change",e=>handleFile("carton",e.target)); $("openCameraBtn").addEventListener("click",openCamera); $("closeCameraBtn").addEventListener("click",closeCamera); $("capturePouchBtn").addEventListener("click",()=>captureTo("pouch")); $("captureCartonBtn").addEventListener("click",()=>captureTo("carton")); $("checkBtn").addEventListener("click",sendCheck); $("closeResultBtn").addEventListener("click",closeResult); $("closeResultBtn2").addEventListener("click",closeResult); $("shareBtn").addEventListener("click",shareResult); updateAllMachineOptions(); updateProductUI(); updateMarketUI(); });\n</script>\n</body>\n</html>'


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
            if re.fullmatch(r"(?:LP|MS|AS)\d{1,2}", v):
                result["machine"] = v
            else:
                result["mix_code"] = v
        if idx + 3 < len(tokens):
            v = tokens[idx + 3]
            if re.fullmatch(r"(?:LP|MS|AS)\d{1,2}", v):
                result["machine"] = v

    # fallback date
    if not result["mfg_date"]:
        m = re.search(r"\b\d{6}\b", text)
        if m:
            result["mfg_date"] = m.group(0)

    # fallback machine
    if not result["machine"]:
        m = re.search(r"\b(?:LP|MS|AS)\d{1,2}\b", text)
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
        expected_line2 = data.get("line2", "").strip().upper()
        expected_exp = data.get("exp", "").strip()
        # EPW LAOS FORCE EXP 3 YEARS: MFG 230626 -> EXP 230629
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
        shipping_mark = data.get("shippingMark", "").strip().upper()
        carton_alpha_code = data.get("cartonAlphaCode", "").strip().upper()

        # Carton lot does not separate Laos. Treat Laos as normal Export for carton mode.
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
            carton_base64 = carton_image_data.split(",", 1)[1] if "," in carton_image_data else carton_image_data

            pouch_results = []
            for idx, pouch_item in enumerate(pouches, start=1):
                line_code = pouch_item.get("line", "").strip().upper()
                pouch_img = pouch_item.get("image", "")
                pouch_base64 = pouch_img.split(",", 1)[1] if "," in pouch_img else pouch_img
                raw_pouch_ai = read_lot_with_ai(
                    pouch_base64, "pouch", mode, product_type, market_type, expected_mfg, line_code,
                    expected_exp, mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code
                )
                pouch_json_i = json.loads(clean_json_text(raw_pouch_ai))
                pouch_lines_i = pouch_json_i.get("lines", [])
                if mode == "sachet":
                    pouch_overall_i, pouch_details_i = check_pouch_sachet(
                        pouch_lines_i, product_type, market_type, expected_mfg, line_code, expected_exp
                    )
                else:
                    ai_time_i = pouch_json_i.get("time", "")
                    pouch_overall_i, pouch_details_i = check_pouch_linapack(
                        pouch_lines_i, product_type, market_type, expected_mfg, line_code, expected_exp, mix_code, ai_time_i
                    )
                pouch_results.append({
                    "index": idx,
                    "line": line_code,
                    "image": pouch_img,
                    "json": pouch_json_i,
                    "lines": pouch_lines_i,
                    "overall": pouch_overall_i,
                    "details": pouch_details_i,
                })

            carton_market_type = "EXPORT" if market_type == "LAOS" else market_type
            raw_carton_ai = read_lot_with_ai(
                carton_base64, "carton", mode, product_type, carton_market_type, expected_mfg, pouches[0].get("line", ""),
                expected_exp, mix_code, building_no, building_suffix, shipping_mark, carton_alpha_code
            )
            carton_json = json.loads(clean_json_text(raw_carton_ai))
            carton_lines = carton_json.get("lines", [])

            mode_name = "Sachet + Carton" if mode == "sachet" else "Linapack + Carton"

            carton_overall, carton_details = check_carton(
                carton_lines, carton_market_type, expected_mfg, expected_exp, building_no, building_suffix,
                shipping_mark, carton_alpha_code, carton_json
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
            carton_image_data if check_type == "both" else None,
            pouch2_image_data if check_type == "both" else None,
            [item.get("image", "") for item in pouches[1:]] if check_type == "both" else None
        )

        def build_expected_pouch(line_code):
            if mode == "sachet":
                return f"MFG {expected_mfg} {line_code} 1" + (f" EXP {expected_exp}" if expected_exp else "")
            line1 = f"MFG {expected_mfg}"
            if mix_code:
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
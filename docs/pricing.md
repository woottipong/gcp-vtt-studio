# Auto VTT Studio — Pricing & Cost Estimation

## Google Cloud Services ที่ใช้

โปรเจกต์นี้ใช้ Google Cloud 2 services หลัก:
1. **Cloud Speech-to-Text V2** — ถอดเสียงเป็นข้อความ + สร้าง VTT
2. **Cloud Storage (GCS)** — เก็บไฟล์เสียงและ VTT ชั่วคราว

---

## 1. Speech-to-Text V2 — Pricing

### Pricing Model

คิดค่าบริการ **ต่อ 15 วินาที** ของเสียงที่ประมวลผล (ปัดขึ้น)

### ราคา Standard

| Feature                  | ราคา/นาที   | หมายเหตุ                 |
| ------------------------ | ---------- | ----------------------- |
| **Standard Recognition** | **$0.016** | รวม Batch API (Chirp 2) |

### Free Tier

- **ฟรี 60 นาทีแรกต่อเดือน** สำหรับ Speech-to-Text ทุก model
- Free tier นับรวมทุก request type (online, streaming, batch)
- รีเซ็ตทุกเดือน

### Features ที่ใช้ในโปรเจกต์นี้ (ไม่มีค่าใช้จ่ายเพิ่ม)

| Feature                        | ค่าใช้จ่ายเพิ่ม              |
| ------------------------------ | ----------------------- |
| `enable_word_time_offsets`     | ฟรี                      |
| `VttOutputFileFormatConfig`    | ฟรี                      |
| `AutoDetectDecodingConfig`     | ฟรี                      |
| `enable_automatic_punctuation` | ฟรี                      |
| Chirp model                    | ฟรี (รวมในราคา standard) |

### Features ที่จะเพิ่มค่าใช้จ่าย (ถ้าเปิดใช้ในอนาคต)

| Feature                   | ค่าใช้จ่ายเพิ่ม         |
| ------------------------- | ------------------ |
| Speaker Diarization       | +$0.012/นาที        |
| Multi-channel recognition | คิดแต่ละ channel แยก |
| Model Adaptation          | ค่า training เพิ่มเติม |

---

## 2. Cloud Storage (GCS) — Pricing

### ราคา Standard Storage

| Item                         | ราคา                      |
| ---------------------------- | ------------------------- |
| Storage                      | $0.020/GB/เดือน            |
| Class A Operations           | $0.005/10,000 operations  |
| Class B Operations           | $0.0004/10,000 operations |
| Network Egress (same region) | ฟรี                        |

### การใช้งานจริงในโปรเจกต์นี้

โปรเจกต์นี้ลบไฟล์เสียงจาก GCS หลังใช้งานเสร็จ ดังนั้น:

- **Audio file**: เก็บชั่วคราว (นาทีถึงชั่วโมง) → ค่า storage แทบเป็น 0
- **VTT file**: ยังอยู่บน GCS หลัง download → ขนาดเล็กมาก (ไม่กี่ KB)
- **Operations**: upload 1 ครั้ง + download 1-2 ครั้ง ต่อ task → เล็กน้อยมาก

**ค่า GCS ต่อ task โดยประมาณ: < $0.001** (แทบไม่มี)

---

## 3. ตัวอย่างคำนวณค่าใช้จ่ายรวม

### Use Case: ถอดเสียงวิดีโอ YouTube ภาษาไทย

| ความยาวเสียง | STT Cost | GCS Cost | รวม        |
| ----------- | -------- | -------- | ---------- |
| 5 นาที       | $0.08    | ~$0.00   | **~$0.08** |
| 10 นาที      | $0.16    | ~$0.00   | **~$0.16** |
| 30 นาที      | $0.48    | ~$0.00   | **~$0.48** |
| 1 ชั่วโมง     | $0.96    | ~$0.00   | **~$0.96** |
| 3 ชั่วโมง     | $2.88    | ~$0.00   | **~$2.88** |
| 10 ชั่วโมง    | $9.60    | ~$0.00   | **~$9.60** |

### Use Case: ทีมงานใช้ทุกวัน

| Scenario                      | เสียงต่อเดือน | หักFree 60นาที | ค่าSTT/เดือน | ค่ารวม/เดือน  |
| ----------------------------- | ---------- | ------------ | ---------- | ----------- |
| 1 คน, 2 วิดีโอ/วัน (10 นาที/วิดีโอ) | ~600 นาที   | 540 นาที      | $8.64      | **~$8.64**  |
| 3 คน, 1 วิดีโอ/วัน (15 นาที/วิดีโอ) | ~1,350 นาที | 1,290 นาที    | $20.64     | **~$20.64** |
| ทีม 10 คน, heavy use           | ~6,000 นาที | 5,940 นาที    | $95.04     | **~$95.04** |

> **Note**: Free tier 60 นาที/เดือน shared ทั้ง project ไม่ใช่ต่อคน

---

## 4. เปรียบเทียบกับบริการอื่น

| Service                      | ราคา/นาที    | VTT Output   | Thai Support | หมายเหตุ           |
| ---------------------------- | ----------- | ------------ | ------------ | ----------------- |
| **Google STT V2 (โปรเจกต์นี้)** | **$0.016**  | ✅ Built-in   | ✅ ดี (Chirp)  | Batch API, async  |
| AWS Transcribe               | $0.024      | ✅            | ✅            | Real-time + batch |
| Azure Speech                 | $0.016      | ❌ ต้องแปลงเอง | ✅            | Real-time only    |
| OpenAI Whisper API           | $0.006      | ✅ SRT/VTT    | ✅            | ไฟล์ ≤25MB         |
| Whisper (self-hosted)        | ฟรี (ค่า GPU) | ❌ ต้องแปลงเอง | ✅            | ต้องมี GPU          |
| AssemblyAI                   | $0.015      | ✅ SRT/VTT    | ❌            | ไม่รองรับไทย        |

---

## 5. Tips ลดค่าใช้จ่าย

### ✅ สิ่งที่ทำได้

1. **Trim audio ก่อน transcribe** → ตัดส่วนเงียบหรือไม่จำเป็นออก
   - ลดจำนวนนาทีที่ต้องจ่าย

2. **ใช้ Free tier ให้เต็มที่** → 60 นาที/เดือนฟรี
   - เหมาะสำหรับทดสอบหรือใช้งานเบาๆ

3. **เลือก region ใกล้** → ลด network latency (ไม่ลดราคาตรงๆ แต่เร็วขึ้น)
   - โปรเจกต์นี้ใช้ `asia-southeast1` (Singapore)

4. **ลบไฟล์ GCS หลังใช้** → โปรเจกต์นี้ทำอยู่แล้ว (auto cleanup)

> **หมายเหตุ:** Data Logging opt-in ($0.012/min) ไม่สามารถเปิดผ่าน API ได้สำหรับ Speech V2 Chirp model

### ❌ สิ่งที่ไม่ช่วยลดราคา

- Batch API vs Online API → ราคาเท่ากัน
- เปลี่ยน output format (VTT, SRT, JSON) → ราคาเท่ากัน
- เปลี่ยน audio encoding → ราคาเท่ากัน (คิดตามความยาวเสียง ไม่ใช่ขนาดไฟล์)

---

## 6. Billing Alerts แนะนำ

ตั้ง budget alert ใน Google Cloud Console:

```
Google Cloud Console → Billing → Budgets & alerts → Create Budget
```

| Alert Level | Amount | Action                     |
| ----------- | ------ | -------------------------- |
| 50%         | $5     | Email notification         |
| 90%         | $9     | Email + Slack notification |
| 100%        | $10    | Email + consider pause     |

> **Recommendation**: ตั้ง budget ที่ $10-$50/เดือน สำหรับ development/testing

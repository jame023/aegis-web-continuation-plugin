# ติดตั้ง AEGIS Web Continuation

เอกสารนี้เป็นทางลัดสำหรับติดตั้ง หากต้องการขั้นตอนละเอียดพร้อมภาพประกอบและตัวอย่างคำสั่งจากมือถือ ให้อ่าน [docs/USER_GUIDE_TH.md](docs/USER_GUIDE_TH.md)

Plugin นี้เพิ่ม workflow ให้ ChatGPT Chat/Work/Codex Cloud รับช่วงงานวิศวกรรมจาก GitHub และ AEGIS checkpoint โดยไม่ทำซ้ำงานที่ verify แล้วและไม่ขยายขอบเขตอัตโนมัติ

> Skill ไม่ได้ให้สิทธิ์ GitHub, shell, filesystem, network, credential, merge หรือ deploy สิทธิ์เหล่านี้ต้องมาจาก environment/connector ที่ผู้ใช้อนุญาตแยกต่างหาก และ Skill ไม่สามารถข้าม ChatGPT/Codex usage limit ได้

## สิ่งที่ต้องมี

- Windows PowerShell
- ChatGPT desktop app สำหรับค้นพบ local personal marketplace ครั้งแรก
- บัญชี/workspace ที่เปิดใช้ Plugins/Skills
- หากต้องการแก้ repository จริง: GitHub repository ที่เชื่อมกับ Codex cloud และมี environment สำหรับ repository นั้น

## ติดตั้งบน Windows

1. แตก ZIP แล้วเปิด PowerShell ในโฟลเดอร์แพ็กเกจ
2. Preview ก่อนติดตั้ง:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-AEGISWebContinuation.ps1
```

ต้องเห็น `PREVIEW_ONLY` และยังไม่มีไฟล์ถูกแก้

3. เมื่อตรวจ path แล้วจึงติดตั้ง:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-AEGISWebContinuation.ps1 -Apply
```

Installer เพิ่มเฉพาะ:

```text
$HOME\plugins\aegis-web-continuation
$HOME\.agents\plugins\marketplace.json
```

ถ้ามีปลายทางหรือ marketplace entry ชื่อเดียวกันแต่เนื้อหาต่างกัน Installer จะหยุด ไม่ overwrite โดยเงียบ และ backup marketplace เดิมก่อนเขียน

4. ปิดและเปิด ChatGPT desktop app ใหม่
5. เปิด Plugins → Personal → `AEGIS Web Continuation` → กดปุ่ม `+`
6. เริ่ม chat ใหม่ แล้วพิมพ์ `@` เพื่อเลือก `AEGIS Web Continuation`

Local/repo marketplace เป็นแหล่งสำหรับพัฒนาและทดสอบ ความพร้อมบน Web/Mobile อาจต่างกันตาม surface, plan และ workspace policy หากไม่ปรากฏบนมือถือ ให้อ่านหัวข้อ “ทำให้พร้อมใช้บน Web/Mobile” ในคู่มือฉบับเต็ม

## เชื่อม repository สำหรับงานแก้โค้ด

1. เปิด Codex cloud และลงชื่อเข้าใช้บัญชีเดียวกัน
2. เชื่อม GitHub และเลือกเฉพาะ repository ที่ต้องการ
3. สร้าง environment สำหรับ repository นั้น
4. ตั้ง dependencies, variables หรือ secrets เฉพาะค่าจริงที่งานต้องใช้
5. เริ่มด้วยคำสั่งตรวจแบบ read-only แล้ว review repository/branch/commit ที่ระบบรายงาน

## ตัวอย่างคำสั่งจากมือถือ

```text
@AEGIS Web Continuation
รับช่วงงาน repository <owner/repo> branch <exact-branch>
อ้างอิง Issue/PR <URL-or-number> และ commit <exact-sha>
ตรวจ AEGIS checkpoint กับ security boundary ก่อน
ทำเฉพาะงานที่ยังค้าง แล้วสรุป diff และ verification ให้ตรวจ
```

ห้ามเดา repository, branch, issue, path, credential หรือ environment ใช้ค่าจริงเท่านั้น

## ถอนติดตั้ง

Preview แล้ว apply:

```powershell
powershell -ExecutionPolicy Bypass -File .\Uninstall-AEGISWebContinuation.ps1
powershell -ExecutionPolicy Bypass -File .\Uninstall-AEGISWebContinuation.ps1 -Apply
```

Uninstaller ลบเฉพาะ plugin ที่ fingerprint ยังตรงกับแพ็กเกจ และลบเฉพาะ marketplace entry ชื่อเดียวกัน หากไฟล์ถูกแก้หลังติดตั้งจะหยุดเพื่อรักษางานผู้ใช้

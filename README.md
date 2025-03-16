# Git Compare Project

โปรเจ็กต์นี้เป็นแอปพลิเคชันเว็บ (Web App) ที่สร้างด้วย **[Streamlit](https://streamlit.io)** เพื่อ:

- **Clone Git Repository** ตาม URL ที่กำหนด
- **เปรียบเทียบ Branch หรือ Tag** สองตัว แล้วแสดงรายชื่อไฟล์แตกต่าง
- **ดู Diff แบบ Side-by-Side** ของไฟล์ที่มีการเปลี่ยนแปลง
- รองรับ **Custom File Mapping** สำหรับไฟล์ที่ชื่อไม่ตรงกัน
- **ลบโฟลเดอร์เก่า** และ **Clear Cache** อัตโนมัติเมื่อเปลี่ยน URL

## วิธีใช้งาน (Local Machine)

1. **Clone โปรเจ็กต์ และติดตั้ง dependencies:**
   git clone https://github.com/Nattakitt-Tin/repo_compare
   cd git_compare_project
   pip install -r requirements.txt

2. **รันแอป Streamlit:**
    streamlit run app.py

## วิธีใช้งานผ่าน Docker

1. **Build Image:**
    docker build -t my-streamlit-app:latest .

2. **CRun Container:**
    docker run -p 8501:8501 my-streamlit-app:latest

เปิดเบราว์เซอร์ที่ http://localhost:8501 เพื่อใช้งานแอป


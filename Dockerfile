# ใช้ base image Python เวอร์ชัน 3.9 (หรือเวอร์ชันอื่นที่ต้องการ)
FROM python:3.9

# สร้างและกำหนดโฟลเดอร์ /app เป็นโฟลเดอร์ทำงาน (Workdir)
WORKDIR /app

# คัดลอกไฟล์ requirements.txt ไปที่ /app
COPY requirements.txt .

# ติดตั้ง dependencies ที่ระบุใน requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมดในโปรเจ็กต์ไปไว้ที่ /app
COPY . /app

# เปิดพอร์ต 8501 สำหรับ Streamlit
EXPOSE 8501

# คำสั่งเริ่มต้นเมื่อ Container รัน
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

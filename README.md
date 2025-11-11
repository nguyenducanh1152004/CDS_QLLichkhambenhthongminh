<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    🎓 Faculty of Information Technology (DaiNam University)
    </a>
</h2>
<h2 align="center">
   ĐỀ TÀI: HỆ THỐNG ĐẶT LỊCH KHÁM BỆNH (MEDICAL APPOINTMENT SYSTEM)
</h2>
<p align="center"><strong>Ngành / Môn: Công nghệ thông tin — Hướng dẫn: [Tên giảng viên hướng dẫn]</strong></p>
<div align="center">
    <p align="center">
        <img src="docs/aiotlab_logo.png" alt="AIoTLab Logo" width="170"/>
        <img src="docs/fitdnu_logo.png" alt="FIT Logo" width="180"/>
        <img src="docs/dnu_logo.png" alt="DaiNam University Logo" width="200"/>
    </p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

## 📖 **1. Giới thiệu hệ thống**  
Hệ thống **Medical Appointment System** là giải pháp web toàn diện cho việc quản lý và đặt lịch khám bệnh tại các phòng khám, bệnh viện. Hệ thống được phát triển bằng **Flask (Python)** và **SQLite**, cung cấp giao diện thân thiện và các tính năng quản lý chuyên nghiệp.

- **Mục tiêu chính**: Tự động hóa quy trình đặt lịch khám bệnh, quản lý thông tin bệnh nhân, bác sĩ và lịch hẹn
- **Phạm vi**: Quản lý người dùng, bệnh nhân, bác sĩ, lịch hẹn, gửi email xác nhận, thống kê báo cáo
- **Công nghệ**: Flask + SQLite + Bootstrap 5 + Chart.js + Flask-Mail
- **Người dùng mục tiêu**: Quản trị viên, nhân viên lễ tân, bác sĩ, bệnh nhân

## ✨ **Tính năng chính**

### 🔐 **Xác thực & Phân quyền**
- **4 vai trò người dùng**: 
  - 👨‍💼 **Admin**: Toàn quyền quản trị hệ thống
  - 👩‍💼 **Receptionist**: Quản lý bệnh nhân, bác sĩ, lịch hẹn
  - 👨‍⚕️ **Doctor**: Xem lịch làm việc, thông tin bệnh nhân
  - 👤 **Patient**: Đặt lịch, quản lý thông tin cá nhân
- 🔒 Đăng nhập/Đăng ký với mã hóa **SHA-256**
- 🎯 Session-based authentication với **Flask-Login**
- 🔑 Phân quyền truy cập theo vai trò với decorators

### 👥 **Quản lý Bệnh nhân**
- 📋 **CRUD đầy đủ**: Thông tin cá nhân, liên hệ, địa chỉ, ngày sinh, giới tính
- 📞 Quản lý số điện thoại và email duy nhất
- 📊 Lịch sử khám bệnh chi tiết
- 🔍 Tìm kiếm và lọc nâng cao
- 📅 Theo dõi ngày tạo và cập nhật

### 👨‍⚕️ **Quản lý Bác sĩ**
- 🏥 **Thông tin chuyên môn**: Tên, chuyên khoa, số điện thoại, email
- 📅 **Lịch làm việc**: Ngày làm việc, giờ làm việc cụ thể
- 🔄 Import từ file CSV tự động
- 📊 Quản lý lịch trình và khả năng tiếp nhận

### 📅 **Quản lý Lịch hẹn**
- ➕ **Đặt lịch linh hoạt**: Có tài khoản và không cần tài khoản
- 📧 **Gửi email xác nhận**: Template HTML chuyên nghiệp
- 🔄 **Trạng thái đa dạng**: Scheduled, Confirmed, Completed, Cancelled
- ✏️ **Chỉnh sửa lịch**: Bệnh nhân có thể chỉnh sửa/hủy lịch
- ⏰ **Kiểm tra trùng lịch**: Tự động kiểm tra khung giờ khả dụng

### 📧 **Hệ thống Email**
- ✉️ **Gửi email xác nhận**: Tự động khi đặt lịch thành công
- 🎨 **Template HTML**: Thiết kế chuyên nghiệp, responsive
- 📋 **Thông tin đầy đủ**: Mã lịch hẹn, bác sĩ, ngày giờ, hướng dẫn
- 🔧 **Cấu hình SMTP**: Hỗ trợ Gmail và các SMTP khác

### 📊 **Dashboard & Báo cáo**
- 📈 **Thống kê tổng quan**: 
  - Tổng số bệnh nhân, bác sĩ, lịch hẹn
  - Lịch hẹn hôm nay, lịch hẹn gần đây
- 📊 **Biểu đồ động** (Chart.js):
  - Phân bố thống kê (Doughnut Chart)
  - Xu hướng theo thời gian
- 📋 Danh sách lịch hẹn gần đây
- 🔄 Real-time updates với API endpoints

---

## 🔧 **2. Công nghệ sử dụng**  

<p align="center">
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  </a>
  <a href="https://flask.palletsprojects.com/">
    <img src="https://img.shields.io/badge/Flask-2.3.3-000000?style=for-the-badge&logo=flask&logoColor=white" />
  </a>
  <a href="https://www.sqlite.org/">
    <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  </a>
  <a href="https://getbootstrap.com/">
    <img src="https://img.shields.io/badge/Bootstrap-5.1-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" />
  </a>
  <a href="https://www.chartjs.org/">
    <img src="https://img.shields.io/badge/Chart.js-3.9-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" />
  </a>
  <a href="https://jinja.palletsprojects.com/">
    <img src="https://img.shields.io/badge/Jinja2-Template-B41717?style=for-the-badge&logo=jinja&logoColor=white" />
  </a>
</p>

### **Backend**
- 🐍 **Python 3.9+**: Ngôn ngữ lập trình chính
- 🌶️ **Flask 2.3.3**: Web framework nhẹ và linh hoạt
- 🗄️ **SQLite**: Cơ sở dữ liệu nhúng, không cần cài đặt server
- 🔐 **Flask-Login**: Quản lý session và authentication
- 📧 **Flask-Mail**: Gửi email xác nhận
- 🗃️ **SQLAlchemy**: ORM cho database operations

### **Frontend**
- 🎨 **Bootstrap 5.1**: CSS framework responsive
- ✨ **Font Awesome 6**: Icon library
- 📊 **Chart.js 3.9**: Thư viện biểu đồ động
- 🎯 **Jinja2**: Template engine
- 🌐 **HTML5, CSS3, JavaScript**: Core web technologies

### **Thư viện Python chính**
```python
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Werkzeug==2.3.7
Flask-Login==0.6.3
Flask-Mail==0.9.1
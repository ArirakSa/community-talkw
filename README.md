# Project Talk with TOK 
#### <br>พัฒนาโดยใช้ Django Tailwind และ MySQL

**ตรวจสอบเครื่องมือว่ามีพร้อมใช้งานหรือไม่**
##### 1. ตรวจสอบว่ามี Python หรือไม่ โดยใช้คำสั่ง
* python --version
<br> หากไม่มีให้ทำการ download จาก https://www.python.org/downloads/ โดยเลือก version 3.8 ขึ้นไป
##### 2. ตรวจสอบว่ามี Node หรือไม่
* node --version
<br>หากไม่มีให้ทำการ download  จาก https://nodejs.org/

##### 3. ตรวจสอบว่ามี MySQL หรือไม่ โดยใช้คำสั่ง
*  mysql --version
<br>หากไม่มีให้ทำการ download MySQL จาก https://dev.mysql.com/downloads/installer/
<br>และ download  MySQL workbench จาก https://dev.mysql.com/downloads/workbench/
<br>ทำการสร้างฐานข้อมูล ใน  MySQL workbench ชื่อ dssi-prj

##### 4. ทำการ Clone project  โดยใช้คำสั่ง
* git clone https://github.com/ArirakSa/ST-DSSI-68/
* cd ST-DSSI-68

##### 5. สร้าง virsual environment โดยใช้คำสั่ง
* python -m venv env
* venv\Scripts\activate

##### 6. ติดตั้ง python dependencies
* pip install -r requirements.txt

##### 7. ทำการติดตั้ง npm dependencies
* cd theme
* cd static_src
* npm install
* cd ../../

##### 8. เริ่มต้น Tailwind CSS โดยใช้คำสั่ง
* python manage.py tailwind start

##### 9. รัน Django Server
* python manage.py runserver


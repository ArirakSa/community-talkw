# Project Talk with TOK 
#### <br>พัฒนาโดยใช้ Django Tailwind และ MySQL

**ตรวจสอบการติดตั้งและความพร้อมใช้งานของเครื่องมือที่จำเป็น**
##### 1. ตรวจสอบว่ามี Python หรือไม่ โดยใช้คำสั่ง
* python --version
<br> หากไม่มีให้ทำการ downloads จาก https://www.python.org/downloads/ โดยเลือก version 3.8 ขึ้นไป
##### 2. ตรวจสอบว่ามี Node หรือไม่
* node --version
<br>หากไม่มีให้ทำการ downloads  จาก https://nodejs.org/

##### 3. ตรวจสอบว่ามี MySQL หรือไม่ โดยใช้คำสั่ง
*  mysql --version
<br>หากไม่มีให้ทำการ downloads MySQL จาก https://dev.mysql.com/downloads/installer/
<br>และ downloads  MySQL workbench จาก https://dev.mysql.com/downloads/workbench/
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

##### 8. เตรียมฐานข้อมูลโปรเจกต์
* python manage.py migrate

##### 9. สร้าง Superuser (Admin) สำหรับเข้าใช้ส่วนของ admin
* python manage.py createsuperuser ( ตามด้วยใส่ username, email และรหัสผ่าน )

##### 10. install และเริ่มต้น Tailwind CSS โดยใช้คำสั่ง
* python manage.py tailwind install
* python manage.py tailwind start

##### 11. run Django Server
* python manage.py runserver


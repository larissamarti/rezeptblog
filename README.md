# rezeptblog

define credentials and keys for the app and db connection -> create a file named "var.env" with following environment varbiales in folder rezeptblog/app:

 SECRET_KEY="secret"
 
 DATABASE_URL=mysql+pymysql://"user":"password"@"containername db"/"db name" -> (check in docker-compose.yml file if credentials for the db matches)
 
 FLASK_APP=rezeptblog.py
 
unzip file "ib_logfile0.zip" in folder db/ before you start docker-compose

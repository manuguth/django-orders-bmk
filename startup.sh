echo de_DE ISO-8859-1 >> /etc/locale.gen && locale-gen
gunicorn --bind=0.0.0.0 --timeout 600 bmk_orders_togo.wsgi
# oryx build /tmp/zipdeploy/extracted -o /home/site/wwwroot --platform python --platform-version 3.8 -i /tmp/8d9363af8c5d407 --compress-destination-dir -p virtualenv_name=antenv --log-file /tmp/build-debug.log
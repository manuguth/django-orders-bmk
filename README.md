# Bestellplattform Essen ToGo BMK Buggingen


## Azure Settings
### WebApp
- ResourceGroup: DjangoPostgres-Order-ToGo
- Name: bmk-bestellung
- Runtime Stack: python3.8

### PostSQL
- Servername: bmk-bestellung-db
- databasename: festessendb202107



### Startup
`echo de_DE ISO-8859-1 >> /etc/locale.gen && locale-gen`


## Adding timeslots

it is possible to add timeslots from a yaml file via

```
python manage.py addtimeslots scripts/timeslots.yaml
```

deleting table in db and adding reinitialising it:
https://stackoverflow.com/questions/33259477/how-to-recreate-a-deleted-table-with-django-migrations/37369497#37369497
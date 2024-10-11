DB_NAME := $(if $(DB),$(DB),kuja)  # Default to "kuja" if no parameter is provided

# Target for setting up the database, using the provided database name
db_drop:
	dropdb kujatmp
	createdb kujatmp
	dropdb kuja
	createdb kuja

db_pop:
	psql kuja -f ../tmp/db/country.sql
	# psql kuja -f ../tmp/db/states.sql
	# psql kuja -f ../tmp/db/banks.sql
	# psql kuja -f ../tmp/db/biller_cat.sql
	# psql kuja -f ../tmp/db/lga.sql
	# psql kuja -f ../tmp/db/currency.sql
	# psql kuja -f ../tmp/db/cust_segment.sql
	# psql kuja -f ../tmp/db/doc_type.sql
	# psql kuja -f ../tmp/db/mime_types.sql
	# psql kuja -f ../tmp/db/mime_type_map.sql
	# psql kuja -f ../tmp/db/tech_params.sql
	# psql kuja -f ../tmp/db/trans_type.sql
	# psql kuja -f ../tmp/db/agency.sql

# Other targets (no changes needed)
code:
	python codegen.py

test:
    # python test1.py  # Uncomment if you want to run the test

cpf:
	cp gen/models.py gen/views.py  /Users/nyimbiodero/src/pjs/kj/kuja/app/blueprints/org 

# cpl:
# 	scp apis.py gql.py models.py views.py view_mixins.py model_mixins.py sec.py sec_forms.py sec_views.py __init__.py nyimbi@139.162.203.216:/home/nyimbi/terra/src/terra/app
# 	scp config.py nyimbi@139.162.203.216:/home/nyimbi/terra/src/terra/

# cpb:
# 	cp py_templates/apis.py py_templates/gql.py models.py views.py  py_templates/view_mixins.py py_templates/model_mixins.py py_templates/sec.py py_templates/sec_forms.py py_templates/sec_views.py __init__.py  /Users/nyimbiodero/src/pjs/bubetech/src/bubetech/app



all: db_drop code cpf  # test  # Uncomment if you want to include testing

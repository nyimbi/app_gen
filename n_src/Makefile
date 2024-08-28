DB_NAME := $(if $(DB),$(DB),kuja1)  # Default to "kuja1" if no parameter is provided

# Target for setting up the database, using the provided database name
db_drop:
	dropdb $(DB_NAME)
	createdb $(DB_NAME)

db_pop:
	psql kuja1 -f ../tmp/db/country.sql
	psql kuja1 -f ../tmp/db/states.sql
	psql kuja1 -f ../tmp/db/banks.sql
	psql kuja1 -f ../tmp/db/biller_cat.sql
	psql kuja1 -f ../tmp/db/lga.sql
	psql kuja1 -f ../tmp/db/currency.sql
	psql kuja1 -f ../tmp/db/cust_segment.sql
	psql kuja1 -f ../tmp/db/doc_type.sql
	psql kuja1 -f ../tmp/db/mime_types.sql
	psql kuja1 -f ../tmp/db/mime_type_map.sql
	psql kuja1 -f ../tmp/db/tech_params.sql
	psql kuja1 -f ../tmp/db/trans_type.sql
	psql kuja1 -f ../tmp/db/agency.sql

# Other targets (no changes needed)
code:
	python gen_models4.py --uri "postgresql:///kujatmp" --output "gen/models.py"
	cp gen/models.py /Users/nyimbiodero/src/pjs/kj/kuja/app/blueprints/org

test:
    # python test1.py  # Uncomment if you want to run the test
	# https://pypi.org/project/geoparser/

cpf:
	cp apis.py gql.py models.py views.py view_mixins.py model_mixins.py sec.py sec_forms.py sec_views.py __init__.py  /Users/nyimbiodero/src/pjs/kj/kuja/app/blueprints/org

cpl:
	scp apis.py gql.py models.py views.py view_mixins.py model_mixins.py sec.py sec_forms.py sec_views.py __init__.py nyimbi@139.162.203.216:/home/nyimbi/terra/src/terra/app
	scp config.py nyimbi@139.162.203.216:/home/nyimbi/terra/src/terra/

cpb:
	cp py_templates/apis.py py_templates/gql.py models.py views.py  py_templates/view_mixins.py py_templates/model_mixins.py py_templates/sec.py py_templates/sec_forms.py py_templates/sec_views.py __init__.py  /Users/nyimbiodero/src/pjs/bubetech/src/bubetech/app



all: db_drop code cpf  # test  # Uncomment if you want to include testing

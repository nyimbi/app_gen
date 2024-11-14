from faker import Faker
import random

fake = Faker()

# Generate fake data for the user_ext table
def generate_user_data(manager_id_fk=None):
    user_data = {
        'middle_name': fake.first_name(),
        'employee_number': fake.unique.random_number(),
        'job_title': fake.job(),
        'phone_number': fake.phone_number(),
        'email': fake.unique.email(),
        'user_data': fake.text(max_nb_chars=200),
    }
    
    if manager_id_fk is not None:
        user_data['manager_id_fk'] = manager_id_fk

    return user_data

# Generate INSERT SQL script for a specified number of user entries
def generate_insert_sql(entries):
    insert_statements = []

    for _ in range(entries):
        user_data = generate_user_data(manager_id_fk=random.randint(1, _))
        
        insert_sql = f"""
        INSERT INTO user_ext (
            middle_name, employee_number, job_title, phone_number, email, user_data, manager_id_fk
        ) VALUES (
            '{user_data['middle_name']}', '{user_data['employee_number']}', '{user_data['job_title']}',
            '{user_data['phone_number']}', '{user_data['email']}', '{user_data['user_data']}',
            {user_data.get('manager_id_fk', 'NULL')}
        );
        """
        
        insert_statements.append(insert_sql)

    return insert_statements

# Specify the number of entries you want to generate
num_entries = 1000

# Generate INSERT SQL statements
insert_sql_statements = generate_insert_sql(num_entries)

# Save the INSERT statements to a SQL file
with open('user_ext_data_insert.sql', 'w') as file:
    for statement in insert_sql_statements:
        file.write(statement + '\n')


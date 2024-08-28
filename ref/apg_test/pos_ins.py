from faker import Faker
import random
import datetime

fake = Faker()

# Generate fake data for the pos table
def generate_pos_data():
    pos_data = {
        'serial_no': fake.unique.uuid4(),
        'imei': fake.uuid4() if random.choice([True, False]) else None,
        'mac_addr': fake.mac_address(),
        'device_model': fake.random_element(elements=('Model A', 'Model B', 'Model C')),
        'device_make': fake.random_element(elements=('Make X', 'Make Y', 'Make Z')),
        'device_mfg': fake.company(),
        'os_version': fake.word(),
        'device_color': fake.color_name(),
        'device_condition': fake.random_element(elements=('working', 'irreparable', 'repaired')),
        'status': fake.random_element(elements=('Active', 'Inactive', 'In Repair')),
        'owner_type': fake.random_element(elements=('Company', 'Individual')),
        'registration_date': fake.date_time_between(start_date='-2y', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'assigned': fake.boolean(chance_of_getting_true=40),  # 40% chance of being assigned
        'assigned_date': fake.date_time_between(start_date='-1y', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'assigned_narrative': fake.text(max_nb_chars=100),
        'active': fake.boolean(chance_of_getting_true=80),  # 80% chance of being active
        'activation_date': fake.date_time_between(start_date='-1y', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'last_active': fake.date_time_between(start_date='-1d', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'deployed': fake.boolean(chance_of_getting_true=60),  # 60% chance of being deployed
        'deploy_date': fake.date_time_between(start_date='-1y', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'deploy_narrative': fake.text(max_nb_chars=100),
        'returned': fake.boolean(chance_of_getting_true=20),  # 20% chance of being returned
        'return_date': fake.date_time_between(start_date='-1y', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'return_narrative': fake.text(max_nb_chars=100),
        'return_received_date': fake.date_time_between(start_date='-1y', end_date='now').strftime("%Y-%m-%d %H:%M:%S"),
        'return_received_by_id_fk': random.randint(1, 100),  # Replace with actual user_ext IDs
        'state_id_fk': random.randint(1, 37),  # Replace with actual state IDs
        'lga_id_fk': random.randint(1, 774),  # Replace with actual LGA IDs
        'street_address': fake.street_address(),
        'building_name': fake.building_number(),
        'contact_phone_num': fake.phone_number(),
        'pos_user': fake.user_name(),
        'crypt_priv_key': fake.text(max_nb_chars=500),
        'crypt_pub_key': fake.text(max_nb_chars=500),
        'crypt_password': fake.password(),
        'override_key': fake.password(),
    }
    return pos_data

# Generate INSERT SQL script for a specified number of entries
def generate_insert_sql(entries):
    insert_statements = []

    for _ in range(entries):
        pos_data = generate_pos_data()
        
        insert_sql = f"""
        INSERT INTO pos (
            serial_no, imei, mac_addr, device_model, device_make, device_mfg, os_version, device_color, 
            device_condition, status, owner_type, registration_date, assigned, assigned_date, assigned_narrative,
            active, activation_date, last_active, deployed, deploy_date, deploy_narrative, returned, return_date,
            return_narrative, return_received_date,   
            street_address, building_name, contact_phone_num, pos_user,
            crypt_password, override_key
        ) VALUES (
            '{pos_data['serial_no']}', '{pos_data['imei']}', '{pos_data['mac_addr']}', '{pos_data['device_model']}',
            '{pos_data['device_make']}', '{pos_data['device_mfg']}', '{pos_data['os_version']}', 
            '{pos_data['device_color']}', '{pos_data['device_condition']}', '{pos_data['status']}',
            '{pos_data['owner_type']}', '{pos_data['registration_date']}', {pos_data['assigned']},
            '{pos_data['assigned_date']}', '{pos_data['assigned_narrative']}', {pos_data['active']},
            '{pos_data['activation_date']}', '{pos_data['last_active']}', {pos_data['deployed']},
            '{pos_data['deploy_date']}', '{pos_data['deploy_narrative']}', {pos_data['returned']},
            '{pos_data['return_date']}', '{pos_data['return_narrative']}', '{pos_data['return_received_date']}',
            
            '{pos_data['street_address']}', '{pos_data['building_name']}', '{pos_data['contact_phone_num']}',
            '{pos_data['pos_user']}',
            '{pos_data['crypt_password']}', '{pos_data['override_key']}'
        );
        """
        
        insert_statements.append(insert_sql)

    return insert_statements

# Specify the number of entries you want to generate
num_entries = 1000

# Generate INSERT SQL statements
insert_sql_statements = generate_insert_sql(num_entries)

# Save the INSERT statements to a SQL file
with open('pos_data_insert.sql', 'w') as file:
    for statement in insert_sql_statements:
        file.write(statement + '\n')


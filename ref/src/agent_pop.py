from faker import Faker
import random
import datetime

fake = Faker()

# Enum values
VERIFICATION_STATUSES = ['PENDING', 'KYC_SUBMITTED', 'KYC_APPROVED', 'KYC_REJECTED', 'ESCALATED',
                         'CONTRACTED', 'ACTIVE', 'SUSPENDED', 'INACTIVE', 'CONTRACT_TERMINATED',
                         'DOCS_EXPIRED', 'UNDER_REVIEW', 'LOCKED', 'AWAITING_RENEWAL', 'RENEWAL_REJECTED',
                         'VERIFICATION_FAILED']

org_types = ['INDIVIDUAL', 'BUSINESS_NAME', 'SOLE_PROPRIETORSHIP', 'PRIVATE_LIMITED_COMPANY',
             'PUBLIC_LIMITED_COMPANY', 'PUBLIC_COMPANY_LIMITED_BY_GUARANTEE', 'PRIVATE_UNLIMITED_COMPANY',
             'PUBLIC_UNLIMITED_COMPANY']

agent_roles = ['AGENT', 'SUB_AGENT', 'SUPER_AGENT', 'AGGREGATOR']

# Generate fake data
def generate_agent_data():
    agent_data = {
        'is_aggregator': fake.boolean(chance_of_getting_true=20),  # 20% chance of being an aggregator
        'assigned_pos_count': random.randint(0, 100),
        'verification_status': random.choice(verification_statuses),
        'verification_status_notes': fake.text(max_nb_chars=200),
        'agent_type': random.choice(org_types),
        'agent_role': random.choice(agent_roles),
        'agent_name': fake.name(),
        'phone': fake.phone_number(),
        'email': fake.unique.email(),
        'bvn': fake.random_int(min=1000000000, max=9999999999),
        'bvn_verified': fake.boolean(chance_of_getting_true=80),  # 80% chance of being verified
        'tax_id': fake.random_int(min=1000000000, max=9999999999),
        'bank_acc_no': fake.credit_card_number(card_type='mastercard'),
        'biz_name': fake.company(),
        'biz_city': fake.city(),
        'biz_street': fake.street_name(),
        'biz_address': fake.address(),
        'biz_lat': fake.latitude(),
        'biz_lon': fake.longitude(),
        'company_name': fake.company(),
        'cac_number': fake.random_int(min=1000000000, max=9999999999),
        'cac_reg_date': fake.date_between(start_date='-10y', end_date='today'),
        'ref_code': fake.unique.uuid4(),
        'access_pin': fake.random_int(min=1000, max=9999),
        'registration_date': fake.date_time_this_decade(),
        'review_date': fake.date_time_this_decade(),
        'kyc_submit_date': fake.date_time_this_decade(),
        'kyc_approval_date': fake.date_time_this_decade(),
        'kyc_ref_code': fake.unique.uuid4(),
        'rejection_narrative': fake.text(max_nb_chars=200),
    }

    if agent_data['is_aggregator']:
        agent_data['aggregator_pos_threshold'] = random.randint(10, 50)
        agent_data['became_aggregator_date'] = fake.date_time_this_decade()

    return agent_data

# Generate and print SQL INSERT statements for 1000 entries
insert_statements = []

for _ in range(10):  # Generate 1000 sample agents
    agent_data = generate_agent_data()

    insert_sql = f"""
    INSERT INTO agent (
        is_aggregator, assigned_pos_count, verification_status, verification_status_notes,
        agent_type, agent_role, agent_name, phone, email, bvn, bvn_verified, tax_id,
        bank_acc_no, biz_name, biz_city, biz_street, biz_address, biz_lat, biz_lon,
        company_name, cac_number, cac_reg_date, ref_code, access_pin, registration_date,
        review_date, kyc_submit_date, kyc_approval_date, kyc_ref_code, rejection_narrative
    ) VALUES (
        {agent_data['is_aggregator']}, {agent_data['assigned_pos_count']}, '{agent_data['verification_status']}',
        '{agent_data['verification_status_notes']}', '{agent_data['agent_type']}', '{agent_data['agent_role']}',
        '{agent_data['agent_name']}', '{agent_data['phone']}', '{agent_data['email']}', '{agent_data['bvn']}',
        {agent_data['bvn_verified']}, '{agent_data['tax_id']}', '{agent_data['bank_acc_no']}', '{agent_data['biz_name']}',
        '{agent_data['biz_city']}', '{agent_data['biz_street']}', '{agent_data['biz_address']}', {agent_data['biz_lat']},
        {agent_data['biz_lon']}, '{agent_data['company_name']}', '{agent_data['cac_number']}',
        '{agent_data['cac_reg_date']}', '{agent_data['ref_code']}', '{agent_data['access_pin']}',
        '{agent_data['registration_date']}', '{agent_data['review_date']}', '{agent_data['kyc_submit_date']}',
        '{agent_data['kyc_approval_date']}', '{agent_data['kyc_ref_code']}', '{agent_data['rejection_narrative']}'
    );
    """

    insert_statements.append(insert_sql)

# Save the INSERT statements to a file
with open('agent_data_insert.sql', 'w') as file:
    for statement in insert_statements:
        file.write(statement + '\n')


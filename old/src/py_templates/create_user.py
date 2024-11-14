import sys
from app import db, app
from flask_appbuilder.security.sqla.models import User, Role
from flask_appbuilder.security.manager import SecurityManager

if len(sys.argv) != 3:
    print("Usage: script.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

# Create a security manager instance
security_manager = SecurityManager(app)

# Create a new user
new_user = User()
new_user.username = username
new_user.first_name = "FirstName" # You can modify this
new_user.last_name = "LastName"   # You can modify this
new_user.email = f"{username}@example.com" # Modify as needed
new_user.password = security_manager.bcrypt.generate_password_hash(password).decode('utf-8')

# Add user to the session
db.session.add(new_user)

# Assign role
role = db.session.query(Role).filter_by(name='User').first()
new_user.roles.append(role)

# Commit session
db.session.commit()

print(f"User {username} created successfully.")


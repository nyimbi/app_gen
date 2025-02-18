from flask import Flask, jsonify, request, session
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    base64url_to_bytes,
    bytes_to_base64url
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
)
import secrets
from datetime import datetime
from typing import Optional, Dict
import uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# In-memory storage (replace with database in production)
registered_users: Dict[str, Dict] = {}
credentials: Dict[str, Dict] = {}

# Relying Party configuration
RP_ID = "example.com"  # Your domain
RP_NAME = "Example App"
ORIGIN = "https://example.com"  # Your origin

class PasskeyAuth:
    @staticmethod
    def generate_challenge() -> bytes:
        """Generate a random challenge"""
        return secrets.token_bytes(32)

    @staticmethod
    def get_user_unique_id(username: str) -> bytes:
        """Generate or retrieve a unique user ID"""
        return uuid.uuid4().bytes

    @classmethod
    def start_registration(cls, username: str, display_name: str) -> dict:
        """Start the registration process"""
        user_id = cls.get_user_unique_id(username)
        challenge = cls.generate_challenge()

        # Store challenge for verification
        session['challenge'] = bytes_to_base64url(challenge)
        session['username'] = username

        options = generate_registration_options(
            rp=PublicKeyCredentialRpEntity(
                id=RP_ID,
                name=RP_NAME
            ),
            user=PublicKeyCredentialUserEntity(
                id=user_id,
                name=username,
                display_name=display_name
            ),
            challenge=challenge,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED
            ),
            exclude_credentials=[],
            timeout=60000,
        )

        return options.model_dump()

    @classmethod
    def verify_registration(cls, response: dict) -> bool:
        """Verify the registration response"""
        challenge = base64url_to_bytes(session['challenge'])
        username = session['username']

        try:
            credential = RegistrationCredential.model_validate(response)
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID
            )

            # Store the credential
            credentials[verification.credential_id] = {
                'public_key': verification.credential_public_key,
                'sign_count': verification.sign_count,
                'username': username
            }

            # Store user info
            registered_users[username] = {
                'credential_ids': [verification.credential_id],
                'registered_at': datetime.utcnow().isoformat()
            }

            return True

        except Exception as e:
            print(f"Registration verification failed: {e}")
            return False

    @classmethod
    def start_authentication(cls, username: str) -> dict:
        """Start the authentication process"""
        if username not in registered_users:
            raise ValueError("User not registered")

        challenge = cls.generate_challenge()
        session['challenge'] = bytes_to_base64url(challenge)
        session['username'] = username

        options = generate_authentication_options(
            rp_id=RP_ID,
            challenge=challenge,
            allow_credentials=[
                {"id": cred_id, "type": "public-key"}
                for cred_id in registered_users[username]['credential_ids']
            ],
            user_verification=UserVerificationRequirement.PREFERRED,
            timeout=60000
        )

        return options.model_dump()

    @classmethod
    def verify_authentication(cls, response: dict) -> bool:
        """Verify the authentication response"""
        challenge = base64url_to_bytes(session['challenge'])
        credential_id = response.get('id')

        if credential_id not in credentials:
            return False

        stored_credential = credentials[credential_id]

        try:
            credential = AuthenticationCredential.model_validate(response)
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
                credential_public_key=stored_credential['public_key'],
                credential_current_sign_count=stored_credential['sign_count']
            )

            # Update sign count
            credentials[credential_id]['sign_count'] = verification.new_sign_count
            return True

        except Exception as e:
            print(f"Authentication verification failed: {e}")
            return False

# Flask routes
@app.route('/register/start', methods=['POST'])
def start_registration():
    data = request.get_json()
    username = data.get('username')
    display_name = data.get('displayName', username)

    if username in registered_users:
        return jsonify({'error': 'User already registered'}), 400

    try:
        options = PasskeyAuth.start_registration(username, display_name)
        return jsonify(options)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/register/complete', methods=['POST'])
def complete_registration():
    data = request.get_json()

    try:
        if PasskeyAuth.verify_registration(data):
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Registration failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/authenticate/start', methods=['POST'])
def start_authentication():
    data = request.get_json()
    username = data.get('username')

    try:
        options = PasskeyAuth.start_authentication(username)
        return jsonify(options)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/authenticate/complete', methods=['POST'])
def complete_authentication():
    data = request.get_json()

    try:
        if PasskeyAuth.verify_authentication(data):
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Authentication failed'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Client-side JavaScript example
CLIENT_JS = """
// Registration
async function registerUser(username, displayName) {
    // Start registration
    const optionsResponse = await fetch('/register/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, displayName })
    });
    const options = await optionsResponse.json();

    // Create credentials
    const credential = await navigator.credentials.create({
        publicKey: {
            ...options,
            challenge: base64urlToBuffer(options.challenge),
            user: {
                ...options.user,
                id: base64urlToBuffer(options.user.id)
            }
        }
    });

    // Complete registration
    const response = await fetch('/register/complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            id: credential.id,
            rawId: bufferToBase64url(credential.rawId),
            response: {
                attestationObject: bufferToBase64url(credential.response.attestationObject),
                clientDataJSON: bufferToBase64url(credential.response.clientDataJSON)
            },
            type: credential.type
        })
    });
    return response.json();
}

// Authentication
async function authenticateUser(username) {
    // Start authentication
    const optionsResponse = await fetch('/authenticate/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username })
    });
    const options = await optionsResponse.json();

    // Get credentials
    const credential = await navigator.credentials.get({
        publicKey: {
            ...options,
            challenge: base64urlToBuffer(options.challenge),
            allowCredentials: options.allowCredentials.map(cred => ({
                ...cred,
                id: base64urlToBuffer(cred.id)
            }))
        }
    });

    // Complete authentication
    const response = await fetch('/authenticate/complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            id: credential.id,
            rawId: bufferToBase64url(credential.rawId),
            response: {
                authenticatorData: bufferToBase64url(credential.response.authenticatorData),
                clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
                signature: bufferToBase64url(credential.response.signature),
                userHandle: credential.response.userHandle ? bufferToBase64url(credential.response.userHandle) : null
            },
            type: credential.type
        })
    });
    return response.json();
}

// Utility functions
function bufferToBase64url(buffer) {
    const bytes = new Uint8Array(buffer);
    let str = '';
    for (const byte of bytes) {
        str += String.fromCharCode(byte);
    }
    return btoa(str).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function base64urlToBuffer(base64url) {
    const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
    const padlen = 4 - (base64.length % 4);
    const padded = padlen < 4 ? base64 + '='.repeat(padlen) : base64;
    const binary = atob(padded);
    const buffer = new ArrayBuffer(binary.length);
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return buffer;
}
"""

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # WebAuthn requires HTTPS


"""

To use this in production:

1. Install required packages:
```bash
pip install flask py-webauthn cryptography pyOpenSSL
```

2. Replace the in-memory storage with a proper database:
```python
# Example using SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/dbname'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    registered_at = db.Column(db.DateTime, nullable=False)
    credentials = db.relationship('Credential', backref='user', lazy=True)

class Credential(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.Integer, nullable=False, default=0)
```

3. Update configuration for your domain:
```python
RP_ID = "yourdomain.com"
RP_NAME = "Your App Name"
ORIGIN = "https://yourdomain.com"
```

4. Add proper session management and user authentication middleware

5. Add error handling and logging

6. Implement proper CORS if needed:
```python
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": ORIGIN}})
```

7. Add rate limiting to prevent abuse:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

This implementation provides:
- Registration and authentication flows
- Challenge-response security
- User verification
- Credential management
- Client-side JavaScript example
- Basic security measures

Remember to:
- Use HTTPS in production
- Implement proper session management
- Add appropriate error handling
- Use a secure database
- Implement rate limiting
- Add logging
- Follow security best practices

"""

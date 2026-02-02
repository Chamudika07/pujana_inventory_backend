from passlib.context import CryptContext
import hashlib

# Use bcrypt with proper configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Function to hash password
def hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
        
    Raises:
        ValueError: If password hashing fails
    """
    password = str(password).strip()

    # bcrypt has a 72-byte limit
    # If password is longer, hash it first to get a consistent 64-char string
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        # Hash the password first to get it under 72 bytes, then use that for bcrypt
        password = hashlib.sha256(password_bytes).hexdigest()

    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")

# Function to verify password
def verify(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        return False
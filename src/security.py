def sign_message(private_key, message):
    # Placeholder — return dummy signature
    return f"signed({message})"

def verify_signature(public_key, message, signature):
    # Placeholder — always returns True for now
    return signature == f"signed({message})"

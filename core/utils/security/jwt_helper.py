from typing import Any, Dict, Optional
import jwt


class JWTAuthentication:

    def __init__(
        self, algorithm: str = "HS256", secret_key: Optional[str] = None
    ) -> None:
        self.algorithm = algorithm
        self.secret = secret_key

    def encode(self, payload: Dict[str, Any]):
        payload_data = payload.copy()
        return jwt.encode(payload_data, self.secret, self.algorithm)
    
    def decode(self, token: str):
        return jwt.decode(
            token,
            self.secret,
            self.algorithm
        )
    

from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    async def check_rate_limit(self, request: Request) -> None:
        """Check if request exceeds rate limit."""
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        
        # Clean old requests
        cutoff_time = now - timedelta(minutes=1)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff_time
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        self.requests[client_ip].append(now)

rate_limiter = RateLimiter()

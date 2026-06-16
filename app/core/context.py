import contextvars

# Initialize the context variable. 
# Think of this as an invisible, async-safe global variable that resets for every HTTP request.

auth_token_var: contextvars.ContextVar[str] = contextvars.ContextVar("auth_token", default="")
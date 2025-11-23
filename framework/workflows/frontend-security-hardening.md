---
id: frontend-security-hardening
name: Frontend Security Hardening Workflow
type: quality
version: 1.0.0
duration: 3-5 days
complexity: high
steps:
- order: 1
  name: Implement Authentication{% if config.security and config.security.authentication
    %} ({{ config.security.authentication.method }}){% endif %} (1-2 days)
  agent: '{%-if-config.agents-%}{{-config.agents.security_engineer-or-''security-engineer''-}}{%-else-%}security-engineer{%-endif-%}'
  duration: 0.5 days
- order: 2
  name: Implement Input Validation (1-2 days)
  agent: '{%-if-config.agents-%}{{-config.agents.security_engineer-or-''security-engineer''-}}{%-else-%}security-engineer{%-endif-%}'
  duration: 0.5 days
- order: 3
  name: XSS Prevention (1 day)
  agent: '{%-if-config.agents-%}{{-config.agents.security_engineer-or-''security-engineer''-%}{%-else-%}security-engineer{%-endif-%}'
  duration: 0.5 days
- order: 4
  name: Security Headers (0.5 days)
  agent: '{%-if-config.agents-%}{{-config.agents.security_engineer-or-''security-engineer''-%}{%-else-%}security-engineer{%-endif-%}'
  duration: 0.5 days
- order: 5
  name: Rate Limiting (0.5 days)
  agent: '{%-if-config.agents-%}{{-config.agents.security_engineer-or-''security-engineer''-}}{%-else-%}security-engineer{%-endif-%}'
  duration: 0.5 days
- order: 6
  name: Security Audit (1 day)
  agent: '{%-if-config.agents-%}{{-config.agents.security_engineer-or-''security-engineer''-}}-+-{{-config.agents.test_engineer-or-''test-engineer''-}}{%-else-%}security-engineer-+-test-engineer{%-endif-%}'
  duration: 0.5 days
- order: 7
  name: Documentation (0.5 days)
  agent: '{%-if-config.agents-%}{{-config.agents.documentation_engineer-or-''documentation-engineer''-}}{%-else-%}documentation-engineer{%-endif-%}'
  duration: 0.5 days
- order: 8
  name: Commit Security Changes (0.5 days)
  agent: '{%-if-config.agents-%}{{-config.agents.git_committer-or-''git-committer''-}}{%-else-%}git-committer{%-endif-%}'
  duration: 0.5 days
inputs:
- name: feature_name
  type: string
  required: true
  description: Name of the feature or task
- name: requirements
  type: string
  required: true
  description: Requirements and acceptance criteria
- name: project_type
  type: string
  required: false
  default: web-app
  description: Project type (web-app, api, ml, data-platform)
description: Comprehensive security implementation and audit for frontend applications
---

# Frontend Security Hardening Workflow

**Purpose:** Comprehensive security implementation and audit for frontend applications
**Duration:** 3-5 days
**Complexity:** High
**Agents:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' }}, {{ config.agents.test_engineer or 'Test Engineer' }}, {{ config.agents.documentation_engineer or 'Documentation Engineer' }}, {{ config.agents.git_committer or 'Git Committer' }}{% else %}Security Engineer, Test Engineer, Documentation Engineer, Git Committer{% endif %}

**When to Use:**
- Before production deployment
- When implementing security from scratch
- After security vulnerabilities discovered
- During security audits or compliance reviews
- As part of quality gates

---

## 📋 Workflow Overview

This workflow implements comprehensive security across frontend and backend with:

1. Authentication and authorization
2. Input validation (frontend and backend)
3. XSS prevention
4. CSRF protection
5. Security headers
6. Rate limiting
7. Security audit and testing

**Total Effort:** 3-5 days (varies by application complexity)

---

## 🚀 Prerequisites

Before starting:

**1. Complete Application:**
- ✅ All features implemented
- ✅ All tests passing
- ✅ Security requirements documented

**2. Security Checklist:**
- Review security requirements
- Identify sensitive data
- Document authentication needs
- Plan security architecture

**3. Environment Configuration:**
- Secrets management configured
- {% if config.security and config.security.authentication %}{{ config.security.authentication.method or 'Authentication' }}{% else %}Authentication{% endif %} provider ready
- SSL certificates available

---

## 📝 Workflow Steps

### Step 1: Implement Authentication{% if config.security and config.security.authentication %} ({{ config.security.authentication.method }}){% endif %} (1-2 days)

**Agent:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' }}{% else %}Security Engineer{% endif %}

**Activities:**

**1.1: Backend Authentication**

{% if config.web_framework and config.web_framework.backend == 'fastapi' or config.technology_stack.backend.language == 'python' %}**FastAPI JWT Authentication:**

```python
# {% if config.project.structure and config.project.structure.backend_directory %}{{ config.project.structure.backend_directory }}{% else %}backend{% endif %}/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

SECRET_KEY = "{% raw %}{{ config.security.jwt_secret or 'your-secret-key-from-env' }}{% endraw %}"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.post("/api/auth/login")
async def login(username: str, password: str):
    # Verify credentials
    user = verify_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
```

**Protect Routes:**
```python
from fastapi import Depends

@app.get("/api/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"user": current_user, "message": "This is a protected route"}
```

{% elif config.web_framework and config.web_framework.backend == 'express' or config.technology_stack.backend.language in ['javascript', 'typescript'] %}**Express JWT Authentication:**

```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// {% if config.project.structure and config.project.structure.backend_directory %}{{ config.project.structure.backend_directory }}{% else %}backend{% endif %}/auth.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';

const SECRET_KEY = process.env.JWT_SECRET || 'your-secret-key';
const ACCESS_TOKEN_EXPIRE = '30m';

export function createAccessToken(data{% if config.technology_stack.backend.language == 'typescript' %}: any{% endif %}){% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %} {
    return jwt.sign(data, SECRET_KEY, { expiresIn: ACCESS_TOKEN_EXPIRE });
}

export function verifyToken(token{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}) {
    try {
        return jwt.verify(token, SECRET_KEY);
    } catch (error) {
        return null;
    }
}

export function authMiddleware(req{% if config.technology_stack.backend.language == 'typescript' %}: any{% endif %}, res{% if config.technology_stack.backend.language == 'typescript' %}: any{% endif %}, next{% if config.technology_stack.backend.language == 'typescript' %}: any{% endif %}) {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Unauthorized' });
    }

    const token = authHeader.substring(7);
    const payload = verifyToken(token);
    if (!payload) {
        return res.status(401).json({ error: 'Invalid token' });
    }

    req.user = payload;
    next();
}

// Login route
app.post('/api/auth/login', async (req, res) => {
    const { username, password } = req.body;

    // Verify credentials
    const user = await verifyUser(username, password);
    if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = createAccessToken({ sub: username });
    res.json({ access_token: token, token_type: 'bearer' });
});
```

{% elif config.web_framework and config.web_framework.backend == 'spring-boot' or config.technology_stack.backend.language == 'java' %}**Spring Security JWT Authentication:**

```java
// SecurityConfig.java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf().disable()
            .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeHttpRequests()
            .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
            .anyRequest().authenticated()
            .and()
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}

// JwtTokenProvider.java
@Component
public class JwtTokenProvider {

    @Value("${jwt.secret}")
    private String secret;

    private static final long EXPIRATION_TIME = 1800000; // 30 minutes

    public String createToken(String username) {
        return Jwts.builder()
            .setSubject(username)
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME))
            .signWith(SignatureAlgorithm.HS512, secret)
            .compact();
    }

    public String getUsernameFromToken(String token) {
        return Jwts.parser()
            .setSigningKey(secret)
            .parseClaimsJws(token)
            .getBody()
            .getSubject();
    }
}
```

{% else %}**Authentication Setup:**

Configure authentication for your backend framework:
- Set up JWT token generation and validation
- Create login endpoint
- Implement authentication middleware
- Protect routes requiring authentication
{% endif %}

**1.2: Frontend Authentication**

{% if config.web_framework and config.web_framework.frontend == 'react' %}**React Authentication Context:**

```{% if config.technology_stack.backend.language == 'typescript' %}tsx{% else %}jsx{% endif %}
// src/contexts/AuthContext.{% if config.technology_stack.backend.language == 'typescript' %}tsx{% else %}jsx{% endif %}
import React, { createContext, useContext, useState{% if config.technology_stack.backend.language == 'typescript' %}, ReactNode{% endif %} } from 'react';

interface AuthContextType {
    user: string | null;
    token: string | null;
    login: (username: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }{% if config.technology_stack.backend.language == 'typescript' %}: { children: ReactNode }{% endif %}) {
    const [user, setUser] = useState<string | null>(localStorage.getItem('user'));
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

    const login = async (username: string, password: string) => {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        setToken(data.access_token);
        setUser(username);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', username);
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
```

**Protected Routes:**
```{% if config.technology_stack.backend.language == 'typescript' %}tsx{% else %}jsx{% endif %}
// src/components/ProtectedRoute.{% if config.technology_stack.backend.language == 'typescript' %}tsx{% else %}jsx{% endif %}
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export function ProtectedRoute({ children }{% if config.technology_stack.backend.language == 'typescript' %}: { children: ReactNode }{% endif %}) {
    const { token } = useAuth();

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}
```

{% elif config.web_framework and config.web_framework.frontend == 'vue' %}**Vue Authentication:**

```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// src/composables/useAuth.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}
import { ref, computed } from 'vue';

const user = ref(localStorage.getItem('user'));
const token = ref(localStorage.getItem('token'));

export function useAuth() {
    const isAuthenticated = computed(() => !!token.value);

    async function login(username{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}, password{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}) {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        token.value = data.access_token;
        user.value = username;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', username);
    }

    function logout() {
        token.value = null;
        user.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }

    return {
        user,
        token,
        isAuthenticated,
        login,
        logout
    };
}
```

{% elif config.web_framework and config.web_framework.frontend == 'angular' %}**Angular Authentication Service:**

```typescript
// src/app/services/auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private tokenSubject: BehaviorSubject<string | null>;
    public token: Observable<string | null>;

    constructor(private http: HttpClient) {
        this.tokenSubject = new BehaviorSubject<string | null>(
            localStorage.getItem('token')
        );
        this.token = this.tokenSubject.asObservable();
    }

    login(username: string, password: string) {
        return this.http.post<{ access_token: string }>('/api/auth/login', {
            username,
            password
        }).pipe(
            map(response => {
                localStorage.setItem('token', response.access_token);
                this.tokenSubject.next(response.access_token);
                return response.access_token;
            })
        );
    }

    logout() {
        localStorage.removeItem('token');
        this.tokenSubject.next(null);
    }

    get tokenValue(): string | null {
        return this.tokenSubject.value;
    }
}
```

{% else %}**Frontend Authentication:**

Implement authentication in your frontend framework:
- Create authentication state management
- Implement login/logout functions
- Create protected route guards
- Handle token storage
{% endif %}

**1.3: API Integration with Authentication**

Update API client to include authentication headers:

{% if config.technology_stack.backend.language == 'typescript' or config.technology_stack.backend.language == 'javascript' %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// src/services/api.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}
function getAuthHeader(){% if config.technology_stack.backend.language == 'typescript' %}: HeadersInit{% endif %} {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function apiRequest(url{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}, options{% if config.technology_stack.backend.language == 'typescript' %}: RequestInit{% endif %} = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader(),
            ...options.headers
        }
    });

    if (response.status === 401) {
        // Redirect to login
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    return response;
}
```
{% else %}# Update API client to include authentication headers
{% endif %}

**Output:**
- Backend authentication implemented
- Frontend authentication UI
- Protected routes configured
- Token management working

---

### Step 2: Implement Input Validation (1-2 days)

**Agent:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' }}{% else %}Security Engineer{% endif %}

**Activities:**

**2.1: Backend Validation**

{% if config.web_framework and config.web_framework.backend == 'fastapi' or config.technology_stack.backend.language == 'python' %}```python
# Pydantic models for validation
from pydantic import BaseModel, Field, validator
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: str = Field(..., regex="^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=8)

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```
{% elif config.web_framework and config.web_framework.backend == 'express' %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// Use express-validator
import { body, validationResult } from 'express-validator';

const validateUser = [
    body('username')
        .isLength({ min: 3, max: 50 })
        .matches(/^[a-zA-Z0-9_-]+$/),
    body('email').isEmail(),
    body('password').isLength({ min: 8 })
        .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/),
];

app.post('/api/users', validateUser, (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }
    // Process request
});
```
{% elif config.web_framework and config.web_framework.backend == 'spring-boot' %}```java
// Bean Validation
import javax.validation.constraints.*;

public class UserDTO {
    @NotBlank
    @Size(min = 3, max = 50)
    @Pattern(regexp = "^[a-zA-Z0-9_-]+$")
    private String username;

    @NotBlank
    @Email
    private String email;

    @NotBlank
    @Size(min = 8)
    @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)")
    private String password;
}

// Controller
@PostMapping("/api/users")
public ResponseEntity<?> createUser(@Valid @RequestBody UserDTO userDTO) {
    // Process request
}
```
{% else %}# Implement backend validation for your framework
{% endif %}

**2.2: Frontend Validation**

{% if config.web_framework and config.web_framework.frontend == 'react' %}```{% if config.technology_stack.backend.language == 'typescript' %}tsx{% else %}jsx{% endif %}
// Use yup + react-hook-form
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

const schema = yup.object({
    username: yup.string()
        .required('Username is required')
        .min(3, 'Username must be at least 3 characters')
        .max(50, 'Username must be at most 50 characters')
        .matches(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, hyphens, and underscores'),
    email: yup.string()
        .required('Email is required')
        .email('Email is invalid'),
    password: yup.string()
        .required('Password is required')
        .min(8, 'Password must be at least 8 characters')
        .matches(/(?=.*[a-z])/, 'Password must contain lowercase letter')
        .matches(/(?=.*[A-Z])/, 'Password must contain uppercase letter')
        .matches(/(?=.*\d)/, 'Password must contain digit'),
});

export function UserForm() {
    const { register, handleSubmit, formState: { errors } } = useForm({
        resolver: yupResolver(schema)
    });

    const onSubmit = (data{% if config.technology_stack.backend.language == 'typescript' %}: any{% endif %}) => {
        // Submit form
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <input {...register('username')} />
            {errors.username && <p>{errors.username.message}</p>}

            <input {...register('email')} type="email" />
            {errors.email && <p>{errors.email.message}</p>}

            <input {...register('password')} type="password" />
            {errors.password && <p>{errors.password.message}</p>}

            <button type="submit">Submit</button>
        </form>
    );
}
```
{% elif config.web_framework and config.web_framework.frontend == 'vue' %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// Use vee-validate + yup
import { useForm } from 'vee-validate';
import * as yup from 'yup';

const schema = yup.object({
    username: yup.string().required().min(3).max(50)
        .matches(/^[a-zA-Z0-9_-]+$/),
    email: yup.string().required().email(),
    password: yup.string().required().min(8)
        .matches(/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
});

export default {
    setup() {
        const { errors, handleSubmit, defineField } = useForm({
            validationSchema: schema
        });

        const [username] = defineField('username');
        const [email] = defineField('email');
        const [password] = defineField('password');

        const onSubmit = handleSubmit((values) => {
            // Submit form
        });

        return { username, email, password, errors, onSubmit };
    }
};
```
{% else %}# Implement frontend validation for your framework
{% endif %}

**Output:**
- Backend validation configured
- Frontend validation implemented
- Validation errors displayed
- Client and server validation synchronized

---

### Step 3: XSS Prevention (1 day)

**Agent:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' %}{% else %}Security Engineer{% endif %}

**Activities:**

**3.1: Install Sanitization Library**

{% if config.web_framework and config.web_framework.frontend == 'react' or config.web_framework and config.web_framework.frontend == 'vue' %}```bash
npm install dompurify {% if config.technology_stack.backend.language == 'typescript' %}@types/dompurify{% endif %}
```

**3.2: Create Sanitization Utility**

```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
// src/utils/sanitize.{% if config.technology_stack.backend.language == 'typescript' %}ts{% else %}js{% endif %}
import DOMPurify from 'dompurify';

export function sanitizeHtml(dirty{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}){% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %} {
    return DOMPurify.sanitize(dirty, {
        ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
        ALLOWED_ATTR: ['href']
    });
}

export function sanitizeInput(input{% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %}){% if config.technology_stack.backend.language == 'typescript' %}: string{% endif %} {
    return input
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
}
```

**3.3: Use Sanitization**

{% if config.web_framework and config.web_framework.frontend == 'react' %}```{% if config.technology_stack.backend.language == 'typescript' %}tsx{% else %}jsx{% endif %}
import { sanitizeHtml } from '../utils/sanitize';

// Only use dangerouslySetInnerHTML with sanitized content
function UserContent({ html }{% if config.technology_stack.backend.language == 'typescript' %}: { html: string }{% endif %}) {
    return (
        <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }} />
    );
}
```
{% endif %}
{% else %}# Install and configure XSS prevention for your framework
{% endif %}

**Output:**
- Sanitization library installed
- All user content sanitized
- XSS vulnerabilities mitigated

---

### Step 4: Security Headers (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' %}{% else %}Security Engineer{% endif %}

**Activities:**

Configure security headers:

{% if config.web_framework and config.web_framework.backend == 'fastapi' %}```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```
{% elif config.web_framework and config.web_framework.backend == 'express' %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
import helmet from 'helmet';

app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", 'data:', 'https:']
        }
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true
    }
}));
```
{% else %}# Configure security headers for your backend framework
{% endif %}

**Output:**
- Security headers configured
- CSP policy defined
- HSTS enabled

---

### Step 5: Rate Limiting (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' }}{% else %}Security Engineer{% endif %}

**Activities:**

{% if config.web_framework and config.web_framework.backend == 'fastapi' %}```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login logic
```
{% elif config.web_framework and config.web_framework.backend == 'express' %}```{% if config.technology_stack.backend.language == 'typescript' %}typescript{% else %}javascript{% endif %}
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 5, // 5 requests per minute
    message: 'Too many requests, please try again later'
});

app.post('/api/auth/login', limiter, (req, res) => {
    // Login logic
});
```
{% else %}# Configure rate limiting for your backend framework
{% endif %}

**Output:**
- Rate limiting configured
- API endpoints protected
- Brute force attacks mitigated

---

### Step 6: Security Audit (1 day)

**Agent:** {% if config.agents %}{{ config.agents.security_engineer or 'Security Engineer' }} + {{ config.agents.test_engineer or 'Test Engineer' }}{% else %}Security Engineer + Test Engineer{% endif %}

**Activities:**

**6.1: Automated Security Scanning**

```bash
# Frontend vulnerability scan
npm audit
npm audit fix

# OWASP Dependency Check (if applicable)
dependency-check --scan .

# Static code analysis
{% if config.technology_stack.backend.language == 'python' %}bandit -r .{% elif config.technology_stack.backend.language in ['javascript', 'typescript'] %}npm run lint:security{% endif %}
```

**6.2: Manual Security Review**

Review checklist:
- ✅ {% if config.security and config.security.authentication %}{{ config.security.authentication.method }}{% else %}Authentication{% endif %} properly implemented
- ✅ All endpoints require authentication (except public ones)
- ✅ Input validation on frontend and backend
- ✅ XSS prevention implemented
- ✅ CSRF protection enabled
- ✅ Security headers configured
- ✅ Rate limiting on sensitive endpoints
- ✅ Secrets not hardcoded
- ✅ HTTPS enforced
- ✅ Dependencies up to date

**6.3: Penetration Testing**

Test common vulnerabilities:
- SQL injection
- XSS attacks
- CSRF attacks
- Authentication bypass
- Broken access control
- Security misconfiguration

**Output:**
- Security audit report
- Vulnerability list
- Remediation plan

---

### Step 7: Documentation (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.documentation_engineer or 'Documentation Engineer' }}{% else %}Documentation Engineer{% endif %}

**Activities:**

Create security documentation:

```markdown
# Security Documentation

## Authentication
- Method: {% if config.security and config.security.authentication %}{{ config.security.authentication.method }}{% else %}JWT{% endif %}
- Token expiration: 30 minutes
- Storage: localStorage

## Protected Routes
- All `/api/*` routes except `/api/auth/*`
- Frontend protected routes require authentication

## Input Validation
- Frontend: yup validation schemas
- Backend: {% if config.web_framework and config.web_framework.backend == 'fastapi' %}Pydantic{% elif config.web_framework and config.web_framework.backend == 'express' %}express-validator{% elif config.web_framework and config.web_framework.backend == 'spring-boot' %}Bean Validation{% else %}validation library{% endif %}

## Security Headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security
- Content-Security-Policy

## Rate Limiting
- Login: 5 attempts per minute
- API: 100 requests per minute

## Secrets Management
- Stored in environment variables
- Never committed to Git
```

**Output:**
- Security documentation complete
- Developer security guide
- Incident response plan

---

### Step 8: Commit Security Changes (0.5 days)

**Agent:** {% if config.agents %}{{ config.agents.git_committer or 'Git Committer' }}{% else %}Git Committer{% endif %}

**Activities:**
1. Review all security changes
2. Stage security implementation files
3. Create comprehensive commit
4. Push to repository

**Commit Message:**
```
feat: Implement comprehensive security hardening

Security Features Implemented:
- {% if config.security and config.security.authentication %}{{ config.security.authentication.method }}{% else %}JWT{% endif %} authentication (frontend + backend)
- Input validation (yup + {% if config.web_framework and config.web_framework.backend == 'fastapi' %}Pydantic{% elif config.web_framework and config.web_framework.backend == 'spring-boot' %}Bean Validation{% else %}backend validation{% endif %})
- XSS prevention (DOMPurify)
- CSRF protection
- Security headers (CSP, HSTS, etc.)
- Rate limiting on sensitive endpoints
- Security audit completed

Security Score: {% if config.security and config.security.target_score %}{{ config.security.target_score }}{% else %}90{% endif %}/100

All security checks passing:
- ✅ Authentication implemented
- ✅ Authorization enforced
- ✅ Input validation (client + server)
- ✅ XSS protection
- ✅ Security headers configured
- ✅ Rate limiting enabled
- ✅ No hardcoded secrets
- ✅ Dependencies up to date
```

---

## ✅ Success Criteria

Security hardening is successful when:

1. ✅ **Authentication:** {% if config.security and config.security.authentication %}{{ config.security.authentication.method }}{% else %}JWT{% endif %} authentication working
2. ✅ **Authorization:** Protected routes enforce authentication
3. ✅ **Validation:** Input validated on frontend and backend
4. ✅ **XSS Prevention:** All user content sanitized
5. ✅ **Security Headers:** CSP, HSTS, and other headers configured
6. ✅ **Rate Limiting:** Sensitive endpoints protected
7. ✅ **Audit:** Security score ≥ {% if config.security and config.security.target_score %}{{ config.security.target_score }}{% else %}90{% endif %}/100
8. ✅ **Documentation:** Security features documented

---

## 🔗 Related Workflows

**Upstream (Triggers This Workflow):**
- **{% if config.web_framework and config.web_framework.frontend %}{{ config.web_framework.frontend | title }}{% else %}Frontend{% endif %} Development** - Application features complete
- **Sprint Planning** - Security requirements defined

**Downstream (This Workflow Enables):**
- **Frontend Production Deployment** - Security review passed
- **Production Monitoring** - Security monitoring configured

---

## 💡 Best Practices

1. **Defense in Depth:** Implement security at multiple layers
2. **Principle of Least Privilege:** Minimal permissions by default
3. **Input Validation:** Validate on both client and server
4. **Secure Defaults:** Security enabled by default
5. **Keep Dependencies Updated:** Regular security updates
6. **Security Headers:** Always configure CSP, HSTS, etc.
7. **Rate Limiting:** Protect against brute force
8. **Regular Audits:** Continuous security reviews

---

**Workflow Version:** 1.0
**Created:** {{ "now"|date("%Y-%m-%d") }}
**Maintained By:** {% if config.team %}{{ config.team.name }}{% else %}Project Team{% endif %}
**Framework:** Vibey Agent Framework

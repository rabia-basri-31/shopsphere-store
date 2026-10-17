# M1 – User Authentication

#### 1.1 `is_valid_email(email)`  → *(Noor)*
**Technique:** ECP + BVA on structure.

| ID | Class / Boundary | Input | Expected |
|----|------------------|-------|----------|
| AU-E1 | Valid (typical) | `user@example.com` | True |
| AU-E2 | Valid – shortest TLD (2 letters) | `a@b.co` | True |
| AU-E3 | Invalid – 1-letter TLD (boundary) | `a@b.c` | False |
| AU-E4 | Invalid – no `@` | `abc.example.com` | False |
| AU-E5 | Invalid – two `@` | `a@@b.com` | False |
| AU-E6 | Invalid – contains space | `a b@c.com` | False |
| AU-E7 | Invalid – digits in TLD | `a@b.c0m` | False |
| AU-E8 | Empty string | `""` | False |
| AU-E9 | `None` | `None` | False |
| AU-E10 | Trailing space (not stripped here) | `"a@b.com "` | False |

#### 1.2 `password_problem(password)` → *(Noor)*
**Technique:** BVA on length (6 and 72) + ECP on character types.

| ID | Class / Boundary | Input | Expected |
|----|------------------|-------|----------|
| AU-P1 | Length 5 (below min) | `abc12` | "at least 6 characters" |
| AU-P2 | Length 6 (min, valid) | `abc123` | `""` |
| AU-P3 | Length 72 (max, valid) | `"a"*71+"1"` | `""` |
| AU-P4 | Length 73 (above max) | `"a"*72+"1"` | "too long (maximum 72…)" |
| AU-P5 | Letters only | `abcdef` | "at least one number" |
| AU-P6 | Digits only | `123456` | "at least one letter" |
| AU-P7 | Empty | `""` | "at least 6 characters" |
| AU-P8 | `None` | `None` | "at least 6 characters" |
| AU-P9 | Only spaces (6) | `"      "` | "at least one letter" |
| AU-P10 | Unicode letters + digit | `پاسورڈ1` | `""` (isalpha is true) |

#### 1.3 `safe_next_url(value)` → *(Rabia)*
**Technique:** ECP (relative / protocol-relative / absolute / empty), security error guessing.

| ID | Input | Expected |
|----|-------|----------|
| AU-N1 | `/cart` | `/cart` |
| AU-N2 | `//evil.com` | `None` |
| AU-N3 | `http://evil.com` | `None` |
| AU-N4 | `None` | `None` |
| AU-N5 | `""` | `None` |
| AU-N6 | `cart` (no leading slash) | `None` |
| AU-N7 | `/` | `/` |
| AU-N8 | `/\evil.com` | **Returns it unchanged → possible open-redirect weakness** (browsers treat `/\` like `//`). Write the test for the *secure* behaviour (`None`) and mark `xfail` / log as a defect. |

#### 1.4 `register()` route → *(Noor)* – mock `query_one`, `execute`
**Technique:** Decision table (name ✓/✗, email ✓/✗, phone ✓/✗/empty, password ✓/✗, match ✓/✗, duplicate ✓/✗).

| ID | Scenario | Expected |
|----|----------|----------|
| AU-R1 | All valid | 302 → `/login`, flash "Account created!", `execute` called once |
| AU-R2 | Name 1 char (boundary) | error "full name (at least 2…)", no insert |
| AU-R3 | Name exactly 2 chars | accepted |
| AU-R4 | Invalid email | "valid email address" |
| AU-R5 | Phone 9 digits / 11 digits / letters | "exactly 10 digits" |
| AU-R6 | Phone empty (optional) | accepted, stored as `None` |
| AU-R7 | Password ≠ confirm | "do not match" |
| AU-R8 | Duplicate email (mock `query_one` returns a row) | "already exists", no insert |
| AU-R9 | Email in UPPER case | saved lower-case |
| AU-R10 | Missing CSRF token | 400 |

#### 1.5 `login()`, `logout()`, decorators → *(Rabia)*
**Technique:** Decision table (email given?, password given?, user exists?, password correct?, admin?, `next` present?).

| ID | Scenario | Expected |
|----|----------|----------|
| AU-L1 | Valid customer | session `user_id` set, redirect `/` |
| AU-L2 | Valid admin | redirect `/admin` |
| AU-L3 | Valid user + `next=/cart` | redirect `/cart` |
| AU-L4 | Valid user + `next=//evil.com` | next ignored → `/` |
| AU-L5 | Wrong password | "Incorrect email or password." |
| AU-L6 | Unknown email | **same** message as AU-L5 (no user enumeration) |
| AU-L7 | Empty email / empty password | "enter both…" |
| AU-L8 | Already logged in → GET `/login` | redirect `/` |
| AU-L9 | `/logout` when logged in | session cleared, flash "logged out" |
| AU-L10 | `/logout` as guest | redirect `/`, no flash |
| AU-L11 | Guest → `/cart` (`login_required`) | redirect to `/login?next=/cart` |
| AU-L12 | Customer → `/admin` (`admin_required`) | 403 / redirect (verify) |

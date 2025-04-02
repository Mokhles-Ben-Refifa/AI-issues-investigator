# 📘 Reference Guide - Application Errors & Recommendations

This document is intended to help intelligent agents diagnose and resolve frequent application-level issues. It is designed to support Retrieval-Augmented Generation (RAG) systems.

---

## 🐛 NullReferenceException / AttributeError

**Log example**:

```
[2024-12-10 11:25:33] ERROR - NullReferenceException: Object reference not set to an instance of an object
```

**Likely cause**:

- Attempt to access a property or method on a null/undefined object

**Recommendations**:

- Add null/undefined checks before object access  
- Use optional chaining (`obj?.property`) if supported  
- Validate all inputs before use

---

## 🧾 Validation Errors

**Log example**:

```
[2024-12-11 14:09:17] WARNING - Validation failed: email is required
```

**Likely cause**:

- Missing or invalid user input  
- Schema mismatch between client and backend

**Recommendations**:

- Enforce schema validation on both frontend and backend  
- Provide clear user feedback for each invalid field  
- Use libraries like `Joi`, `Zod`, or `Pydantic` for robust validation

---

## 🧩 TypeError / TypeMismatch

**Log example**:

```
[2024-12-12 09:58:02] ERROR - TypeError: Cannot read property 'length' of undefined
```

**Likely cause**:

- Accessing properties/methods on the wrong data type  
- Incorrect assumptions about input/output structure

**Recommendations**:

- Use type checking and type inference (`typeof`, `instanceof`)  
- Add defensive programming techniques (type guards, assertions)  
- Consider static typing tools (TypeScript, MyPy)

---

## 🔐 Authentication/Authorization Errors

**Log example**:

```
[2024-12-13 19:41:55] WARNING - 401 Unauthorized: Invalid token
```

**Likely cause**:

- Expired or malformed access token  
- User not authorized to perform the action

**Recommendations**:

- Verify JWT expiration and signature  
- Implement token refresh mechanisms  
- Restrict route access based on roles/permissions

---

## 🗃️ Database Query Failures

**Log example**:

```
[2024-12-14 15:32:10] ERROR - QueryException: Column 'user_id' not found
```

**Likely cause**:

- Incorrect SQL syntax  
- Schema not in sync with code  
- Missing migrations

**Recommendations**:

- Use ORM migrations to keep schema synchronized  
- Write tests for critical queries  
- Log full query with parameters when errors occur

---

## 🔄 Infinite Loops or Recursive Calls

**Log example**:

```
[2024-12-15 12:00:00] ERROR - StackOverflowError: Maximum call stack size exceeded
```

**Likely cause**:

- Improper exit condition in recursion or loop  
- Bad state causing repeated invocation

**Recommendations**:

- Add proper base/exit conditions  
- Use iteration when possible to avoid deep call stacks  
- Monitor stack size in recursive designs

---

## 🧱 UI Rendering Errors

**Log example**:

```
[2024-12-16 18:47:01] ERROR - React error: Cannot update a component while rendering a different component
```

**Likely cause**:

- Illegal state change during render  
- Circular updates between components

**Recommendations**:

- Avoid calling `setState` or `dispatch` during rendering phase  
- Use `useEffect` for side effects  
- Break down complex components into smaller ones

---



# Go Backend for GYM_System

This service is a Go implementation of the existing Spring Boot `/api` backend.

Development target:

- Listen on `:8080`.
- Use the existing `gym_system` MySQL database.
- Keep the same response wrapper: `{ "code": 0, "message": "success", "data": ... }`.
- Keep the same `Authorization: Bearer <token>` authentication contract.
- Proxy `/api/chat` to the existing Python Agent at `http://localhost:8000/chat`.

Run:

```bash
go run ./cmd/server
```

Do not run the Spring Boot backend at the same time when this service uses port `8080`.

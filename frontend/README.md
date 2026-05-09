# GYM Frontend

## Tech Stack

- Vue 3
- Vite

## Start

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

```text
http://localhost:5173
```

## Backend Proxy

Vite 已配置代理：

- `/api` -> `http://localhost:8080`

因此本地联调前，请先启动 Spring Boot 后端。

# Frontend Dockerfile - multi-stage build for Cloud Run
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
RUN npm run build

# Production image - Cloud Run uses PORT (default 8080)
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf

ENV PORT=8080
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

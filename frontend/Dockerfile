# --- Build stage ---
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ARG API_URL=http://localhost:5000/api
ENV API_URL=$API_URL

RUN npx quasar build

# --- Production stage ---
FROM nginx:alpine

COPY --from=build /app/dist/spa /usr/share/nginx/html

# SPA fallback: send all routes to index.html
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

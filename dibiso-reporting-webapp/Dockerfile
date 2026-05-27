FROM node:24-alpine AS build

WORKDIR /build

COPY package.json .
COPY package-lock.json .

RUN npm ci

COPY index.html index.html
COPY postcss.config.js postcss.config.js
COPY tailwind.config.js tailwind.config.js
COPY vite.config.js vite.config.js
COPY src src
COPY .env .env

RUN npm run build

FROM nginx:alpine

LABEL org.opencontainers.image.source="https://github.com/dibiso-upsaclay/dibiso-reporting-webapp"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Romain THOMAS <contact@romainthomas.net>"
LABEL org.opencontainers.image.title="DiBISO reporting webapp"

COPY --from=build /build/dist/ /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
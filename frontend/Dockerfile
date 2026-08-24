FROM node:22.18.0-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_CANDIDATE_FORM_ENABLED=false
ARG VITE_PUBLIC_SITE_ORIGIN=
ENV VITE_CANDIDATE_FORM_ENABLED=${VITE_CANDIDATE_FORM_ENABLED}
ENV VITE_PUBLIC_SITE_ORIGIN=${VITE_PUBLIC_SITE_ORIGIN}

RUN npm run build

FROM nginx:1.27.5-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

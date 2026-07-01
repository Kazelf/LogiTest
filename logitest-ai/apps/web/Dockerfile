FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared/package.json ./packages/shared/package.json

RUN npm install && npm install \
  lightningcss-linux-x64-musl@1.32.0 \
  @tailwindcss/oxide-linux-x64-musl@4.3.1 \
  --no-save \
  --workspace web

COPY apps/web ./apps/web
COPY packages/shared ./packages/shared

EXPOSE 3000

CMD ["npm", "run", "dev", "--workspace", "web", "--", "--hostname", "0.0.0.0"]

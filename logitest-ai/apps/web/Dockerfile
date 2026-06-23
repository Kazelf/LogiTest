FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared/package.json ./packages/shared/package.json

RUN npm install

COPY apps/web ./apps/web
COPY packages/shared ./packages/shared

EXPOSE 3000

CMD ["npm", "run", "dev", "--workspace", "web", "--", "--hostname", "0.0.0.0"]

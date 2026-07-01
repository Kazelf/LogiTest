FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache openssl

COPY package*.json ./
RUN npm ci

COPY src ./src
RUN npm run prisma:generate

EXPOSE 4000

CMD ["sh", "-c", "npm run prisma:deploy && npm run seed && npm start"]

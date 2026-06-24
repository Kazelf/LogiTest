FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
COPY demo-system/package.json ./demo-system/package.json

RUN npm install --workspace demo-system

COPY demo-system ./demo-system

WORKDIR /app/demo-system

EXPOSE 3001

CMD ["npm", "start"]

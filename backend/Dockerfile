FROM node:20-alpine

WORKDIR /app

# Zkopíruj celý obsah složky backend
COPY . .

# Viditelný otisk do logu, ať víš, že se používá TENTO Dockerfile
RUN echo "USING DOCKERFILE WITHOUT NPM (no COPY package*.json, no npm install)"

ENV NODE_ENV=production
EXPOSE 8080

CMD ["node", "server.js"]

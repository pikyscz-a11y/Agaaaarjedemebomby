FROM node:20-alpine

WORKDIR /app

# Zkopíruj manifesty závislostí a nainstaluj prod závislosti
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# Zbytek zdrojáků
COPY . .

ENV NODE_ENV=production
EXPOSE 8080

# Spuštění aplikace
CMD ["npm", "start"]

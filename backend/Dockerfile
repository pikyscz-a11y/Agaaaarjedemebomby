FROM node:20-alpine

WORKDIR /app

# z backend/ kontextu zkopíruj manifesty
COPY package*.json ./

# nainstaluj prod závislosti
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# zbytek zdrojáků backendu
COPY . .

ENV NODE_ENV=production
EXPOSE 8080

# očekává "start" script v package.json
CMD ["npm", "start"]

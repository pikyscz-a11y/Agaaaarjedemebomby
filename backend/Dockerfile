FROM node:20-alpine

WORKDIR /app

# Vezmi package*.json ze složky backend (protože context je kořen repa)
COPY backend/package*.json ./

# Instalace prod závislostí
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# Zbytek zdrojáků backendu
COPY backend/ .

ENV NODE_ENV=production
EXPOSE 8080

# Očekává script "start" v package.json (ve složce backend)
CMD ["npm", "start"]

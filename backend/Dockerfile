# Lehký Node runtime
FROM node:20-alpine

# Pracovní adresář uvnitř kontejneru
WORKDIR /app

# Zkopíruj manifesty závislostí (rychlejší cache)
COPY package*.json ./

# Instalace prod závislostí (funguje i bez package-lock.json)
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi

# Zbytek zdrojáků
COPY . .

# Produkční prostředí
ENV NODE_ENV=production
# Aplikace by měla poslouchat na portu 8080 (lze upravit podle tvé app)
EXPOSE 8080

# Spuštění – očekává script "start" v package.json
CMD ["npm", "start"]

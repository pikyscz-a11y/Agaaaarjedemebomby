FROM node:20-alpine

WORKDIR /app
# Zkopíruj celý projekt (stačí, nemáme žádné závislosti)
COPY . .

ENV NODE_ENV=production
EXPOSE 8080

# Spusť náš server
CMD ["node", "backend/server.js"]

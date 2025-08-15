FROM node:20-alpine

WORKDIR /app

# Zkopíruj vše ze složky backend (build context = backend)
COPY . .

ENV NODE_ENV=production
EXPOSE 8080

CMD ["node", "server.js"]

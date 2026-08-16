FROM node:20-alpine
WORKDIR /app

# Context is root, so we must copy from apps/web
COPY apps/web/package*.json ./
RUN npm ci

COPY apps/web/ ./
RUN npm run build

CMD ["npm", "start"]

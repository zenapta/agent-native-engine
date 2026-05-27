FROM node:20-alpine

WORKDIR /usr/src/app

# Pre-stage dependencies to maximize Docker build-caching
COPY package*.json ./
RUN npm ci --only=production

# Copy over the source tree
COPY . .

EXPOSE 3000

CMD ["node", "src/server.js"]

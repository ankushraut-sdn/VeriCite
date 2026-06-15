# Stage 1: Build React static bundle using Node
FROM node:18-alpine AS builder
WORKDIR /app

# Copy lock files and install dependencies
COPY package.json ./
RUN npm install

# Copy source and build static distribution files
COPY . ./
RUN npm run build

# Stage 2: Serve static files using lightweight Nginx container
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

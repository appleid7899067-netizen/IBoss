FROM node:20-alpine
RUN apk add --no-cache git bash curl
RUN npm install -g opencode-ai@latest
WORKDIR /app
COPY .opencode .opencode
COPY opencode.jsonc .
EXPOSE 4096
CMD ["opencode", "web", "--host", "0.0.0.0", "--port", "4096"]

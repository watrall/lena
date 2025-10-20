# syntax=docker/dockerfile:1.6

# Multi-stage build: compile the Next.js app into a standalone bundle.
FROM node:20-bullseye AS builder
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runtime image: copy the standalone output and serve it with Node.
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
EXPOSE 3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER node

CMD ["node", "server.js"]


FROM node:20.18.0-slim AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY web/package.json web/package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY web/ .

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED 1

# NEXT_PUBLIC_* vars must be set BEFORE build — Next.js inlines them at build time.
ARG NEXT_PUBLIC_API_URL=https://skills-marketplace-api-3a6p.onrender.com/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN ls -la
RUN ls -R src || echo "src not found"
RUN ls -la src/lib || echo "src/lib not found"
RUN ls -la src/lib/api.ts || echo "src/lib/api.ts not found"
RUN cat tsconfig.json || echo "tsconfig.json not found"
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 10000

ENV PORT 10000
# set hostname to localhost
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]

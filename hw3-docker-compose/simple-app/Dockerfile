# Build stage
FROM golang:1.23-alpine AS builder

SHELL ["/bin/sh", "-ecx"]

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

# -ldflags="-s -w" strips debug info and symbols
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w" \
    -o main .

# Runtime stage
FROM alpine:3.19@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b

RUN apk --no-cache add curl ca-certificates && \
    addgroup -g 1001 -S appuser && \
    adduser -u 1001 -S appuser -G appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/main .

USER appuser

EXPOSE 8080

CMD ["./main"]
# Stage 1: Compilation Environment
FROM golang:1.20-alpine AS builder

WORKDIR /app

# Copy the module structure and source code into the builder container
COPY go.mod ./
COPY . .

# Force Go to inspect the source, grab dependencies, and auto-generate the missing go.sum entries
RUN go mod tidy

# Compile the monolithic binary statically
RUN CGO_ENABLED=0 GOOS=linux go build -o /engine_orchestrator src/workflow.go

# Stage 2: Minimalist Production Runtime
FROM alpine:latest
WORKDIR /

COPY --from=builder /engine_orchestrator /engine_orchestrator

CMD ["/engine_orchestrator"]

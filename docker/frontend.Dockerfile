FROM node:22-alpine AS build

WORKDIR /app

# The historical lock file in the repository does not describe the current
# frontend dependency set, so the container build installs from package.json.
COPY frontend/package.json ./package.json
RUN npm install --legacy-peer-deps

COPY frontend/ ./

ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

# MathJax is served directly by nginx and is not bundled into the React app.
COPY --from=build /app/node_modules/mathjax /usr/share/nginx/html/mathjax

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

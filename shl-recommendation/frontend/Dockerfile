FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# CHANGE THIS LINE to your Render URL:
ARG REACT_APP_API_URL=https://shl-smart-recommender.onrender.com
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
# Ensure you have this nginx.conf or remove this line if using default
COPY nginx.conf /etc/nginx/conf.d/default.conf 
EXPOSE 80